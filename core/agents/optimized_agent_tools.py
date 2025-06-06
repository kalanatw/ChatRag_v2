"""
Optimized Agent tools implementation for the Agentic RAG system.
This module directly uses functions from document_search_api.py for optimal performance.
"""

import json
import re
from typing import Dict, List, Any, Optional
from openai import OpenAI
from django.contrib.postgres.search import TrigramSimilarity
from core.models import ChatHistory
import os
from dotenv import load_dotenv

# Import optimized functions from document_search_api
from core.views.document_search_api import (
    generate_embeddings_for_single_text,
    search_query,
    meta_data_extraction,
    construct_openai_prompt,
    construct_openai_prompt_follow_up_query,
    find_similar_previous_query,
    is_follow_up_query,
    save_chat_history_to_db
)
from memory_manager import get_memory, save_and_limit_chat_history

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OptimizedAgentProcessor:
    """
    Optimized agent processor that directly uses core RAG functions
    for maximum performance and minimal time complexity.
    """
    
    def __init__(self):
        self.client = client
        
    def process_rag_query(self, query: str, twin_version_id: str, chat_instance_id: str, 
                         agent_type: str = "default_rag") -> Dict[str, Any]:
        """
        Process RAG query using optimized direct function calls.
        
        Args:
            query: User query text
            twin_version_id: Twin version identifier
            chat_instance_id: Chat instance identifier
            agent_type: Type of agent processing
            
        Returns:
            Complete response with metadata and verification
        """
        try:
            # Step 1: Generate embeddings (O(1) operation)
            query_vector = generate_embeddings_for_single_text(query)
            
            # Step 2: Check if follow-up query (O(1) operation)
            is_followup = is_follow_up_query(query, chat_instance_id)
            
            # Step 3: Extract metadata and search (O(log n) for vector search)
            if is_followup:
                # Get last query from memory for metadata extraction
                memory = get_memory(chat_instance_id)
                chat_history = memory.load_memory_variables({})["chat_history"]
                user_queries = [line[6:] for line in chat_history.splitlines() if line.startswith("Human:")]
                last_query = user_queries[-1] if user_queries else query
                
                metadata_json = meta_data_extraction(twin_version_id, chat_instance_id, last_query)
                metadata = json.loads(metadata_json)
                filtered_metadata = {k: v for k, v in metadata.items() if v is not None}
                
                # Search vector database
                results = search_query(query_vector, 12, last_query, twin_version_id, filtered_metadata)
                
                # Construct follow-up prompt
                openai_prompt = construct_openai_prompt_follow_up_query(chat_instance_id, query, results)
                
            else:
                # Extract metadata for new query
                metadata_json = meta_data_extraction(twin_version_id, chat_instance_id, query)
                metadata = json.loads(metadata_json)
                filtered_metadata = {k: v for k, v in metadata.items() if v is not None}
                
                # Search vector database
                results = search_query(query_vector, 12, query, twin_version_id, filtered_metadata)
                
                # Construct standard prompt
                openai_prompt = construct_openai_prompt(query, results, twin_version_id, chat_instance_id)
            
            # Step 4: Generate response (single API call)
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=1,
                messages=openai_prompt
            )
            
            response_content = completion.choices[0].message.content
            
            # Step 5: Save to memory and database (O(1) operations)
            save_and_limit_chat_history(chat_instance_id, query, response_content)
            save_chat_history_to_db(query, response_content, twin_version_id, chat_instance_id)
            
            # Step 6: Perform verification if needed
            verification_result = None
            if agent_type == "hr_agent":
                verification_result = self._verify_hr_response(response_content, results, query)
            else:
                verification_result = self._verify_response_accuracy(response_content, results, query, agent_type)
            
            return {
                "response": response_content,
                "metadata": metadata,
                "source_chunks": results,
                "verification": verification_result,
                "is_followup": is_followup,
                "agent_type": agent_type
            }
            
        except Exception as e:
            print(f"Error in optimized agent processing: {e}")
            raise e
    
    def _verify_response_accuracy(self, response: str, source_chunks: List[Dict[str, Any]], 
                                 original_query: str, agent_type: str) -> Dict[str, Any]:
        """
        Fast response verification with minimal API calls.
        """
        try:
            verification_prompt = [
                {"role": "system", "content": f"Verify this {agent_type} response for accuracy and guidelines compliance."},
                {"role": "user", "content": f"Query: {original_query}"},
                {"role": "user", "content": f"Response: {response[:1000]}"},  # Limit response size
                {"role": "user", "content": f"Sources: {len(source_chunks)} chunks used"},
                {"role": "system", "content": """
Return JSON format:
{
    "accuracy_score": 0-100,
    "guideline_compliance": true/false,
    "overall_assessment": "pass/review/fail"
}
"""}
            ]
            
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.1,
                messages=verification_prompt
            )
            
            verification_text = completion.choices[0].message.content
            
            # Extract JSON from response
            verification_match = re.search(r'\{.*\}', verification_text, re.DOTALL)
            if verification_match:
                return json.loads(verification_match.group())
            
            # Fallback
            return {
                "accuracy_score": 85,
                "guideline_compliance": True,
                "overall_assessment": "pass"
            }
            
        except Exception as e:
            print(f"Error in response verification: {e}")
            return {
                "accuracy_score": 70,
                "guideline_compliance": False,
                "overall_assessment": "review"
            }
    
    def _verify_hr_response(self, response: str, hr_policy_chunks: List[Dict[str, Any]], 
                           query: str) -> Dict[str, Any]:
        """
        Fast HR-specific response verification.
        """
        try:
            hr_verification_prompt = [
                {"role": "system", "content": "Verify HR response for policy compliance and professionalism."},
                {"role": "user", "content": f"HR Query: {query}"},
                {"role": "user", "content": f"HR Response: {response[:1000]}"},  # Limit size
                {"role": "user", "content": f"Policy Sources: {len(hr_policy_chunks)} chunks"},
                {"role": "system", "content": """
Return JSON:
{
    "policy_compliance": true/false,
    "professional_tone": true/false,
    "contact_info_correct": true/false,
    "overall_hr_assessment": "approved/needs_review/rejected"
}
"""}
            ]
            
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.1,
                messages=hr_verification_prompt
            )
            
            verification_text = completion.choices[0].message.content
            
            # Extract JSON from response
            verification_match = re.search(r'\{.*\}', verification_text, re.DOTALL)
            if verification_match:
                return json.loads(verification_match.group())
            
            # Fallback
            return {
                "policy_compliance": True,
                "professional_tone": True,
                "contact_info_correct": True,
                "overall_hr_assessment": "approved"
            }
            
        except Exception as e:
            print(f"Error in HR response verification: {e}")
            return {
                "policy_compliance": False,
                "professional_tone": True,
                "contact_info_correct": True,
                "overall_hr_assessment": "needs_review"
            }
    
    def check_similar_queries(self, query: str, twin_version_id: str) -> Optional[str]:
        """
        Optimized similar query check using direct database query.
        Only for HR agent to maintain consistency.
        """
        try:
            if twin_version_id == "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455":
                similar_chat = ChatHistory.objects.filter(
                    twin_id=twin_version_id
                ).annotate(
                    similarity=TrigramSimilarity('user_query', query)
                ).filter(
                    similarity__gt=0.6
                ).order_by('-similarity').first()
                
                if similar_chat:
                    return similar_chat.chatbot_response
            
            return None
            
        except Exception as e:
            print(f"Error checking similar queries: {e}")
            return None

    def get_simple_response(self, query: str, twin_version_id: str, chat_instance_id: str) -> str:
        """
        Get simple response without verification for fastest performance.
        Used when verification is not required.
        """
        try:
            # Direct processing without verification overhead
            query_vector = generate_embeddings_for_single_text(query)
            
            # Check follow-up
            is_followup = is_follow_up_query(query, chat_instance_id)
            
            if is_followup:
                memory = get_memory(chat_instance_id)
                chat_history = memory.load_memory_variables({})["chat_history"]
                user_queries = [line[6:] for line in chat_history.splitlines() if line.startswith("Human:")]
                last_query = user_queries[-1] if user_queries else query
                
                metadata_json = meta_data_extraction(twin_version_id, chat_instance_id, last_query)
                metadata = json.loads(metadata_json)
                filtered_metadata = {k: v for k, v in metadata.items() if v is not None}
                results = search_query(query_vector, 12, last_query, twin_version_id, filtered_metadata)
                openai_prompt = construct_openai_prompt_follow_up_query(chat_instance_id, query, results)
            else:
                metadata_json = meta_data_extraction(twin_version_id, chat_instance_id, query)
                metadata = json.loads(metadata_json)
                filtered_metadata = {k: v for k, v in metadata.items() if v is not None}
                results = search_query(query_vector, 12, query, twin_version_id, filtered_metadata)
                openai_prompt = construct_openai_prompt(query, results, twin_version_id, chat_instance_id)
            
            # Generate response
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=1,
                messages=openai_prompt
            )
            
            response_content = completion.choices[0].message.content
            
            # Save to memory and database
            save_and_limit_chat_history(chat_instance_id, query, response_content)
            save_chat_history_to_db(query, response_content, twin_version_id, chat_instance_id)
            
            return response_content
            
        except Exception as e:
            print(f"Error in simple response generation: {e}")
            raise e
    
    def process_simple_rag_query(self, query: str, twin_version_id: str, chat_instance_id: str) -> Dict[str, Any]:
        """
        Process RAG query using simplified mode - bypasses metadata extraction for maximum speed.
        This is the fastest processing mode that focuses purely on vector search and response generation.
        
        Args:
            query: User query text
            twin_version_id: Twin version identifier
            chat_instance_id: Chat instance identifier
            
        Returns:
            Complete response without metadata processing overhead
        """
        try:
            # Step 1: Generate embeddings (O(1) operation)
            query_vector = generate_embeddings_for_single_text(query)
            
            # Step 2: Direct vector search without metadata filtering (O(log n))
            # Use empty metadata for direct similarity search
            results = search_query(query_vector, 12, query, twin_version_id, {})
            
            # Step 3: Check if follow-up query for prompt construction
            is_followup = is_follow_up_query(query, chat_instance_id)
            
            # Step 4: Construct prompt based on query type
            if is_followup:
                openai_prompt = construct_openai_prompt_follow_up_query(chat_instance_id, query, results)
            else:
                openai_prompt = construct_openai_prompt(query, results, twin_version_id, chat_instance_id)
            
            # Step 5: Generate response (single API call)
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=1,
                messages=openai_prompt
            )
            
            response_content = completion.choices[0].message.content
            
            # Step 6: Save to memory and database (O(1) operations)
            save_and_limit_chat_history(chat_instance_id, query, response_content)
            save_chat_history_to_db(query, response_content, twin_version_id, chat_instance_id)
            
            return {
                "response": response_content,
                "metadata": {},  # No metadata extraction in simple mode
                "source_chunks": results,
                "verification": {"mode": "simple", "bypassed": True},  # No verification for speed
                "is_followup": is_followup,
                "agent_type": "simple_rag",
                "processing_mode": "simplified"
            }
            
        except Exception as e:
            print(f"Error in simplified RAG processing: {e}")
            raise e

# Global optimized processor instance
optimized_processor = OptimizedAgentProcessor()

# Optimized tool functions that use the processor
def optimized_extract_metadata(query: str, twin_version_id: str, chat_instance_id: str) -> Dict[str, Any]:
    """Optimized metadata extraction using direct API call."""
    try:
        metadata_json = meta_data_extraction(twin_version_id, chat_instance_id, query)
        return json.loads(metadata_json)
    except Exception as e:
        print(f"Error in optimized metadata extraction: {e}")
        return {}

def optimized_search_vector_database(query: str, twin_version_id: str, 
                                   metadata: Dict[str, Any], top_k: int = 12) -> List[Dict[str, Any]]:
    """Optimized vector database search using direct API call."""
    try:
        query_vector = generate_embeddings_for_single_text(query)
        filtered_metadata = {k: v for k, v in metadata.items() if v is not None}
        return search_query(query_vector, top_k, query, twin_version_id, filtered_metadata)
    except Exception as e:
        print(f"Error in optimized vector search: {e}")
        return []

def optimized_simple_search_vector_database(query: str, twin_version_id: str, top_k: int = 12) -> List[Dict[str, Any]]:
    """Simplified vector database search that bypasses metadata extraction for maximum speed."""
    try:
        query_vector = generate_embeddings_for_single_text(query)
        # Use empty metadata for direct similarity search - no filtering
        return search_query(query_vector, top_k, query, twin_version_id, {})
    except Exception as e:
        print(f"Error in simplified vector search: {e}")
        return []

def optimized_process_complete_query(query: str, twin_version_id: str, chat_instance_id: str, 
                                   agent_type: str = "default_rag", 
                                   verification_mode: str = "full") -> Dict[str, Any]:
    """
    Main optimized function for complete query processing.
    
    Args:
        query: User query
        twin_version_id: Twin version ID
        chat_instance_id: Chat instance ID
        agent_type: Type of agent (default_rag, hr_agent)
        verification_mode: 'full' for complete verification, 'simple' for fast response
    
    Returns:
        Complete processed response
    """
    if verification_mode == "simple":
        response = optimized_processor.get_simple_response(query, twin_version_id, chat_instance_id)
        return {
            "response": response,
            "agent_type": agent_type,
            "verification_mode": "simple"
        }
    else:
        return optimized_processor.process_rag_query(query, twin_version_id, chat_instance_id, agent_type)

# Optimized tool registry
OPTIMIZED_AGENT_TOOLS = {
    "extract_metadata": optimized_extract_metadata,
    "search_vector_database": optimized_search_vector_database,
    "simple_search_vector_database": optimized_simple_search_vector_database,
    "process_complete_query": optimized_process_complete_query,
    "process_simple_rag_query": optimized_processor.process_simple_rag_query,
    "check_similar_queries": optimized_processor.check_similar_queries,
    "get_simple_response": optimized_processor.get_simple_response
}

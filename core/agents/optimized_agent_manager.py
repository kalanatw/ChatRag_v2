"""
Optimized Agent Manager for the Agentic RAG system.
This module provides the fastest possible agent execution by directly using
core RAG functions with minimal overhead and optimal time complexity.
"""

import json
import time
from typing import Dict, List, Any, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv

# Import optimized tools
from .optimized_agent_tools import (
    optimized_processor,
    optimized_process_complete_query,
    OPTIMIZED_AGENT_TOOLS
)

# Import agent definitions
from .agent_definitions import AGENT_CONFIGS

load_dotenv()

class OptimizedAgentManager:
    """
    Optimized agent manager with direct function calls for maximum performance.
    Eliminates loops and unnecessary processing for optimal time complexity.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.agent_configs = AGENT_CONFIGS
    
    def execute_agent_query(self, query: str, twin_version_id: str, chat_instance_id: str,
                           mode: str = "full") -> Dict[str, Any]:
        """
        Execute agent query with optimized direct processing.
        
        Args:
            query: User query
            twin_version_id: Twin version identifier
            chat_instance_id: Chat instance identifier  
            mode: 'full' for complete processing with verification, 'simple' for fastest response
            
        Returns:
            Complete agent response with minimal processing time
        """
        start_time = time.time()
        
        try:
            # Step 1: Determine agent type (O(1) lookup)
            agent_type = self._get_agent_type(twin_version_id, mode)
            agent_config = self.agent_configs.get(agent_type, self.agent_configs["DEFAULT_RAG_AGENT"])
            
            # Step 2: Direct processing based on mode
            if mode == "simple":
                # Fastest path - direct response without verification
                response = optimized_processor.get_simple_response(query, twin_version_id, chat_instance_id)
                
                processing_time = time.time() - start_time
                
                return {
                    "success": True,
                    "response": response,
                    "agent_type": agent_type,
                    "mode": mode,
                    "processing_time": round(processing_time, 3),
                    "timestamp": time.time()
                }
            
            elif mode == "simplified":
                # Simplified RAG mode - bypasses metadata extraction
                return self.execute_simple_rag_query(query, twin_version_id, chat_instance_id)
            
            else:
                # Full processing with verification
                result = optimized_process_complete_query(
                    query=query,
                    twin_version_id=twin_version_id,
                    chat_instance_id=chat_instance_id,
                    agent_type=agent_type,
                    verification_mode="full"
                )
                
                processing_time = time.time() - start_time
                
                return {
                    "success": True,
                    "response": result["response"],
                    "metadata": result.get("metadata", {}),
                    "source_chunks_count": len(result.get("source_chunks", [])),
                    "verification": result.get("verification", {}),
                    "is_followup": result.get("is_followup", False),
                    "agent_type": agent_type,
                    "mode": mode,
                    "processing_time": round(processing_time, 3),
                    "timestamp": time.time()
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            
            print(f"Error in optimized agent execution: {e}")
            
            # Fallback to original system for reliability
            try:
                from core.views.document_search_api import document_response_api
                from django.http import HttpRequest
                
                # Create mock request for fallback
                fallback_request = HttpRequest()
                fallback_request.method = 'POST'
                fallback_request._body = json.dumps({
                    'query': query,
                    'twin_version_id': twin_version_id,
                    'chat_instance_id': chat_instance_id
                }).encode('utf-8')
                
                fallback_response = document_response_api(fallback_request)
                fallback_data = json.loads(fallback_response.content)
                
                return {
                    "success": True,
                    "response": fallback_data.get("openai_response", {}).get("content", ""),
                    "agent_type": "fallback",
                    "mode": "fallback",
                    "processing_time": round(time.time() - start_time, 3),
                    "timestamp": time.time(),
                    "fallback_used": True,
                    "original_error": str(e)
                }
                
            except Exception as fallback_error:
                return {
                    "success": False,
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                    "processing_time": round(time.time() - start_time, 3),
                    "timestamp": time.time()
                }
    
    def _get_agent_type(self, twin_version_id: str, mode: str = "full") -> str:
        """
        Fast agent type determination with O(1) lookup.
        
        Args:
            twin_version_id: Twin version identifier
            mode: Processing mode ('full', 'simple', 'simplified')
        """
        # Simple RAG agent for simplified mode
        if mode == "simplified":
            return "SIMPLE_RAG_AGENT"
        
        # HR Agent for specific twin ID
        if twin_version_id == "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455":
            return "HR_AGENT"
        
        # Default RAG agent for all others
        return "DEFAULT_RAG_AGENT"
    
    def execute_batch_queries(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple queries efficiently with optimized processing.
        
        Args:
            queries: List of query dictionaries with 'query', 'twin_version_id', 'chat_instance_id'
            
        Returns:
            List of processed responses
        """
        results = []
        start_time = time.time()
        
        for query_data in queries:
            try:
                result = self.execute_agent_query(
                    query=query_data.get('query'),
                    twin_version_id=query_data.get('twin_version_id'),
                    chat_instance_id=query_data.get('chat_instance_id'),
                    mode=query_data.get('mode', 'full')
                )
                results.append(result)
                
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "query_data": query_data
                })
        
        total_time = time.time() - start_time
        
        return {
            "batch_results": results,
            "total_queries": len(queries),
            "successful_queries": len([r for r in results if r.get("success", False)]),
            "total_processing_time": round(total_time, 3),
            "average_time_per_query": round(total_time / len(queries), 3) if queries else 0
        }
    
    def get_agent_health(self) -> Dict[str, Any]:
        """
        Get optimized agent system health status.
        """
        try:
            # Test basic functionality
            test_start = time.time()
            
            # Quick test query
            test_result = optimized_processor.get_simple_response(
                "test query", 
                "default", 
                "1"
            )
            
            test_time = time.time() - test_start
            
            return {
                "status": "healthy",
                "optimized_processor": "operational",
                "agent_configs_loaded": len(self.agent_configs),
                "test_response_time": round(test_time, 3),
                "available_agents": list(self.agent_configs.keys()),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the optimized system.
        """
        return {
            "optimization_features": [
                "Direct function calls to document_search_api.py",
                "Eliminated redundant processing loops",
                "O(1) agent type determination",  
                "O(log n) vector search complexity",
                "Single API call for response generation",
                "Optimized verification with size limits",
                "Fallback to original system for reliability"
            ],
            "supported_modes": ["simple", "full"],
            "supported_agents": ["DEFAULT_RAG_AGENT", "HR_AGENT"],
            "fallback_mechanism": "Automatic fallback to original document_search_api",
            "time_complexity": "O(log n) for vector search, O(1) for other operations"
        }
    
    def execute_simple_rag_query(self, query: str, twin_version_id: str, chat_instance_id: str) -> Dict[str, Any]:
        """
        Execute query using simplified RAG mode - bypasses metadata extraction for maximum speed.
        This is the fastest processing mode focusing purely on vector search and response generation.
        
        Args:
            query: User query
            twin_version_id: Twin version identifier
            chat_instance_id: Chat instance identifier
            
        Returns:
            Response from simplified RAG processing
        """
        start_time = time.time()
        
        try:
            # Direct simplified processing
            result = optimized_processor.process_simple_rag_query(query, twin_version_id, chat_instance_id)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "response": result["response"],
                "source_chunks_count": len(result.get("source_chunks", [])),
                "is_followup": result.get("is_followup", False),
                "agent_type": "simple_rag",
                "mode": "simplified",
                "processing_mode": "simplified",
                "metadata_bypassed": True,
                "verification_bypassed": True,
                "processing_time": round(processing_time, 3),
                "timestamp": time.time()
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            print(f"Error in simplified RAG processing: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "agent_type": "simple_rag",
                "mode": "simplified",
                "processing_time": round(processing_time, 3),
                "timestamp": time.time()
            }

# Global optimized agent manager instance
optimized_agent_manager = OptimizedAgentManager()

# Convenience functions for easy access
def process_optimized_query(query: str, twin_version_id: str, chat_instance_id: str, 
                           mode: str = "full") -> Dict[str, Any]:
    """
    Process query using optimized agent system.
    
    Args:
        query: User query
        twin_version_id: Twin version ID
        chat_instance_id: Chat instance ID
        mode: 'simple' for fastest response, 'full' for complete processing
        
    Returns:
        Processed response
    """
    return optimized_agent_manager.execute_agent_query(
        query, twin_version_id, chat_instance_id, mode
    )

def get_fast_response(query: str, twin_version_id: str, chat_instance_id: str) -> str:
    """
    Get fastest possible response without verification overhead.
    
    Args:
        query: User query
        twin_version_id: Twin version ID
        chat_instance_id: Chat instance ID
        
    Returns:
        Response string
    """
    result = optimized_agent_manager.execute_agent_query(
        query, twin_version_id, chat_instance_id, "simple"
    )
    return result.get("response", "")

def get_verified_response(query: str, twin_version_id: str, chat_instance_id: str) -> Dict[str, Any]:
    """
    Get complete response with verification.
    
    Args:
        query: User query
        twin_version_id: Twin version ID
        chat_instance_id: Chat instance ID
        
    Returns:
        Complete response with verification
    """
    return optimized_agent_manager.execute_agent_query(
        query, twin_version_id, chat_instance_id, "full"
    )

def get_simplified_rag_response(query: str, twin_version_id: str, chat_instance_id: str) -> Dict[str, Any]:
    """
    Get response using simplified RAG mode - bypasses metadata extraction for maximum speed.
    This is the fastest mode that focuses purely on vector search and response generation.
    
    Args:
        query: User query
        twin_version_id: Twin version ID
        chat_instance_id: Chat instance ID
        
    Returns:
        Complete simplified RAG response
    """
    return optimized_agent_manager.execute_simple_rag_query(query, twin_version_id, chat_instance_id)

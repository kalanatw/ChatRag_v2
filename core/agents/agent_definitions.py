"""
OpenAI Agent definitions for the Agentic RAG system.
This module defines different types of agents with specific instructions and tools.
"""

import json
from typing import Dict, List, Any
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Agent Instructions based on existing prompt templates
DEFAULT_RAG_AGENT_INSTRUCTIONS = """
You are a specialized RAG (Retrieval-Augmented Generation) assistant that helps users find information from technical documents. 

Your core responsibilities:
1. Analyze user queries and extract relevant metadata for document retrieval
2. Search through vector databases to find relevant information chunks
3. Generate accurate, concise responses based on retrieved information
4. Verify the accuracy of your responses using available tools
5. Provide proper document references for all information used

Guidelines for responses:
- Be concise, accurate, and complete
- Reference document knowledge appropriately
- Round numeric values to maximum 2 decimals
- Don't mention methodology or use words like 'chunks'
- For equipment issues, ask if user needs troubleshooting steps
- Always cite document sources as (REFERENCES: document names)
- If no relevant information found, inform user clearly
- Don't create answers from general knowledge when no relevant documents exist

Use the available tools to:
- Extract metadata from queries
- Search vector databases
- Verify response accuracy
- Check for similar previous queries
"""

SIMPLE_RAG_AGENT_INSTRUCTIONS = """
You are a fast, streamlined RAG (Retrieval-Augmented Generation) assistant focused purely on document search and response generation.

Your core responsibilities (simplified mode):
1. Perform direct vector search on user queries without metadata processing
2. Generate accurate, concise responses based on retrieved information chunks
3. Provide proper document references for all information used

Guidelines for responses:
- Be concise, accurate, and complete
- Reference document knowledge appropriately
- Round numeric values to maximum 2 decimals
- Don't mention methodology or use words like 'chunks'
- Always cite document sources as (REFERENCES: document names)
- If no relevant information found, inform user clearly
- Don't create answers from general knowledge when no relevant documents exist

This simplified mode prioritizes speed by:
- Bypassing metadata extraction for fastest response times
- Using direct vector similarity search only
- Minimizing processing overhead for maximum performance

Use the available tools to:
- Search vector databases directly
- Generate responses based on retrieved content
"""

HR_AGENT_INSTRUCTIONS = """
You are an HR helpdesk assistant providing clear, practical, and professional information about HR policies and procedures.

Your core responsibilities:
1. Provide accurate HR policy information from company documents
2. Extract HR-related metadata from user queries
3. Search HR policy databases for relevant information
4. Verify HR information accuracy using specialized tools
5. Format responses professionally using markdown

HR Contact Information: hr@aitkenspence.com

Guidelines for HR responses:
- Use professional but friendly HR language
- Stick strictly to HR policies in documents
- Give practical, actionable information
- Use markdown formatting with bullet points and headings
- Be concise and direct
- Ask for clarification if information is unclear
- For escalations, direct users to hr@aitkenspence.com
- Round numbers to 2 decimals
- Provide document references at the end

Response Format Requirements:
- Use bullet points for multiple items
- Apply bold text and headings where appropriate
- Keep formatting clean and simple
- End with (REFERENCES: document names) when using document content

If no relevant HR policy information is available, inform the user clearly and don't create answers from general knowledge.

Use the available tools to:
- Extract HR-specific metadata
- Search HR policy databases
- Verify HR information accuracy
- Check consistency with previous HR responses
"""

# Tool definitions for agents
METADATA_EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_metadata",
        "description": "Extract relevant metadata from user queries to improve document search accuracy",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The user query to extract metadata from"
                },
                "twin_version_id": {
                    "type": "string", 
                    "description": "The twin version ID for context"
                },
                "chat_instance_id": {
                    "type": "string",
                    "description": "The chat instance ID for context"
                }
            },
            "required": ["query", "twin_version_id", "chat_instance_id"]
        }
    }
}

VECTOR_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_vector_database",
        "description": "Search the vector database for relevant document chunks based on query and metadata",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "query_vector": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Query embedding vector"
                },
                "twin_version_id": {
                    "type": "string",
                    "description": "Twin version ID for context"
                },
                "metadata": {
                    "type": "object",
                    "description": "Extracted metadata for filtering"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 12
                }
            },
            "required": ["query", "query_vector", "twin_version_id"]
        }
    }
}

SIMPLE_VECTOR_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "simple_search_vector_database",
        "description": "Fast vector search without metadata extraction - bypasses metadata processing for maximum speed",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "query_vector": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Query embedding vector"
                },
                "twin_version_id": {
                    "type": "string",
                    "description": "Twin version ID for context"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 12
                }
            },
            "required": ["query", "query_vector", "twin_version_id"]
        }
    }
}

RESPONSE_VERIFICATION_TOOL = {
    "type": "function",
    "function": {
        "name": "verify_response_accuracy",
        "description": "Verify the accuracy and consistency of generated responses",
        "parameters": {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "The generated response to verify"
                },
                "source_chunks": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "The source document chunks used for response"
                },
                "original_query": {
                    "type": "string", 
                    "description": "The original user query"
                },
                "agent_type": {
                    "type": "string",
                    "description": "Type of agent (default_rag or hr_agent)"
                }
            },
            "required": ["response", "source_chunks", "original_query", "agent_type"]
        }
    }
}

HR_VERIFICATION_TOOL = {
    "type": "function", 
    "function": {
        "name": "verify_hr_response",
        "description": "Specialized verification tool for HR responses to ensure policy compliance",
        "parameters": {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "The HR response to verify"
                },
                "hr_policy_chunks": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "HR policy document chunks used"
                },
                "query": {
                    "type": "string",
                    "description": "Original HR query"
                },
                "compliance_check": {
                    "type": "boolean",
                    "description": "Whether to perform compliance verification",
                    "default": True
                }
            },
            "required": ["response", "hr_policy_chunks", "query"]
        }
    }
}

SIMILAR_QUERY_TOOL = {
    "type": "function",
    "function": {
        "name": "find_similar_queries",
        "description": "Find similar previous queries for consistency, especially for HR agent",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Current user query"
                },
                "chat_instance_id": {
                    "type": "string",
                    "description": "Chat instance ID"
                },
                "twin_version_id": {
                    "type": "string",
                    "description": "Twin version ID for context"
                }
            },
            "required": ["query", "chat_instance_id", "twin_version_id"]
        }
    }
}

# Agent configuration constants
DEFAULT_RAG_AGENT = "DEFAULT_RAG_AGENT"
SIMPLE_RAG_AGENT = "SIMPLE_RAG_AGENT"
HR_AGENT = "HR_AGENT"

# Agent configurations
AGENT_CONFIGS = {
    DEFAULT_RAG_AGENT: {
        "name": "Default RAG Agent",
        "instructions": DEFAULT_RAG_AGENT_INSTRUCTIONS,
        "model": "gpt-4o-mini",
        "tools": [
            METADATA_EXTRACTION_TOOL,
            VECTOR_SEARCH_TOOL, 
            RESPONSE_VERIFICATION_TOOL,
            SIMILAR_QUERY_TOOL
        ],
        "temperature": 0.1
    },
    SIMPLE_RAG_AGENT: {
        "name": "Simple RAG Agent",
        "instructions": SIMPLE_RAG_AGENT_INSTRUCTIONS,
        "model": "gpt-4o-mini",
        "tools": [
            SIMPLE_VECTOR_SEARCH_TOOL
        ],
        "temperature": 0.1
    },
    HR_AGENT: {
        "name": "HR Policy Agent", 
        "instructions": HR_AGENT_INSTRUCTIONS,
        "model": "gpt-4o-mini",
        "tools": [
            METADATA_EXTRACTION_TOOL,
            VECTOR_SEARCH_TOOL,
            RESPONSE_VERIFICATION_TOOL,
            HR_VERIFICATION_TOOL,
            SIMILAR_QUERY_TOOL
        ],
        "temperature": 0.1
    }
}

# Twin ID to agent mapping
TWIN_AGENT_MAP = {
    "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455": HR_AGENT,
    "default": DEFAULT_RAG_AGENT
}

def get_agent_config(twin_version_id: str) -> Dict[str, Any]:
    """
    Get agent configuration based on twin version ID.
    
    Args:
        twin_version_id: The twin version identifier
        
    Returns:
        Dict containing agent configuration
    """
    agent_type = TWIN_AGENT_MAP.get(twin_version_id, DEFAULT_RAG_AGENT)
    return AGENT_CONFIGS[agent_type]

def create_agent(twin_version_id: str) -> str:
    """
    Create an OpenAI assistant agent for the specified twin version.
    
    Args:
        twin_version_id: The twin version identifier
        
    Returns:
        Assistant ID string
    """
    config = get_agent_config(twin_version_id)
    
    assistant = client.beta.assistants.create(
        name=config["name"],
        instructions=config["instructions"],
        model=config["model"],
        tools=config["tools"],
        temperature=config.get("temperature", 0.1)
    )
    
    return assistant.id

def get_or_create_agent(twin_version_id: str, force_recreate: bool = False) -> str:
    """
    Get existing agent or create new one for the twin version.
    
    Args:
        twin_version_id: The twin version identifier
        force_recreate: Whether to force recreation of agent
        
    Returns:
        Assistant ID string
    """
    # In production, you'd want to store agent IDs in database
    # For now, we'll create new agents each time
    return create_agent(twin_version_id)

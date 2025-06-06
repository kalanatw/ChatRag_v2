"""
Optimized Agents package for the Agentic RAG system.
This package contains optimized agent definitions, tools, and management functionality
that directly uses functions from document_search_api.py for maximum performance.
"""

# Import optimized agent configurations and tools
from .agent_definitions import AGENT_CONFIGS, DEFAULT_RAG_AGENT, SIMPLE_RAG_AGENT, HR_AGENT
from .optimized_agent_tools import OPTIMIZED_AGENT_TOOLS, optimized_processor
from .optimized_agent_manager import (
    optimized_agent_manager,
    process_optimized_query,
    get_fast_response,
    get_verified_response
)

# Import mappings
TWIN_AGENT_MAP = {
    "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455": HR_AGENT,  # HR specific twin
    "default": DEFAULT_RAG_AGENT  # Default for all other twins
}

# For backward compatibility
agent_manager = optimized_agent_manager
AGENT_TOOLS = OPTIMIZED_AGENT_TOOLS

def get_agent_config(twin_version_id):
    """Get agent configuration for backward compatibility."""
    agent_type = TWIN_AGENT_MAP.get(twin_version_id, DEFAULT_RAG_AGENT)
    return AGENT_CONFIGS.get(agent_type, AGENT_CONFIGS[DEFAULT_RAG_AGENT])

# Export optimized components
__all__ = [
    'AGENT_CONFIGS',
    'DEFAULT_RAG_AGENT',
    'SIMPLE_RAG_AGENT',
    'HR_AGENT',
    'OPTIMIZED_AGENT_TOOLS',
    'TWIN_AGENT_MAP',
    'optimized_agent_manager',
    'optimized_processor',
    'process_optimized_query',
    'get_fast_response',
    'get_verified_response',
    'agent_manager',  # Backward compatibility
    'AGENT_TOOLS',    # Backward compatibility
    'get_agent_config' # Backward compatibility
]

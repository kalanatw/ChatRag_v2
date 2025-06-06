# Agentic RAG System Migration Guide

## Overview

This document describes the conversion of the existing RAG chatbot system to use OpenAI Agents SDK (Assistants API) while maintaining all current functionalities. The system now operates as an Agentic RAG system with specialized tools for response verification, metadata extraction, and agent-specific behavior.

## Key Changes

### 1. **Agent Architecture**
- **Default RAG Agent**: Handles general technical document queries
- **HR Agent**: Specialized for HR policy queries with enhanced verification
- **Tool-based execution**: Each agent has access to specialized tools for metadata extraction, vector search, and response verification

### 2. **New Components**

#### Agent Definitions (`core/agents/agent_definitions.py`)
- Defines agent instructions, tools, and configurations
- Maps twin IDs to appropriate agent types
- Configures specialized behavior for each agent type

#### Agent Tools (`core/agents/agent_tools.py`)
- `extract_metadata`: AI-powered metadata extraction from queries
- `search_vector_database`: Enhanced vector search with metadata filtering
- `verify_response_accuracy`: General response verification
- `verify_hr_response`: HR-specific policy compliance verification
- `find_similar_queries`: Consistency checking for HR responses

#### Agent Manager (`core/agents/agent_manager.py`)
- Orchestrates agent creation and conversation management
- Handles tool execution and OpenAI Assistant API interactions
- Provides both full agent orchestration and direct tool execution modes

### 3. **New API Endpoints**

#### Agentic Document Response API (`/core/api/agentic-document-response/`)
- **Primary endpoint** for the new agentic system
- Backward compatible with fallback to original system
- Supports both `full` and `direct` execution modes
- Enhanced response metadata with verification results

#### Agent Health Check (`/core/api/agent-health/`)
- Monitor agent system status
- View active agents and threads
- Check available tools and configurations

#### Agent Cleanup (`/core/api/agent-cleanup/`)
- Clean up agent and thread resources
- Supports targeted or bulk cleanup operations

## API Usage

### Basic Query (Default RAG Agent)
```json
POST /core/api/agentic-document-response/
{
    "query": "What is the troubleshooting procedure for compressor maintenance?",
    "twin_version_id": "default",
    "chat_instance_id": "chat_001",
    "use_agents": true,
    "agent_mode": "direct"
}
```

### HR Query (HR Agent)
```json
POST /core/api/agentic-document-response/
{
    "query": "What is the annual leave policy?",
    "twin_version_id": "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455",
    "chat_instance_id": "hr_chat_001",
    "use_agents": true,
    "agent_mode": "direct"
}
```

### Enhanced Response Format
```json
{
    "openai_response": {
        "content": "Generated response content..."
    },
    "agent_metadata": {
        "agent_type": "default_rag",
        "verification": {
            "accuracy_score": 95,
            "guideline_compliance": true,
            "reference_quality": "good",
            "overall_assessment": "pass"
        },
        "hr_verification": {
            "policy_compliance": true,
            "professional_tone": true,
            "overall_hr_assessment": "approved"
        },
        "search_results_count": 8,
        "similar_response_found": false,
        "processing_mode": "direct"
    }
}
```

## Twin ID Mappings

- `default`: Default RAG Agent for general technical queries
- `b7586e58-9a07-47f6-8049-43d6d6f2c5e54455`: HR Agent for HR policy queries

## Agent Features

### Default RAG Agent
- General document search and response generation
- Technical troubleshooting guidance
- Equipment-specific information retrieval
- Standard response verification

### HR Agent
- HR policy-specific responses
- Professional markdown formatting
- Policy compliance verification
- Consistent response checking for similar queries
- Proper escalation guidance to hr@aitkenspence.com

## Verification Tools

### General Verification
- **Accuracy scoring**: 0-100 based on source alignment
- **Guideline compliance**: Adherence to formatting rules
- **Reference quality**: Quality of document citations
- **Improvement suggestions**: AI-generated recommendations

### HR-Specific Verification
- **Policy compliance**: Alignment with HR policies
- **Professional tone**: Appropriate business communication
- **Markdown quality**: Proper formatting standards
- **Escalation appropriateness**: Correct guidance for complex issues
- **Contact information accuracy**: Verification of HR email

## Backward Compatibility

The system maintains full backward compatibility:

1. **Original API**: `/core/api/document-response/` continues to work unchanged
2. **Fallback mechanism**: Agentic API falls back to original system on errors
3. **Optional agent usage**: Set `use_agents: false` to use original system
4. **Existing features preserved**: All prompt templates, similar query detection, and metadata extraction

## Performance Modes

### Direct Mode (`agent_mode: "direct"`)
- **Recommended for production**
- Direct tool execution without full Assistant API orchestration
- Faster response times
- Lower token consumption
- More predictable behavior

### Full Mode (`agent_mode: "full"`)
- Complete OpenAI Assistant orchestration
- Agent makes autonomous decisions about tool usage
- Higher token consumption
- More complex debugging

## Migration Benefits

1. **Enhanced accuracy**: Multi-layered verification tools
2. **Specialized agents**: Domain-specific behavior for different use cases
3. **Improved consistency**: Especially for HR responses
4. **Better monitoring**: Health checks and agent status tracking
5. **Flexible deployment**: Multiple execution modes
6. **Graceful degradation**: Automatic fallback mechanisms

## Testing

Run the test script to verify system functionality:
```bash
python test_agentic_system.py
```

Tests include:
- Agent health check
- Default RAG agent functionality
- HR agent functionality
- Fallback behavior verification

## Monitoring

### Health Check
```bash
curl http://localhost:8000/core/api/agent-health/
```

### Agent Cleanup
```bash
curl -X POST http://localhost:8000/core/api/agent-cleanup/ \
  -H "Content-Type: application/json" \
  -d '{"cleanup_type": "all"}'
```

## Production Considerations

1. **Start with direct mode** for stability
2. **Monitor verification scores** to ensure quality
3. **Use health checks** for system monitoring
4. **Implement regular cleanup** for resource management
5. **Fallback testing** to ensure original system availability

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure Django settings are properly configured
2. **OpenAI API errors**: Check API key and rate limits
3. **Agent timeouts**: Increase timeout values for complex queries
4. **Tool execution failures**: Check individual tool implementations

### Debug Information
- Agent execution logs in Django console
- Tool execution results in response metadata
- Verification scores for quality assessment
- Health check endpoint for system status

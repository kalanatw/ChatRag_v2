"""
Optimized Agentic RAG API endpoints.
This module provides the optimized agent-based document search API that directly
uses functions from document_search_api.py for maximum performance.
"""

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.serializer import OpenAIResponseSerializer

# Import optimized agent system
from core.agents.optimized_agent_manager import (
    optimized_agent_manager,
    process_optimized_query,
    get_fast_response,
    get_verified_response,
    get_simplified_rag_response
)

from memory_manager import save_and_limit_chat_history, get_memory
from core.models import ChatHistory
from datetime import datetime
import traceback

def print_timestamp():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current timestamp: {formatted_time}")

def save_chat_history_to_db(user_query, chatbot_response, twin_version_id, chat_instance_id):
    """Save chat history to database."""
    try:
        # Get or create chat instance
        from core.models import ChatInstance, ChatHistory
        chat_instance, created = ChatInstance.objects.get_or_create(
            id=chat_instance_id,
            defaults={'twin_id': twin_version_id}
        )
        
        chat_history = ChatHistory(
            user_query=user_query,
            chatbot_response=chatbot_response,
            twin_id=twin_version_id,  # Use twin_id instead of twin_version_id
            chat_instance=chat_instance
        )
        chat_history.save()
        print("Chat history saved to database.")
    except Exception as e:
        print(f"Error saving chat history: {e}")

@extend_schema(
    summary="Optimized Agentic Document Response API",
    description=(
        "This endpoint accepts a user query regarding a specific twin scenario and "
        "returns a comprehensive response using the optimized OpenAI Agents system. "
        "The system directly uses functions from document_search_api.py for maximum "
        "performance with minimal time complexity. Supports both 'simple' mode for "
        "fastest responses and 'full' mode for complete verification."
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The user query for which the search is being performed.',
                },
                'twin_version_id': {
                    'type': 'string',
                    'description': 'The version identifier for the twin or digital twin model.',
                },
                'chat_instance_id': {
                    'type': 'integer',
                    'description': 'The identifier for the chat instance.',
                },
                'use_agents': {
                    'type': 'boolean',
                    'description': 'Whether to use the optimized agent system (default: true)',
                    'default': True
                },
                'agent_mode': {
                    'type': 'string',
                    'description': 'Agent execution mode: "simple" for fastest response, "full" for complete verification, "simplified" for pure RAG without metadata',
                    'default': 'simple',
                    'enum': ['simple', 'full', 'simplified']
                }
            },
            'required': ['query', 'twin_version_id', 'chat_instance_id'],
        }
    },
    responses={
        200: OpenAIResponseSerializer,
        400: OpenApiResponse(
            description='Bad Request - Query is required.',
            response={
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {
                            'type': 'string',
                            'example': 'Query is required.'
                        }
                    }
                }
            }
        ),
        500: OpenApiResponse(
            description='Internal Server Error - An error occurred while processing the request.',
            response={
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {
                            'type': 'string',
                            'example': 'Error: Some error message'
                        }
                    }
                }
            }
        ),
    }
)
@api_view(['POST'])
def agentic_document_response_api(request):
    """
    Optimized agentic document response API endpoint using direct core functions.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query')
            twin_version_id = data.get('twin_version_id')
            chat_instance_id = data.get('chat_instance_id')
            use_agents = data.get('use_agents', True)
            agent_mode = data.get('agent_mode', 'simple')  # 'simple' or 'full'
            
            print(f"Received optimized agentic request - Query: {query}, Twin: {twin_version_id}, Mode: {agent_mode}")
            print_timestamp()

            if not query:
                return JsonResponse({'error': 'Query is required'}, status=400)
            
            if not use_agents:
                # Fallback to original system
                from django.test import RequestFactory
                from core.views.document_search_api import document_response_api
                
                factory = RequestFactory()
                django_request = factory.post(
                    '/core/api/document-response/',
                    data=json.dumps(data),
                    content_type='application/json'
                )
                
                return document_response_api(django_request)
            
            # Process query using optimized agent system
            result = optimized_agent_manager.execute_agent_query(
                query=query,
                twin_version_id=twin_version_id,
                chat_instance_id=str(chat_instance_id),
                mode=agent_mode
            )
            
            print(f"Optimized agent processing result: {result}")
            print_timestamp()
            
            if result.get("success"):
                response_content = result["response"]
                
                # Prepare response
                openai_response = {
                    "content": response_content,
                }
                
                final_response = {
                    "openai_response": openai_response,
                    "agent_metadata": {
                        "agent_type": result.get("agent_type"),
                        "processing_mode": result.get("mode"),
                        "processing_time": result.get("processing_time"),
                        "verification": result.get("verification"),
                        "source_chunks_count": result.get("source_chunks_count", 0),
                        "is_followup": result.get("is_followup", False),
                        "optimized": True,
                        "fallback_used": result.get("fallback_used", False)
                    }
                }
                
                print(f"Optimized agent response generated successfully in {result.get('processing_time', 0)}s")
                print_timestamp()
                
                return JsonResponse(final_response)
            else:
                # Agent processing failed, return error
                print(f"Optimized agent processing failed: {result.get('error')}")
                
                return JsonResponse({
                    "error": f"Agent processing failed: {result.get('error')}",
                    "fallback_error": result.get("fallback_error"),
                    "processing_time": result.get("processing_time")
                }, status=500)
                
        except Exception as e:
            print(f"Error in optimized agentic API: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Fallback to original system on error
            try:
                from django.test import RequestFactory
                from core.views.document_search_api import document_response_api
                
                factory = RequestFactory()
                django_request = factory.post(
                    '/core/api/document-response/',
                    data=json.dumps(data),
                    content_type='application/json'
                )
                
                print("Falling back to original system due to error...")
                return document_response_api(django_request)
            except Exception as fallback_error:
                return JsonResponse(
                    {"error": f"Both optimized agent and fallback systems failed. Agent error: {str(e)}, Fallback error: {str(fallback_error)}"},
                    status=500,
                )

@extend_schema(
    summary="Optimized Agent Health Check",
    description="Check the health and status of the optimized agent system.",
    responses={
        200: OpenApiResponse(
            description='Optimized agent system is healthy',
            response={
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string'},
                        'optimization_features': {'type': 'array'},
                        'performance_metrics': {'type': 'object'}
                    }
                }
            }
        ),
    }
)
@api_view(['GET'])
def agent_health_check(request):
    """
    Health check endpoint for the optimized agent system.
    """
    try:
        health_status = optimized_agent_manager.get_agent_health()
        performance_metrics = optimized_agent_manager.get_performance_metrics()
        
        combined_status = {
            **health_status,
            "performance_metrics": performance_metrics,
            "optimized_system": True
        }
        
        return JsonResponse(combined_status)
        
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e),
            "optimized_system": True,
            "timestamp": datetime.now().isoformat()
        }, status=500)

@extend_schema(
    summary="Fast Response API",
    description="Get the fastest possible response without verification overhead.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string'},
                'twin_version_id': {'type': 'string'},
                'chat_instance_id': {'type': 'integer'}
            },
            'required': ['query', 'twin_version_id', 'chat_instance_id']
        }
    },
    responses={200: OpenAIResponseSerializer}
)
@api_view(['POST'])
def fast_response_api(request):
    """
    Fast response API for minimum latency responses.
    """
    try:
        data = json.loads(request.body)
        query = data.get('query')
        twin_version_id = data.get('twin_version_id')
        chat_instance_id = data.get('chat_instance_id')
        
        if not query:
            return JsonResponse({'error': 'Query is required'}, status=400)
        
        print(f"Fast response request - Query: {query}")
        start_time = datetime.now()
        
        response = get_fast_response(query, twin_version_id, str(chat_instance_id))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return JsonResponse({
            "openai_response": {"content": response},
            "metadata": {
                "mode": "fast",
                "processing_time": round(processing_time, 3),
                "optimized": True
            }
        })
        
    except Exception as e:
        return JsonResponse({
            "error": f"Fast response failed: {str(e)}"
        }, status=500)

@extend_schema(
    summary="Batch Processing API",
    description="Process multiple queries efficiently using optimized agent system.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'queries': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string'},
                            'twin_version_id': {'type': 'string'},
                            'chat_instance_id': {'type': 'integer'},
                            'mode': {'type': 'string', 'enum': ['simple', 'full']}
                        }
                    }
                }
            },
            'required': ['queries']
        }
    },
    responses={200: OpenApiResponse(description='Batch processing results')}
)
@api_view(['POST'])
def batch_processing_api(request):
    """
    Batch processing API for multiple queries.
    """
    try:
        data = json.loads(request.body)
        queries = data.get('queries', [])
        
        if not queries:
            return JsonResponse({'error': 'Queries list is required'}, status=400)
        
        print(f"Batch processing request - {len(queries)} queries")
        
        results = optimized_agent_manager.execute_batch_queries(queries)
        
        return JsonResponse(results)
        
    except Exception as e:
        return JsonResponse({
            "error": f"Batch processing failed: {str(e)}"
        }, status=500)

@extend_schema(
    summary="Agent Performance Metrics",
    description="Get detailed performance metrics for the optimized agent system.",
    responses={200: OpenApiResponse(description='Performance metrics')}
)
@api_view(['GET'])
def agent_performance_metrics(request):
    """
    Get performance metrics for the optimized agent system.
    """
    try:
        metrics = optimized_agent_manager.get_performance_metrics()
        health = optimized_agent_manager.get_agent_health()
        
        return JsonResponse({
            "performance_metrics": metrics,
            "health_status": health,
            "system_info": {
                "direct_function_integration": True,
                "original_system_fallback": True,
                "optimal_time_complexity": "O(log n) for vector search",
                "supported_modes": ["simple", "full"],
                "batch_processing": True
            }
        })
        
    except Exception as e:
        return JsonResponse({
            "error": f"Failed to get performance metrics: {str(e)}"
        }, status=500)

@extend_schema(
    summary="Simplified RAG Document Response API",
    description=(
        "This endpoint provides the fastest possible document search response by "
        "bypassing metadata extraction entirely. This simplified mode focuses purely "
        "on vector similarity search and response generation for maximum speed. "
        "Ideal for use cases where speed is more important than metadata-filtered accuracy."
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The user query for document search.',
                },
                'twin_version_id': {
                    'type': 'string',
                    'description': 'The version identifier for the twin or digital twin model.',
                },
                'chat_instance_id': {
                    'type': 'integer',
                    'description': 'The identifier for the chat instance.',
                }
            },
            'required': ['query', 'twin_version_id', 'chat_instance_id'],
        }
    },
    responses={
        200: OpenApiResponse(
            description='Successful simplified RAG response',
            response={
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'response': {'type': 'string'},
                        'processing_time': {'type': 'number'},
                        'metadata_bypassed': {'type': 'boolean'},
                        'source_chunks_count': {'type': 'integer'},
                        'mode': {'type': 'string'}
                    }
                }
            }
        ),
        400: OpenApiResponse(
            description='Bad Request - Invalid parameters',
        ),
        500: OpenApiResponse(
            description='Internal Server Error'
        )
    }
)
@csrf_exempt
@api_view(['POST'])
def simplified_rag_document_response_api(request):
    """
    Simplified RAG Document Response API that bypasses metadata extraction.
    This is the fastest processing mode for pure vector search and response generation.
    """
    print("Simplified RAG Document Response API called")
    print_timestamp()
    
    try:
        # Parse request data
        if hasattr(request, 'data') and request.data:
            data = request.data
        else:
            data = json.loads(request.body.decode('utf-8'))
        
        query = data.get('query')
        twin_version_id = data.get('twin_version_id')
        chat_instance_id = data.get('chat_instance_id')
        
        # Validate required parameters
        if not query:
            return JsonResponse({'error': 'Query is required'}, status=400)
        if not twin_version_id:
            return JsonResponse({'error': 'Twin version ID is required'}, status=400)
        if not chat_instance_id:
            return JsonResponse({'error': 'Chat instance ID is required'}, status=400)
        
        print(f"Simplified RAG query: {query}")
        print(f"Twin version ID: {twin_version_id}")
        print(f"Chat instance ID: {chat_instance_id}")
        print_timestamp()
        
        # Process using simplified RAG mode
        result = get_simplified_rag_response(query, twin_version_id, str(chat_instance_id))
        
        print(f"Simplified RAG processing result: {result}")
        print_timestamp()
        
        if result.get("success"):
            response_data = {
                "response": result["response"],
                "processing_time": result["processing_time"],
                "metadata_bypassed": result.get("metadata_bypassed", True),
                "verification_bypassed": result.get("verification_bypassed", True),
                "source_chunks_count": result.get("source_chunks_count", 0),
                "is_followup": result.get("is_followup", False),
                "mode": "simplified",
                "agent_type": "simple_rag",
                "timestamp": result.get("timestamp")
            }
            
            print(f"Simplified RAG response generated in {result.get('processing_time', 0)}s")
            print_timestamp()
            
            return JsonResponse(response_data)
        else:
            print(f"Simplified RAG processing failed: {result.get('error')}")
            return JsonResponse({
                'error': f'Simplified RAG processing failed: {result.get("error")}',
                'mode': 'simplified'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        print(f"Error in simplified RAG API: {e}")
        print(traceback.format_exc())
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

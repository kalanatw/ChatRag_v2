from django.urls import path
from core.views.document_search_api import document_response_api
from .views.decision_pipeline_api import api_decision
from core.views.document_update_api import document_update_api
from core.views.get_document_list_api import get_documents_list_api
from core.views.load_chat_history_api import load_chat_history_api
from core.views.create_chat_instance_api import create_chat_instance_api
from core.views.get_chat_instances_api import get_chat_instances_api
from core.views.document_upload_api import document_upload_api
from core.views.document_delete_api import document_delete_api
from core.views.agentic_document_api import (
    agentic_document_response_api, 
    agent_health_check, 
    fast_response_api,
    batch_processing_api,
    agent_performance_metrics,
    simplified_rag_document_response_api
)

urlpatterns = [
    # Original RAG endpoints
    path('api/document-response/', document_response_api, name='documet_search_api'),
    path('api/document-update/', document_update_api, name='document_update_api'),
    path('api/get-documents-list/', get_documents_list_api, name='get_documents_list_api'),
    path('api/load-chat-history/', load_chat_history_api, name='load_chat_history_api'),
    path('api/create-chat-instance/', create_chat_instance_api, name='create_chat_instance_api'),
    path('api/get-chat-instances/', get_chat_instances_api, name='get_chat_instances_api'),
    path('api/document-upload/', document_upload_api, name='document_upload_api'),
    path('api/document-delete/', document_delete_api, name='document_delete_api'),
    
    # Optimized Agentic RAG endpoints
    path('api/agentic-document-response/', agentic_document_response_api, name='agentic_document_response_api'),
    path('api/simplified-rag/', simplified_rag_document_response_api, name='simplified_rag_document_response_api'),
    path('api/agent-health/', agent_health_check, name='agent_health_check'),
    path('api/fast-response/', fast_response_api, name='fast_response_api'),
    path('api/batch-processing/', batch_processing_api, name='batch_processing_api'),
    path('api/agent-performance/', agent_performance_metrics, name='agent_performance_metrics'),
    
    # path('api/api-decision/', api_decision, name='api_decesion'),
]


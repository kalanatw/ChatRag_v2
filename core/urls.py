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

urlpatterns = [
    path('api/document-response/', document_response_api, name='documet_search_api'),
    path('api/document-update/', document_update_api, name='document_update_api'),
    path('api/get-documents-list/', get_documents_list_api, name='get_documents_list_api'),
    path('api/load-chat-history/', load_chat_history_api, name='load_chat_history_api'),
    path('api/create-chat-instance/', create_chat_instance_api, name='create_chat_instance_api'),
    path('api/get-chat-instances/', get_chat_instances_api, name='get_chat_instances_api'),
    path('api/document-upload/', document_upload_api, name='document_upload_api'),
    path('api/document-delete/', document_delete_api, name='document_delete_api')
    # path('api/api-decision/', api_decision, name='api_decesion'),
]


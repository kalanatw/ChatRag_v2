from django.http import JsonResponse
from core.models import ChatHistory
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.decorators import api_view
from core.serializer import ChatHistoryResponseSerializer


LIMIT = 3

@extend_schema(
    summary="Load Chat History API",
    description="Retrieve the chat history for a given chat instance in a particular twin.",
    parameters=[
        OpenApiParameter('twin_id', str, description='The unique identifier for the twin.', required=True),
        OpenApiParameter('chat_instance_id', int, description='The unique identifier for the chat instance.', required=True)
    ],
    responses={
        200: OpenApiResponse(
            description='Chat history retrieved successfully',
        response=ChatHistoryResponseSerializer
        ),
        400: OpenApiResponse(
            description='Bad Request - twin_id is required',
            response={
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        ),
        500: OpenApiResponse(
            description='Internal Server Error',
            response={
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        )
    }
)


@api_view(['GET'])
def load_chat_history_api(request):
    if request.method == 'GET':
        twin_id = request.GET.get('twin_id')
        chat_instance_id = request.GET.get('chat_instance_id')
        
        print(f"twin_id: {twin_id}, chat_instance_id: {chat_instance_id}")

        if not twin_id:
            return JsonResponse({'error': 'twin_id is required'}, status=400)
        if not chat_instance_id:
            return JsonResponse({'error': 'chat_instance_id is required'}, status=400)
        
        chat_instance_id = int(chat_instance_id)

        
        #Fetch chat history for the given twin_id and chat_instance_id
        chat_history = ChatHistory.objects.filter(
            twin_id=twin_id,
            chat_instance_id=chat_instance_id
        ).order_by('-id')
        

        # If no chat history found for the twin_id
        if not chat_history.exists():
            return JsonResponse({'chat_history': []}, status=200)
        
        chat_history_list = list(chat_history.values('user_query', 'chatbot_response'))[::-1]

        return JsonResponse({
            'chat_history': chat_history_list
        }, status=200)

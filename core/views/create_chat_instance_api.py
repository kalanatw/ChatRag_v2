from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from core.models import ChatInstance
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from core.serializer import ChatInstanceSerializer

@extend_schema(
    summary="Create Chat Instance API",
    description="Create a new chat instance for the given twin_id.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'twin_id': {
                    'type': 'string', 
                    'description': 'The unique identifier for the twin.'
                }
            },
            'required': ['twin_id']
        }
    },
    responses={
        201: OpenApiResponse(
            description='Chat instance created successfully',
            response=ChatInstanceSerializer
        ),
        400: OpenApiResponse(
            description='Bad Request - twin_id is required',
            response={
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    },
                'examples': {
                    'application/json': {
                        'error': 'twin_id is required'
                    }
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
                    },
                'examples': {
                    'application/json': {
                        'error': 'An unexpected error occurred. Please try again later.'
                    }
                }
                }
            }
        )
    }
)

@api_view(['POST'])
def create_chat_instance_api(request):
    if request.method == 'POST':
        twin_id = request.data.get('twin_id')
        
        if not twin_id:
            return JsonResponse({'error': 'twin_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        chat_instance = ChatInstance(twin_id=twin_id)
        chat_instance.save()
        
        # Return the response with the created instance data
        return JsonResponse({
            'id': chat_instance.id,
            'twin_id': chat_instance.twin_id,
            'created_at': chat_instance.created_at
        }, status=status.HTTP_201_CREATED)

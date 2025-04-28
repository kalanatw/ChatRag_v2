from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import ChatInstance
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, extend_schema_field
from rest_framework import serializers

class ChatInstanceResponseSerializerWithoutTwinId(serializers.ModelSerializer):
    class Meta:
        model = ChatInstance
        fields = ['id', 'created_at']
        
@extend_schema_field(ChatInstanceResponseSerializerWithoutTwinId)
@extend_schema(
    summary="Get Chat Instances API",
    description="Retrieve a list of all available chat instances for a given twin_id.",
    parameters=[
        OpenApiParameter('twin_id', str, description='The unique identifier for the twin.', required=True)
    ],
    responses={
        200: OpenApiResponse(
            description='A list of all available chat instances',
            response=ChatInstanceResponseSerializerWithoutTwinId(many=True),

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
def get_chat_instances_api(request):
    if request.method == 'GET':
        twin_id = request.GET.get('twin_id')
        
        if not twin_id:
            return JsonResponse({'error': 'twin_id is required'}, status=400)
        
        chat_instances = ChatInstance.objects.filter(twin_id=twin_id).values('id', 'created_at')
        return Response(list(chat_instances), status=200)

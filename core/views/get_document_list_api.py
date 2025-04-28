import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from core.models import VectorDB
from core.serializer import DocumentListResponseSerializer

@extend_schema(
    summary="Get Documents List API",
    description="Retrieve a list of all available documents for a given twin_id.",
    parameters=[
        OpenApiParameter('twin_id', str, description='The unique identifier for the twin.', required=True)
    ],
    responses={
        200: DocumentListResponseSerializer,
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
def get_documents_list_api(request):
    try:
        twin_id = request.GET.get('twin_id')
        
        if not twin_id:
            return JsonResponse({'error': 'twin_id is required'}, status=400)

        documents = VectorDB.objects.filter(twin_id=twin_id).distinct('pdf_id').values('pdf_id', 'pdf')

        # Convert the QuerySet to a list
        documents_list = list(documents)

        final_response = {
            'documents': documents_list,
        }

    except Exception as e:
        return JsonResponse({"error": f"Error: {str(e)}"}, status=500)

    return JsonResponse(final_response)



# import json
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from core.models import VectorDB

# @csrf_exempt
# def get_documents_list_api(request):
#     if request.method == 'GET':
#         try:
#             twin_id = request.GET.get('twin_id')
            
#             if not twin_id:
#                 return JsonResponse({'error': 'twin_id is required'}, status=400)

#             documents = VectorDB.objects.filter(twin_id=twin_id).distinct('pdf_id').values('pdf_id', 'pdf')

#             # Convert the QuerySet to a list
#             documents_list = list(documents)

#             final_response = {
#                 'documents': documents_list,
#             }

#         except Exception as e:
#             return JsonResponse({"error": f"Error: {str(e)}"}, status=500)

#         return JsonResponse(final_response)
    
#     return JsonResponse({'error': 'Invalid request method'}, status=405)

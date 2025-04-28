import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from core.models import VectorDB

def delete_data(twin_id, asset_id, integration_entity_id):
    """
    Deletes data from the core_vectordb table based on the given twin_id, asset_id, and integration_entity_id.
    """
    try:
        VectorDB.objects.filter(
            twin_id=twin_id,
            asset_id=asset_id,
            integration_entity_id=integration_entity_id
        ).delete()
        print(f"Successfully deleted data from database for twin_id: {twin_id}")
        return {"status": "success", "message": "Data deleted successfully."}
    except Exception as e:
        print(f"Error deleting data from DB for twin_id {twin_id}: {e}")
        return {"status": "error", "message": f"An error occurred: {str(e)}"}
        

@csrf_exempt
def document_delete_api(request):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            asset_id = data.get('asset_id')
            integration_entity_id = data.get('integration_entity_id')
            twin_id = data.get('twin_id')
            
            response = delete_data(twin_id, asset_id, integration_entity_id)
            
            return JsonResponse(response, status=200 if response.get("status") == "success" else 500)

        except Exception as e:
            return JsonResponse({'error': f'An error occurred while deleting data: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method. Use DELETE.'}, status=405)
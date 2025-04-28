from django.views.decorators.csrf import csrf_exempt
import os
import json
import requests
from django.http import JsonResponse
from core.views.document_search_api import generate_embeddings_for_single_text 
from django.http import JsonResponse, FileResponse, HttpResponse
import PyPDF2
from core.models import VectorDB
import numpy as np
import pickle
from django.db import transaction

from pre_processing_pdf import (
    extract_paragraphs_from_pdf,
    chunk_text,
    generate_embeddings
)

def save_document_data(procore_document_path, twin_version_id, json_object, type):
    pdf_path = f'pdf_doc/{procore_document_path}'

    if not os.path.exists(pdf_path):
        return JsonResponse({'msg': f'PDF file not found at path: {pdf_path}'}, status=404)

    try:
        paragraphs = extract_paragraphs_from_pdf(pdf_path)
        if not paragraphs:
            return JsonResponse({'msg': 'No paragraphs extracted from the PDF.'}, status=404)

        paragraph_chunks = []
        for paragraph in paragraphs:
            if paragraph and 'text' in paragraph and paragraph['text']:
                paragraph_chunks.extend(chunk_text(paragraph['text'], json_object))

        if not paragraph_chunks:
            return JsonResponse({'msg': 'No text chunks generated from the paragraphs.'}, status=404)

        embeddings = generate_embeddings(paragraph_chunks)
        if embeddings.shape[0] == 0:
            return JsonResponse({'msg': 'No embeddings were generated for the text chunks.'}, status=404)

        print(embeddings)

        # Save the data to the database
        save_data_to_db(paragraph_chunks, embeddings, procore_document_path, twin_version_id, json_object, type)

        return JsonResponse({'msg': 'Document processed and data saved.'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
 

def delete_document_data(procore_document_path):
    try:
        # Remove the .pdf extension if it exists
        document_name = os.path.splitext(procore_document_path)[0]

        with transaction.atomic():
            rows_to_delete = VectorDB.objects.filter(pdf=document_name.strip())

            if not rows_to_delete.exists():
                return JsonResponse({'msg': f'No data found for document path: {document_name}'}, status=404)

            rows_deleted, _ = rows_to_delete.delete()
            return JsonResponse({'msg': 'Document data deleted successfully.'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
   

def save_data_to_db(paragraph_chunks, embeddings, procore_document_path, twin_version_id, json_object, type):
    pdf_name = os.path.basename(procore_document_path).split(".")[0]
    
    for i, (chunk, embedding) in enumerate(zip(paragraph_chunks, embeddings)):
        page_number = i + 1 
        VectorDB.objects.create(
            page=str(page_number),
            text=chunk,
            pdf=pdf_name,
            embedding=embedding.tolist(),
            twin_id = twin_version_id,
            meta_data = json_object,
            type = type
        )

@csrf_exempt
def document_update_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        procore_document_path = data.get('procore_document_path')
        twin_version_id = data.get('twin_version_id')
        is_attached = data.get('is_attached')
        type = data.get('type')
        equipment_id = data.get('equipment_id')
        equipment_name = data.get('equipment_name')
        equipment_location = data.get('equipment_location')
        document_name = data.get('document_name')
        document_description = data.get('document_description')
        document_type = data.get('document_type')
        sensor_name = data.get('sensor_name')
        
        data_dict = {
          'equipment_id': equipment_id,
          'equipment_name': equipment_name,
          'equipment_location': equipment_location,
          'document_name': document_name,
          'document_description': document_description,
          'document_type': document_type,
          'sensor_name' : sensor_name
        }
        

        if not procore_document_path:
            return JsonResponse({'error': 'Procore document path is required'}, status=400)

        if is_attached == 1:
            return save_document_data(procore_document_path, twin_version_id, data_dict, type)
        
        elif is_attached == 2:
            return delete_document_data(procore_document_path)

        else:
            return JsonResponse({'error': 'Invalid value for is_attached.'}, status=400)
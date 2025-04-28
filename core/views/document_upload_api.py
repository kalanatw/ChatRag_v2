import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from core.models import VectorDB
import uuid
from core.document_loaders import extract_text_from_pdf, extract_text_from_docx, convert_doc_to_pdf, convert_msg_to_pdf, extract_text_from_xlsx

# Load environment variables
load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the .env file")

client = OpenAI(api_key=OPENAI_API_KEY)


output_folder_path = 'J:\\Work\\ursaleo-chat-backend\\ChatRAG\\Documents'

def get_procore_document_meta_data(procore_base_url, file_id, project_id, access_token):
    #Fetches document meta data from Procore API.
    
    url = f"{procore_base_url}/rest/v1.0/files/{file_id}?project_id={project_id}&show_latest_version_only=true"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    # print(url) 

    if response.status_code == 200:
        return response.json() 
    else:
        return {"error": response.status_code, "message": response.text} 
    
def get_rfi_submittal_meta_data(procore_base_url, project_id, file_id, data_type, access_token):
    #Fetches meta data from Procore API for either RFI or Submittal.
    
    if data_type not in ["rfis", "submittals"]:
        return {"error": "Invalid data type. Use 'rfis' or 'submittals'."}
    
    url = f"{procore_base_url}/rest/v1.0/projects/{project_id}/{data_type}/{file_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    # print(response.json()) 

    if response.status_code == 200:
        return response.json()  
    else:
        return {"error": response.status_code, "message": response.text} 
    
def get_document(downloadable_url):
    #Get document contect from procore
    response = requests.get(downloadable_url)
    
    content_disposition = response.headers.get("Content-Disposition", "")
    match = re.search(r'filename="(.+?)"', content_disposition)
    filename = match.group(1) if match else "default_filename.pdf"
    
    output_file_path = os.path.join(output_folder_path, filename)

    try:
            with open(output_file_path, "wb") as file:
                file.write(response.content)

            # Check if the file exists after writing
            if os.path.exists(output_file_path):
                print(f"File '{filename}' successfully written to {output_file_path}.")
                file_written = True
            else:
                print(f"Failed to write the file '{filename}' to {output_file_path}.")
                file_written = False
            
    except Exception as e:
        print(f"An error occurred while writing the file: {e}")
        file_written = False

    # Check if the request was successful
    if response.status_code == 200:
        print("Request was successful!")
        return file_written, output_file_path, filename
    else:
        print(f"Request failed with status code {response.status_code}")
        return False, None, None
        
def chunk_embed(text_content, batch_size=1, max_tokens=8191):
    #Chunk and embed the text content
    for paragraph in text_content:
            paragraph_text = paragraph['text']
            words = paragraph_text.split()
            current_chunk = []
            current_length = 0
            chunks = []
            
            for word in words:
                if current_length + len(word) + 1 > max_tokens:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    current_chunk.append(word)
                    current_length += len(word) + 1

            if current_chunk:
                chunks.append(' '.join(current_chunk))

            for i in range(0, len(chunks), batch_size):

                batch = chunks[i:i + batch_size]
                response = client.embeddings.create(
                    model="text-embedding-ada-002", 
                    input=batch
                )
                
                for chunk, embedding_obj in zip(batch, response.data):
                    if 'embeddings' not in paragraph:
                        paragraph['embeddings'] = []
                    paragraph['embeddings'].append({
                        'chunk': chunk,
                        'embedding': embedding_obj.embedding
                            
                    })
    return text_content

def embed_metadata(content):
    response = client.embeddings.create(
                    model="text-embedding-ada-002", 
                    input=content
                )
    return response.data[0].embedding
    

def save_data_to_db(text_content, twin_id, twin_version_id,meta_data, integration_entity_id, asset_id, filename):
    pdf_id = str(uuid.uuid4())
    type = "document"
    page_number=0
    success = True
    for paragraph in text_content:
        for emb_data in paragraph.get('embeddings', []):
            chunk = emb_data['chunk']
            embedding = emb_data['embedding'] 
            page_number = page_number + 1
            # Save each chunk with its corresponding embedding in the database
            try:
                VectorDB.objects.create(
                    twin_id=twin_id,
                    twin_version_id=twin_version_id,
                    page=page_number, 
                    text=chunk,
                    pdf=filename,
                    embedding=embedding,
                    type = type,
                    meta_data = meta_data,
                    pdf_id = pdf_id,
                    asset_id = asset_id,
                    integration_entity_id = integration_entity_id
                )
            except Exception as e:
                print(f"Error saving data to DB for twin_id {twin_id}: {e}")
                success = False
    if success:
        print(f"Successfully saved data to database for twin_id: {twin_id}")
    return success

def save_metadata_to_db(text_content, embedding, twin_id, twin_version_id,meta_data, integration_entity_id, asset_id, filename):
    pdf_id = str(uuid.uuid4())
    type = "document"
    page_number=1
    success = True
    try:
        VectorDB.objects.create(
                twin_id=twin_id,
                twin_version_id=twin_version_id,
                page=page_number, 
                text=text_content,
                pdf=filename,
                embedding=embedding,
                type = type,
                meta_data = meta_data,
                pdf_id = pdf_id,
                asset_id = asset_id,
                integration_entity_id = integration_entity_id
            )
    except Exception as e:
            success = False
            print(f"Error saving data to DB for twin_id {twin_id}: {e}")
            return {"status": "error", "message": "Error occurred while saving data to the database."}
          
    if success:
        print(f"Successfully saved data to database for twin_id: {twin_id}")
        return {"status": "success", "message": "Data saved successfully."}
    return success

def handle_rfi_submittal_documents(attachment_urls, meta_data, integration_entity_id, asset_id, twin_id, twin_version_id):
    component = meta_data.get("component")
    for url in attachment_urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Successfully retrieved content from: {url}")
                content_disposition = response.headers.get("Content-Disposition", "")
                match = re.search(r'filename="(.+?)"', content_disposition)
                filename = match.group(1) if match else "default_filename.pdf"
    
                output_file_path = os.path.join(output_folder_path, filename)

                try:
                    with open(output_file_path, "wb") as file:
                        file.write(response.content)

                    # Check if the file exists after writing
                    if os.path.exists(output_file_path):
                        print(f"File '{filename}' successfully written to {output_file_path}.")
                        
                        text_content = extract_text_from_pdf(output_file_path, component)
                        embedded_text_content = chunk_embed(text_content)
            
                        save_data_to_db(embedded_text_content, twin_id, twin_version_id, meta_data, integration_entity_id, asset_id, filename)
                        print("Data saved successfully.")
            
                except Exception as e:
                    print(f"An error occurred while writing the file: {e}")
                    return {"status": "error", "message": f"An error occurred while writing the file: {str(e)}"}
            else:
                print(f"Failed to retrieve content from: {url}, Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while fetching {url}: {str(e)}")
            return {"status": "error", "message": f"An error occurred while fetching {url}: {str(e)}"}
            
    return {"status": "success", "message": "Data saved successfully."}
    
       
def handle_documents(procore_base_url, project_id, file_id, meta_data, integration_entity_id, asset_id, twin_id, twin_version_id, access_token):
    try:
        procore_meta_data = get_procore_document_meta_data(procore_base_url, file_id, project_id, access_token)

        file_version = procore_meta_data['file_versions'][0]
        downloadable_url = file_version['prostore_file']['url']

        component = meta_data.get("component")

        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        file_written, file_path, filename = get_document(downloadable_url)
        file_extension = filename.split('.')[-1].lower()
        print(file_extension)

        if file_written:
            if(file_extension=="pdf"):
                text_content = extract_text_from_pdf(file_path, component)
            elif file_extension == 'docx':
                text_content = extract_text_from_docx(file_path, component)
            elif file_extension == 'doc':
                try:
                    output_file = convert_doc_to_pdf(file_path) 
                    print(f"Converted .doc to .docx: {file_path}")
                except Exception as e:
                    print(f"Error converting .doc to .pdf: {e}")
                    text_content = []
                print(f"Extracting text from converted pdf: {output_file}")
                text_content = extract_text_from_pdf(output_file, component)
            elif file_extension == 'pptx':
                try:
                    output_file = convert_pptx_to_pdf(file_path) 
                    print(f"Converted .pptx to .pdf: {file_path}")
                except Exception as e:
                    print(f"Error converting .pptx to .pdf: {e}")
                    text_content = []
                print(f"Extracting text from converted pdf: {output_file}")
                text_content = extract_text_from_pdf(output_file, component)
            elif file_extension == 'xlsx':
                text_content = extract_text_from_xlsx(file_path, component)
            elif file_extension == 'msg':
                try:
                    output_file = convert_msg_to_pdf(file_path) 
                    print(f"Converted .msg to .pdf: {file_path}")
                except Exception as e:
                    print(f"Error converting  .msg to .pdf: {e}")
                    text_content = []
                text_content = extract_text_from_pdf(output_file, component)
                
            embedded_text_content = chunk_embed(text_content)
            
            success = save_data_to_db(embedded_text_content, twin_id, twin_version_id, meta_data, integration_entity_id, asset_id, filename)
            
            if success:
                return {"status": "success", "message": "Data saved successfully."}
            else:
                return {"status": "error", "message": "Error occurred while saving data to the database."}
        else:
            return {"status": "error", "message": "File could not be written."}

    except Exception as e:
        print(f"Error in handle_documents: {e}")
        return {"status": "error", "message": f"An error occurred: {str(e)}"}
    
def handle_rfi_submittals(procore_base_url, project_id, file_id, meta_data, integration_entity_id, asset_id, twin_id, twin_version_id, access_token, document_type):
    if document_type == "RFI":
        rfi_meta_data = get_rfi_submittal_meta_data(procore_base_url, project_id, file_id, "rfis", access_token)
        has_attachment_url = any("url" in attachment for question in rfi_meta_data.get("questions", []) for attachment in question.get("attachments", []))
        
        if(has_attachment_url):
            attachment_urls = [att["url"] for q in rfi_meta_data.get("questions", []) for att in q.get("attachments", []) if "url" in att] + \
                  [att["url"] for q in rfi_meta_data.get("questions", []) for a in q.get("answers", []) for att in a.get("attachments", []) if "url" in att]
            print(attachment_urls)
            
            response = handle_rfi_submittal_documents(attachment_urls, meta_data, integration_entity_id, asset_id, twin_id, twin_version_id)
            return response
        else:
            print("RFI does not contain urls.")
            additional_text = "This RFI belongs to the " + meta_data.get("component") + " component." + "This is the meta data of the RFI." 
            text_content = additional_text + str(rfi_meta_data)
            embedding = embed_metadata(text_content)
            filename = rfi_meta_data.get('subject')  
            response = save_metadata_to_db(text_content, embedding, twin_id, twin_version_id, meta_data, integration_entity_id, asset_id, filename)
            return response
        
    elif document_type == "Submittal":
        submittal_meta_data = get_rfi_submittal_meta_data(procore_base_url, project_id, file_id, "submittals", access_token)
        attachment_urls = [
            attachment["url"]
            for approver in submittal_meta_data.get("approvers", [])
            for attachment in approver.get("attachments", [])
            if "url" in attachment
        ]
        if attachment_urls:
            print("Attached urls", attachment_urls)
            response = handle_rfi_submittal_documents(attachment_urls, meta_data, integration_entity_id, asset_id, twin_id, twin_version_id)
            return response
        else:
            print("Submittal does not contain urls.")
            additional_text = "This Submittal belongs to the " + meta_data.get("component") + " component." + "This is the meta data of the Submittal." 
            text_content = additional_text + str(submittal_meta_data)
            filename = submittal_meta_data.get('title') 
            print(filename)
            embedding = embed_metadata(text_content)
            response = save_metadata_to_db(text_content, embedding, twin_id, twin_version_id, meta_data, integration_entity_id, asset_id, filename)
            return response
    return
    
    
@csrf_exempt
def document_upload_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            access_token = data.get('access_token')
            asset_id = data.get('asset_id')
            document_type = data.get('document_type')
            file_id = data.get('file_id')
            integration_entity_id = data.get('integration_entity_id')
            meta_data = data.get('meta_data')
            procore_base_url = data.get('procore_base_url')
            project_id = data.get('project_id')
            twin_id = data.get('twin_id')
            twin_version_id = data.get('twin_version_id')
            
            response = None
            
            if document_type == "document":
                print("This is a document.")
                response = handle_documents(
                    procore_base_url, project_id, file_id, meta_data, 
                    integration_entity_id, asset_id, twin_id, twin_version_id, access_token
                )
                
            elif document_type == "RFI":
                print("This is a RFI.")
                response = handle_rfi_submittals(
                    procore_base_url, project_id, file_id, meta_data, 
                    integration_entity_id, asset_id, twin_id, twin_version_id, access_token, document_type  
                )
                
            elif document_type == "Submittal":
                print("This is a Submittal.")
                response = handle_rfi_submittals(
                    procore_base_url, project_id, file_id, meta_data, 
                    integration_entity_id, asset_id, twin_id, twin_version_id, access_token, document_type
                )
            
            # If response is None, return an error
            if response is None:
                return JsonResponse({'error': 'Invalid document type or processing failed.'}, status=400)
            
            return JsonResponse(response, status=200 if response.get("status") == "success" else 500)

        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)
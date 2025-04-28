"""
This script is designed to implement a Retrieval-Augmented Generation (RAG) chatbot using OpenAI's GPT-4 model. 
The chatbot processes user queries, retrieves relevant information from a vector database, and generates accurate and concise responses. 
The main functionalities include generating embeddings for text, searching for relevant text chunks in an external vector database, 
and constructing an OpenAI prompt to generate the final response.

Authors: Chethiya Galkaduwa/ Kalana
"""
import json
import os
import numpy as np
import requests
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from openai import OpenAI
import tiktoken
import openai
from core.models import ChatHistory, ChatInstance
import re
from memory_manager import save_and_limit_chat_history, get_memory
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.serializer import OpenAIResponseSerializer
from ChatRAG.prompt_templates import get_prompt_template

from datetime import datetime

def print_timestamp():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current timestamp: {formatted_time}")


load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env file")

openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

chat_history = {} 
chat_history_with_response = {}
MAX_HISTORY_LENGTH = 1  

        
with open('meta_data_attributes.json', 'r') as f:
    metadata_attributes = json.load(f)

# Function to generate embedding for a single text input
def generate_embeddings_for_single_text(text, model="text-embedding-3-small"):
    response = client.embeddings.create(
        model=model, 
        input=text
    )
    return np.array(response.data[0].embedding)

    
# Function to search query in the external database
def search_query(query_vector, top_k, query,twin_version_id, metadata):
    
    # print("Querying the external vector database")

    url = "http://127.0.0.1:8201/search_document/VectorDB"

    
    payload = {"query_vector": query_vector.tolist(), "top_k": top_k, "query": query, "twin_version_id": twin_version_id, "meta_data": metadata }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()['results']
    else:
        raise ValueError("Error querying the external vector database")


def find_similar_previous_query(query, chat_instance_id):
    """
    Find similar previous queries and their markdown responses from the chat history
    Returns: tuple (bool, str) - (found, markdown_response)
    """
    try:
        # Get previous chats for this instance with exact query match
        previous_chat = ChatHistory.objects.filter(
            chat_instance_id=chat_instance_id,
            user_query__iexact=query  # Case-insensitive exact match
        ).order_by('-id').first()
        print("Previous chat found:", previous_chat)
        
        if previous_chat:
            return True, previous_chat.chatbot_response
        return False, None
        
    except Exception as e:
        print(f"Error checking similar queries: {e}")
        return False, None


def construct_openai_prompt(query, final_results, twin_version_id="default",chat_instance_id=None):
    """
    Constructs the OpenAI prompt using templates based on twin_version_id.
    Args:
        query (str): The user's query
        final_results (list): Retrieved chunks from vector database
        twin_version_id (str): ID of the twin version to determine prompt template
    """
    # Get the appropriate template based on twin ID
    ##have a dictionary here so it will know to run find_similar_previous_query
    ##if have a similar query send everything to construct the promt. ask to using the old response structure recustruct it using the new
    #print("Chat instance ID:", chat_instance_id)
    similar_response = None
    # Only check for similar query for the special twin id
    if twin_version_id == "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455" and chat_instance_id:
        found, prev_response = find_similar_previous_query(query, chat_instance_id)
        if found:
            similar_response = prev_response
    prompt = get_prompt_template(twin_version_id,query,similar_response).copy()
    
    #print("Prompt template:", prompt)
    
    # Format the query into the template
    for item in prompt:
        if isinstance(item["content"], str):
            item["content"] = item["content"].format(query=f"This is the query done by the user: {query}")
    
    # Add the retrieved chunks as context
    for i, result in enumerate(final_results):
        text = result["text"]
        document_name = result["pdf"]
        prompt.append({"role": "user", "content": f"Context {i + 1}: {text} | Document: {document_name}"})
    
    return prompt

def construct_openai_prompt_follow_up_query(chat_instance_id, query, final_results):
    memory = get_memory( chat_instance_id)
    chat_history = memory.load_memory_variables({})["chat_history"]
     
    prompt = [
     {"role": "system", "content": "This is a RAG chatbot using OpenAI to generate responses."},
     {"role": "system", "content": f"Here is the most recent conversation history for your reference.{chat_history}"},
     {"role": "system", "content": f"This is the current user query: {query}"},
     {"role": "system", "content": "In relation to the chat history, these are text chunks retrieved from the in-house Vector database:"},
     {"role": "system", "content": "Generate a concise, accurate and complete response to the user query based on the following chunks. You Must Refer the chat history for getting the contextual understanding of the user query. Refer the metadata for further information. Reference the document knowledge or your own knowledge as needed. If the chat history is about troubleshooting, You MUST provide step by step troubleshooting guide in short. Dont use sensor data, when providing the answeres. If no relevant chunk is found, inform the user that there is no relevant information available for this question. Ensure the response is readable and appropriate for the end user. DO NOT MENTION the methodology or USING words like 'chunks', 'Chunk' or providing explanations. Any numeric value that you provide, round it off to a maximum of two decimals. You must not return any PAGE BREAK signs in the response. Ensure the response is based on the retrieved text and always mention the document it comes from as \"REFERENCES\" within brackets using the document_name from the metadata of each chunk. Only add the documents which you used to generate the answer. You MUST restrict the answer to 10-15 words."}
    ]
    
    for i, result in enumerate(final_results):
      text = result["text"]
      document_name = result["pdf"]
      prompt.append({"role": "user", "content": f"Chunk {i + 1}: {text} | Document Name: {document_name}"})
    
    return prompt


def construct_openai_prompt_for_meta_data(twin_version_id, chat_instance_id, query):
    memory = get_memory( chat_instance_id)
    chat_history = memory.load_memory_variables({})["chat_history"]
    
    prompt = [
        {"role": "system", "content": "This is a RAG chatbot using OpenAI to generate responses."},
        {"role": "system", "content": f"This is the current query done by the user: {query}"},
        {"role": "system", "content": f"Here is the most recent conversation history for your reference: {chat_history}"},
        {"role": "system", "content": "You dont need to provide answer for the user query. But instead extract the following metadata from the provided current user query. Provide the response in a JSON Object."},
         {"role": "system", "content": (
            "Here is a sample metadata JSON for your reference. Follow this structure when extracting metadata:\n"
            "{\n"
            '    "document_type": null,\n'
            '    "manager": null,\n'
            '    "issue_date": null,\n'
            '    "status": null\n'
            "}"
        )}
    ]
    
    for twin_version in metadata_attributes["twin_versions"]:
        if twin_version["twin_version_id"] == twin_version_id:
            for attribute in twin_version["attributes"]:
                meta_data_format = attribute["meta_data_format"]
                meta_data_format_prompt = attribute["meta_data_format_prompt"]
                prompt.append({
                    "role": "system",
                    "content": f"{meta_data_format_prompt}: {meta_data_format}"
                })
            break 

    prompt.append({"role": "system", "content": "Within the resposne JSON object, Just provide the meta data attibute and the value for it only.Do not add additional details like enum, examples etc. If any of these metadata fields are not found, return null for those fields. If you can not find any meta data in the user query, just provide a null json object. The property names must be enclosed in double quotes."})

    return prompt


def meta_data_extraction(twin_version_id, chat_instance_id, query):
    openai_prompt =  construct_openai_prompt_for_meta_data(twin_version_id, chat_instance_id, query)
    completion = client.chat.completions.create(model="gpt-4o-mini",temperature=1, messages=openai_prompt)
    response_text  = completion.choices[0].message.content
    
    print("Meta data extracted.", response_text)
    print_timestamp()
    
    # Extract JSON part from the response text
    metadata = re.search(r'\{.*\}', response_text, re.DOTALL).group()
    
    return metadata


def num_tokens_from_messages(messages, model="gpt-4o-mini"):
    """Return a list of dictionaries with message index and token count for each message."""
    encoding = tiktoken.encoding_for_model(model)
    tokens_per_message = 9
    tokens_per_name = 1

    token_counts = [] 
    total_tokens = 0

    for i, message in enumerate(messages):
        num_tokens = tokens_per_message  
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
        
        # Append a dictionary with message index and token count
        token_counts.append({"message_index": i, "token_count": num_tokens})
        total_tokens += num_tokens

    return token_counts, total_tokens

def is_follow_up_query(query,  chat_instance_id):
    memory = get_memory(chat_instance_id) 
    chat_history = memory.load_memory_variables({})["chat_history"]
    
    # Determine if the query is a follow-up
    if len(chat_history) > 0 and ("yes" in query.lower() or "no" in query.lower() or len(query.split()) <= 3):
        return True
    return False

def get_valid_prompt(twin_version_id, query, query_vector, chat_instance_id, model="gpt-4o-mini", max_tokens=8191):
    #print("Chat instance ID get_valid_prompt:", chat_instance_id)
    top_k = 12

    # Check if the query is a follow-up query
    follow_up_query = is_follow_up_query(query, chat_instance_id)

    if follow_up_query:
        print("This is a follow-up query.")
        # if chat_instance_id in chat_history:
        memory = get_memory(chat_instance_id) 
        chat_history = memory.load_memory_variables({})["chat_history"]

        user_queries = [line[6:] for line in chat_history.splitlines() if line.startswith("Human:")]

        last_query = user_queries[-1] if user_queries else None
        
        metadata_json = meta_data_extraction(twin_version_id, chat_instance_id, last_query)
            
        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in metadata: {e}")
          
        filtered_metadata = {key: value for key, value in metadata.items() if value is not None}
        results = search_query(query_vector, top_k, last_query, twin_version_id, filtered_metadata)

        print("Creating the final prompt")

        # Construct the initial prompt
        initial_prompt = construct_openai_prompt_follow_up_query(chat_instance_id, query, results)

        token_counts, total_tokens = num_tokens_from_messages(initial_prompt, model)
            
        while total_tokens > max_tokens and results:
            token_counts.pop()
            results.pop()
            print(total_tokens)
            total_tokens = sum(item["token_count"] for item in token_counts)

        openai_prompt = construct_openai_prompt_follow_up_query(chat_instance_id, query, results)

        if total_tokens > max_tokens:
            raise ValueError("Cannot fit the prompt within the token limit with the given results.")

        return openai_prompt
      
            
    else:
        print("This is a new query. Proceeding with metadata extraction.")

        metadata_json = meta_data_extraction(twin_version_id,chat_instance_id, query)

        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in metadata: {e}")

        filtered_metadata = {key: value for key, value in metadata.items() if value is not None}

        results = search_query(query_vector, top_k, query, twin_version_id, filtered_metadata)

        print("Creating the final prompt")
        
        # Pass twin_version_id to construct_openai_prompt
        initial_prompt = construct_openai_prompt(query, results, twin_version_id,chat_instance_id)

        token_counts, total_tokens = num_tokens_from_messages(initial_prompt, model)

        while total_tokens > max_tokens and results:
            token_counts.pop()
            results.pop()
            total_tokens = sum(item["token_count"] for item in token_counts)

        # Pass twin_version_id here as well
        openai_prompt = construct_openai_prompt(query, results, twin_version_id,chat_instance_id)

        if total_tokens > max_tokens:
            raise ValueError("Cannot fit the prompt within the token limit with the given results.")

        return openai_prompt

def save_chat_history_to_db(user_query, chatbot_response, twin_version_id, chat_instance_id):
    chat_instance = ChatInstance.objects.get(id=chat_instance_id)

    ChatHistory.objects.create(
        chat_instance=chat_instance, 
        twin_id=twin_version_id,  
        user_query=user_query,
        chatbot_response=chatbot_response
    )

@extend_schema(
    summary="Document Response API",
    description=(
        "This endpoint accepts a user query regarding a specific twin scenario and "
        "returns a comprehensive response based on the query. The system generates "
        "embeddings for the user query and retrieves relevant document chunks from the vectore store. Then it sends user query and retrieved document chunks"
        "to the OpenAI GPT-4 model to generate a complete answer."
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
def document_response_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query')
            twin_version_id = data.get('twin_version_id')
            chat_instance_id = data.get('chat_instance_id')
            print("Received request with query:", query)
            
            print_timestamp()

            if not query:
                return JsonResponse({'error': 'Query is required'}, status=400)
            
            query_vector = generate_embeddings_for_single_text(query)
   
            valid_prompt = get_valid_prompt(twin_version_id, query, query_vector,  chat_instance_id)
            
            print("Got prompt. Sending to chatgpt")
            print_timestamp()

            completion = client.chat.completions.create(model="gpt-4o-mini",temperature=1, messages=valid_prompt)
            response_message = completion.choices[0].message
            print(response_message)
            print_timestamp()
            
            save_and_limit_chat_history(chat_instance_id, query, response_message.content)
            
            save_chat_history_to_db(query, response_message.content, twin_version_id, chat_instance_id)
            
            openai_response = {
            "content": response_message.content,
            }
            
        except Exception as e:
            return JsonResponse(
                {"error": f"Error : {str(e)}"},
                status=500,
            )
            
        final_response = {
            "openai_response": openai_response,
        }
        
    return JsonResponse(final_response)


import fitz  # PyMuPDF
import json
import os
import numpy as np
import faiss
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken


load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env file")

client = OpenAI(api_key=OPENAI_API_KEY)


# Load the FAISS index and text chunks
index = faiss.read_index("ChatRAG/faiss_doc/faiss_index.bin")

# Function to generate embedding for a single text input
def generate_embeddings_for_single_text(text, model="text-embedding-3-small"):
    response = client.embeddings.create(
        model=model, 
        input=text
    )
    return np.array(response.data[0].embedding)

# Load paragraph chunks and embeddings
json_file = "ChatRAG/paragraph_chunks.json"

with open(json_file, 'r') as f:
    data = json.load(f)
    all_paragraph_chunks = data['paragraph_chunks']
    embeddings = np.array(data['embeddings'])

# Function to search query in the FAISS index
def search_query(query, index, chunks, top_k=20):
    query_vector = generate_embeddings_for_single_text(query)
    D, I = index.search(query_vector.reshape(1, -1), top_k)
    results = []
    for i in range(min(top_k, len(I[0]))):  # Ensure we don't go out of bounds
        chunk_index = I[0][i]
        if chunk_index < len(chunks):  # Ensure valid index
            results.append(chunks[chunk_index])
    return results

# Example query
query = "Is the butterfly valve still exempt in 2023?"
results = search_query(query, index, all_paragraph_chunks)

def construct_openai_prompt(query, top_k_texts):
    prompt = [
        {"role": "system", "content": "This is a RAG chatbot using OpenAI to generate responses."},
        {"role": "system", "content": f"This is the query done by the user: {query}"},
        {"role": "system", "content": "In relation to the user query, these are text chunks retrieved from the in-house Vector database:"}
    ]
    prompt.extend({"role": "user", "content": f"Chunk {i + 1}: {text}"} for i, text in enumerate(top_k_texts))
    prompt.append({"role": "system", "content": "Generate a concise and accurate response to the user query based on the provided information. Reference the document knowledge or your own knowledge as needed. Ensure the response is readable and appropriate for the end user. Avoid mentioning the methodology or using words like 'chunks' or providing explanations."})
    return prompt

# Function to count tokens in the prompt
def num_tokens_from_messages(messages, model="gpt-4-0613"):
    """Return the number of tokens used by a list of messages."""
    encoding = tiktoken.encoding_for_model(model)
    tokens_per_message = 3
    tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  
    return num_tokens

# funtion to Adjust top_k until the prompt is within the token limit
def get_valid_prompt(query, index, chunks, max_tokens=8191, model="gpt-4-0613"):
    top_k = 20
    while top_k > 0:
        results = search_query(query, index, chunks, top_k)
        openai_prompt = construct_openai_prompt(query, results)
        num_tokens = num_tokens_from_messages(openai_prompt, model)
        if num_tokens <= max_tokens:
            return openai_prompt, num_tokens
        top_k -= 1
    raise ValueError("Cannot fit the prompt within the token limit even with top_k = 1")

# Get a valid prompt within the token limit
try:
    valid_prompt, token_count = get_valid_prompt(query, index, all_paragraph_chunks)
except ValueError as e:
    print(e)

completion = client.chat.completions.create(model="gpt-4",temperature=0, messages=valid_prompt)
response_message = completion.choices[0].message
print(response_message.content)

    

    







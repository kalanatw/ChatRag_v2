"""
This script processes PDF files from a specified directory by extracting paragraphs of text,
generating embeddings for the text chunks using OpenAI's API, and saving the results to a JSON file.
The script handles chunking of large texts to fit within token limits and can also load and update
existing JSON data with new paragraph chunks and their corresponding embeddings.


BEFORE RUNNING THIS CODE SPECIFY THE NECESSARY PDF DIRECTORY.
SCRIPT WILL CREATE IF A NEW JSON NAME IS PROVIDED UPDATE IF EXSITING NAME IS PROVIDED.

Author: Chethiya Galkaduwa
"""

import fitz  # PyMuPDF
import json
import os
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the .env file")

client = OpenAI(api_key=OPENAI_API_KEY)

# Constants for directories and file paths
PDF_DIRECTORY = "pdf_doc_1"  # Specify the PDF directory
JSON_FILE = "paragraph_chunks_toweronly.json"

# Function to list all PDF files in the directory
def list_pdf_files(directory):
    """List all PDF files in the given directory."""
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.pdf')]

# Function to extract paragraphs from each page of the PDF
def extract_paragraphs_from_pdf(pdf_path, pages_per_chunk=1):
    """Extract paragraphs from each page of the PDF and group them into chunks."""
    doc = fitz.open(pdf_path)
    paragraphs = []
    all_text = ""
    page_count = len(doc)
    
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text.strip():
            all_text += text + "\n\n"
        
        # Add paragraphs to the list after reaching the chunk size or at the last page
        if (page_num + 1) % pages_per_chunk == 0 or page_num == page_count - 1:
            paragraphs.append({
                'pages': list(range(page_num - pages_per_chunk + 2, page_num + 2)),
                'text': all_text.strip(),
                'pdf': os.path.basename(pdf_path)
            })
            all_text = ""
    
    return paragraphs

# Function to chunk text into smaller pieces based on token limits
def chunk_text(text, json_object, max_tokens=8192):
    """Split text into smaller chunks based on the max token limit."""
    if not text:
        return []
    
    ##
    json_str = ' '.join([f'{key}: {value}' for key, value in json_object.items()])
    ##
    words = text.split()
    current_chunk = []
    current_length = 0
    chunks = []
    
    for word in words:
        if current_length + len(word) + 1 > max_tokens:
            ##
            chunk_with_info = ' '.join(current_chunk) + ' ' + json_str
            chunks.append(' '.join(chunk_with_info))
            ##
            # chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

# Function to load existing JSON data
def load_existing_data(json_file):
    """Load existing JSON data if available."""
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            existing_data = json.load(f)
        existing_paragraph_chunks = existing_data['paragraph_chunks']
        existing_embeddings = np.array(existing_data['embeddings'])
    else:
        existing_paragraph_chunks = []
        existing_embeddings = np.array([])

    return existing_paragraph_chunks, existing_embeddings

# Function to generate embeddings for text chunks in batches
def generate_embeddings(texts, batch_size=1):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        response = client.embeddings.create(
            model="text-embedding-3-small", 
            input=batch
        )
        # Access the embeddings using dot notation
        for data in response.data:
            embeddings.append(data.embedding)
    return np.array(embeddings)

# Function to save updated JSON data
def save_updated_data(paragraph_chunks, embeddings, json_file):
    """Save the updated paragraph chunks and embeddings to JSON."""
    data = {
        'paragraph_chunks': paragraph_chunks,
        'embeddings': embeddings.tolist()
    }
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)

# Main script execution
def main():
    # List PDF files in the directory
    pdf_files = list_pdf_files(PDF_DIRECTORY)
    if not pdf_files:
        print("No PDF files found in the directory. Exiting...")
        return

    print("PDF files found in the directory:")
    for pdf_file in pdf_files:
        print(pdf_file)

    # Load existing JSON data
    existing_paragraph_chunks, existing_embeddings = load_existing_data(JSON_FILE)

    # Extract paragraphs from all new PDFs
    new_paragraph_chunks = []
    for pdf_file in pdf_files:
        new_paragraph_chunks.extend(extract_paragraphs_from_pdf(pdf_file))

    #Chunk the extracted text if necessary
    # split_texts = []
    # for chunk in new_paragraph_chunks:
    #     split_texts.extend(chunk_text(chunk['text']))

    # print(f"Number of new text chunks to be embedded: {len(split_texts)}")

    # # Generate embeddings for the new text chunks
    # new_embeddings = generate_embeddings(split_texts)

    # Validate embedding generation
    # if new_embeddings.shape[0] == 0:
    #     raise ValueError("No embeddings were generated.")

    # # Combine existing and new embeddings
    # if existing_embeddings.size > 0:
    #     combined_embeddings = np.vstack((existing_embeddings, new_embeddings))
    # else:
    #     combined_embeddings = new_embeddings

    # Update paragraph chunks with new data
    # existing_paragraph_chunks.extend(new_paragraph_chunks)

    # # Save the updated JSON file
    # save_updated_data(existing_paragraph_chunks, combined_embeddings, JSON_FILE)

    print("JSON file updated successfully.")

if __name__ == "__main__":
    main()

"""
This script sets up a FastAPI application to provide an endpoint for vector-based search using FAISS 
and reranking using a cross-encoder. The app integrates with a Django backend to fetch text chunks 
from a database and utilizes an external reranker for better search results. 

Author: Chethiya Galkaduwa
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss, os, django
import numpy as np
from asgiref.sync import sync_to_async

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatRAG.settings')
django.setup()

from core.models import Documentdb
from rerankers import Reranker

# FastAPI app setup
app = FastAPI()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Initialize reranker
ranker = Reranker("cross-encoder")

# Load FAISS index
try:
    index = faiss.read_index("faiss_doc/document_faiss_index.bin")
except Exception as e:
    raise Exception(f"Error loading FAISS index: {e}")

# Define request model
class SearchRequest(BaseModel):
    query_vector: list[float]
    top_k: int
    query: str

@app.post("/search_document/")
async def search_vectors(request: SearchRequest):
    query_vector = np.array(request.query_vector, dtype='float32').reshape(1, -1)
    
    try:
        D, I = index.search(query_vector, request.top_k)
        print(I)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during FAISS search: {e}")

    results = []
    for i in range(min(request.top_k, len(I[0]))):
        chunk_index = I[0][i]
        try:
            chunk = await sync_to_async(Documentdb.objects.get)(id=chunk_index + 1)
            results.append({
                "page": chunk.page,
                "text": chunk.text,
                "pdf": chunk.pdf
            })
        except Documentdb.DoesNotExist:
            continue

    docs = [result["text"] for result in results]
    
    try:
        reranked_results = ranker.rank(query=request.query, docs=docs)
        final_results = [{"text": item.document.text} for item in reranked_results.results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during reranking: {e}")

    return {"results": final_results}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8080)
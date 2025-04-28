from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import numpy as np
import os
import sys
import django
from asgiref.sync import sync_to_async

# Add the project directory to the Python path
sys.path.append('/Users/chey/NeedToFinish/RAG_chat/ChatRAG')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ChatRAG.settings")

django.setup()

from core.models import ParagraphChunk

app = FastAPI()

try:
    index = faiss.read_index("faiss_doc/faiss-index.bin")
except Exception as e:
    raise Exception(f"Error loading FAISS index: {e}")

class SearchRequest(BaseModel):
    query_vector: list[float]
    top_k: int

@app.post("/search/")
async def search_vectors(request: SearchRequest):
    try:
        query_vector = np.array(request.query_vector, dtype='float32').reshape(1, -1)
        D, I = index.search(query_vector, request.top_k)

        print(f"FAISS Distances: {D}")
        print(f"FAISS Indices: {I}")

        # Retrieve all relevant ParagraphChunks in one query
        chunk_indices = I[0][:request.top_k]
        print(f"Chunk Indices: {chunk_indices}")

        # Ensure all chunk indices are positive and non-zero
        valid_chunk_indices = [idx for idx in chunk_indices if idx > 0]
        print(f"Valid Chunk Indices: {valid_chunk_indices}")

        paragraph_chunks = await sync_to_async(list)(ParagraphChunk.objects.filter(id__in=valid_chunk_indices))

        # Create a dictionary for quick lookup
        chunk_dict = {chunk.id: chunk for chunk in paragraph_chunks}

        results = []
        for idx in valid_chunk_indices:
            chunk = chunk_dict.get(idx)
            if chunk:
                results.append({
                    "page": chunk.page,
                    "text": chunk.text,
                    "pdf": chunk.pdf
                })
            else:
                print(f"No ParagraphChunk found for index: {idx}")

        return {"distances": D.tolist(), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

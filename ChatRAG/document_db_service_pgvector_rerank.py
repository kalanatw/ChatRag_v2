"""
This FastAPI application provides an API endpoint for performing vector similarity searches 
on a dynamically specified Django model (database) using pgvector. The search results are 
then reranked using a cross-encoder model to improve relevance. The application supports 
requests where a vector query is matched against stored vectors, and the top-k most similar 
results are returned after reranking. Django ORM is used for database interactions, and the 
search is conducted asynchronously to improve performance.

Authors: Chethiya Galkaduwa/ Kalana
"""

import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, django
from asgiref.sync import sync_to_async
from pgvector.django import CosineDistance
from django.db.models import Q
from typing import List, Dict, Any
from django.db.models import Q
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from core.models import VectorDB
from rerankers import Reranker
from typing import Optional
from django.contrib.postgres.search import SearchVector, SearchRank 
import cohere

def print_timestamp():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current timestamp: {formatted_time}")

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatRAG.settings')
django.setup()

# FastAPI app setup
app = FastAPI()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

cohere_api_key = os.getenv("COHERE_API_KEY")
co = cohere.Client(cohere_api_key)

# Define request model
class SearchRequest(BaseModel):
    query_vector: list[float]
    top_k: int
    query: str
    twin_version_id: str
    meta_data: Dict[str, Any] 
    

async def perform_hybrid_search(db_name, query_vector, top_k, query, twin_version_id, meta_data):
    print("Starting hybrid search...")
    print_timestamp()

    try:
        # Initialize metadata filter
        metadata_filters = Q()
        if meta_data:
            for key, value in meta_data.items():
                if value is not None:
                    metadata_filters &= Q(**{f'meta_data__{key}__icontains': value})

        # Perform filtering first
        filtered_results = await sync_to_async(list)(
            db_name.objects.filter(twin_version_id=twin_version_id).filter(metadata_filters)
        ) or []

        if filtered_results:
            print("Starting keyword search and vector search...")
            # Perform BM25 Keyword Search and Vector Search in the same block
            filtered_ids = [r.id for r in filtered_results]

            keyword_results, vector_results = await asyncio.gather(
                sync_to_async(list)(
                    db_name.objects.filter(id__in=filtered_ids)
                    .annotate(rank=SearchRank(SearchVector("text"), query))
                    .order_by("-rank")[:top_k]
                ),
                sync_to_async(list)(
                    db_name.objects.filter(id__in=filtered_ids)
                    .annotate(distance=CosineDistance("embedding", query_vector))
                    .order_by("distance")[:top_k]
                )
            )

        else:
            print("No search results found.")
            final_results = []
            return final_results
        
        print_timestamp()

        # Merge results properly
        combined_results = {}

        # Add BM25 results
        for result in keyword_results:
            combined_results[result.id] = {
                "result": result,
                "bm25_score": result.rank,  # BM25 Score
                "vector_score": 0  # Default Vector Score
            }

        # Add Vector results
        for result in vector_results:
            if result.id in combined_results:
                combined_results[result.id]["vector_score"] = 1 - result.distance  # Convert distance to similarity
            else:
                combined_results[result.id] = {
                    "result": result,
                    "bm25_score": 0,  # Default BM25 Score
                    "vector_score": 1 - result.distance
                }
                
        # Normalize Scores
        max_bm25 = max(max((r["bm25_score"] for r in combined_results.values()), default=1), 1)
        max_vector = max(max((r["vector_score"] for r in combined_results.values()), default=1), 1)
        
        print(f"max_bm25: {max_bm25}, max_vector: {max_vector}")
        
        for res in combined_results.values():
            res["bm25_score"] /= max_bm25
            res["vector_score"] /= max_vector
        
        # Hybrid Scoring (Weighted Sum)
        weight_bm25 = 0.5
        weight_vector = 0.5

        for res in combined_results.values():
            res["hybrid_score"] = (weight_bm25 * res["bm25_score"]) + (weight_vector * res["vector_score"])

        # Sort by Hybrid Score
        sorted_results = sorted(combined_results.values(), key=lambda x: x["hybrid_score"], reverse=True)
        sorted_results = [res["result"] for res in sorted_results]

        # Cohere Reranking
        print("Starting Cohere reranking...")
        print_timestamp()
        
        # Prepare documents for reranking
        documents = [result.text for result in sorted_results]

        # Call Cohere's Rerank API
        response = co.rerank(
            model='rerank-v3.5',
            query=query,
            documents=documents,
            top_n=len(documents)
        )
        
        # Process reranked results
        reranked_results = [sorted_results[result.index] for result in response.results]

        # Final formatted results
        final_results = [{"text": result.text, "pdf": result.pdf} for result in reranked_results]

        print("Hybrid search and reranking complete.")
        return final_results

    except Exception as e:
        print(f"Error during hybrid search: {e}")
        raise HTTPException(status_code=500, detail=f"Error during hybrid search: {e}")

#API endpoint that uses the reusable function
@app.post("/search_document/{model_name}")
async def search_vectors(model_name: str, request: SearchRequest):
    db_model = globals().get(model_name)
    if not db_model:
        raise HTTPException(status_code=400, detail=f"Database model {model_name} not found")
    final_results = await perform_hybrid_search(db_model, request.query_vector, request.top_k, request.query, request.twin_version_id, request.meta_data)
    return {"results": final_results}

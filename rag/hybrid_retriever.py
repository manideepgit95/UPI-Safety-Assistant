import json
import time
import faiss
import numpy as np
from pathlib import Path
from rank_bm25 import BM25Okapi


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# Correct location of the knowledge base
KNOWLEDGE_BASE_PATH = (
    BASE_DIR / "data" / "processed" / "knowledge_base.json"
)

# Existing FAISS index location
FAISS_INDEX_PATH = BASE_DIR / "data" / "faiss.index"


# ---------------------------------------------------------
# Load knowledge base
# ---------------------------------------------------------

def load_knowledge_base():
    """
    Load the processed UPI safety knowledge base.
    """

    if not KNOWLEDGE_BASE_PATH.exists():
        raise FileNotFoundError(
            f"Knowledge base not found: {KNOWLEDGE_BASE_PATH}"
        )

    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# Load FAISS index
# ---------------------------------------------------------

def load_faiss_index():
    """
    Load the existing FAISS index.

    This function is kept for compatibility with the project,
    although the lightweight retrieval below does not require
    the embedding model.
    """

    if not FAISS_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {FAISS_INDEX_PATH}"
        )

    return faiss.read_index(str(FAISS_INDEX_PATH))


# ---------------------------------------------------------
# Simple BM25 keyword search
# ---------------------------------------------------------

def keyword_search(query, chunks, top_k=5):
    """
    Perform lightweight BM25 keyword-based retrieval.

    This replaces the SentenceTransformer semantic search
    so the application uses much less memory on Render.
    """

    documents = [
        chunk.get("content", "")
        for chunk in chunks
    ]

    tokenized_documents = [
        document.lower().split()
        for document in documents
    ]

    bm25 = BM25Okapi(tokenized_documents)

    query_tokens = query.lower().split()

    scores = bm25.get_scores(query_tokens)

    ranked_indices = np.argsort(scores)[::-1][:top_k]

    results = []

    for index in ranked_indices:
        results.append(
            {
                "chunk": chunks[index],
                "keyword_score": float(scores[index]),
            }
        )

    return results


# ---------------------------------------------------------
# Lightweight hybrid search
# ---------------------------------------------------------

def hybrid_search(query, top_k=5):
    """
    Retrieve the most relevant knowledge-base chunks.

    The original system used:
        SentenceTransformer
        FAISS semantic search
        BM25
        CrossEncoder reranking

    The lightweight deployment version uses BM25 only
    to reduce memory usage on the free Render instance.
    """

    start_time = time.perf_counter()

    # Load knowledge base
    chunks = load_knowledge_base()

    # Perform keyword retrieval
    keyword_results = keyword_search(
        query,
        chunks,
        top_k=top_k
    )

    # Convert results to the format expected by
    # rag_pipeline.py and reranker.py
    results = []

    for result in keyword_results:
        results.append(
            {
                "chunk": result["chunk"],
                "hybrid_score": result["keyword_score"],
            }
        )

    # Sort by score
    results.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True
    )

    elapsed = time.perf_counter() - start_time

    print(
        f"Hybrid search completed in {elapsed:.3f} seconds"
    )

    return results[:top_k]
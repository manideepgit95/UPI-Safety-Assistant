import json
import time
from pathlib import Path

import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INDEX_FILE = BASE_DIR / "data" / "processed" / "faiss.index"
KNOWLEDGE_BASE = BASE_DIR / "data" / "processed" / "knowledge_base.json"

MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# LAZY MODEL LOADING
# ============================================================

EMBEDDING_MODEL = None


def get_embedding_model():
    """
    Load the embedding model only when it is actually needed.

    This prevents the model from consuming memory during
    FastAPI startup.
    """

    global EMBEDDING_MODEL

    if EMBEDDING_MODEL is None:

        print(f"\nLoading embedding model: {MODEL_NAME}")

        model_start = time.perf_counter()

        EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)

        model_load_time = time.perf_counter() - model_start

        print(
            f"Embedding model loaded in: "
            f"{model_load_time:.2f} seconds"
        )

    return EMBEDDING_MODEL


# ============================================================
# LOAD KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():

    with KNOWLEDGE_BASE.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# BUILD BM25
# ============================================================

def build_bm25(chunks):

    documents = [
        chunk["content"].lower().split()
        for chunk in chunks
    ]

    return BM25Okapi(documents)


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def semantic_search(
    query,
    chunks,
    model,
    index,
    top_k=5
):

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    scores, indices = index.search(
        query_embedding.astype("float32"),
        top_k
    )

    results = []

    for score, index_id in zip(
        scores[0],
        indices[0]
    ):

        results.append(
            {
                "chunk": chunks[index_id],
                "score": float(score)
            }
        )

    return results


# ============================================================
# KEYWORD SEARCH
# ============================================================

def keyword_search(
    query,
    chunks,
    bm25,
    top_k=5
):

    query_tokens = query.lower().split()

    scores = bm25.get_scores(query_tokens)

    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]

    results = []

    for index_id in top_indices:

        results.append(
            {
                "chunk": chunks[index_id],
                "score": float(scores[index_id])
            }
        )

    return results


# ============================================================
# HYBRID SEARCH
# ============================================================

def hybrid_search(
    query,
    top_k=5
):

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # Load knowledge base
    # --------------------------------------------------------

    chunks = load_knowledge_base()

    knowledge_base_time = (
        time.perf_counter() - start_time
    )

    print(
        f"Knowledge base load time: "
        f"{knowledge_base_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # Load FAISS index
    # --------------------------------------------------------

    index_start = time.perf_counter()

    index = faiss.read_index(
        str(INDEX_FILE)
    )

    index_load_time = (
        time.perf_counter() - index_start
    )

    print(
        f"FAISS index load time: "
        f"{index_load_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # Build BM25
    # --------------------------------------------------------

    bm25_start = time.perf_counter()

    bm25 = build_bm25(chunks)

    bm25_build_time = (
        time.perf_counter() - bm25_start
    )

    print(
        f"BM25 build time: "
        f"{bm25_build_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # Get embedding model
    # --------------------------------------------------------

    embedding_model = get_embedding_model()


    # --------------------------------------------------------
    # Semantic search
    # --------------------------------------------------------

    semantic_start = time.perf_counter()

    semantic_results = semantic_search(
        query,
        chunks,
        embedding_model,
        index,
        top_k
    )

    semantic_time = (
        time.perf_counter() - semantic_start
    )

    print(
        f"Semantic search time: "
        f"{semantic_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # Keyword search
    # --------------------------------------------------------

    keyword_start = time.perf_counter()

    keyword_results = keyword_search(
        query,
        chunks,
        bm25,
        top_k
    )

    keyword_time = (
        time.perf_counter() - keyword_start
    )

    print(
        f"Keyword search time: "
        f"{keyword_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # Combine results
    # --------------------------------------------------------

    combined = {}

    for result in semantic_results:

        chunk_id = result["chunk"]["chunk_id"]

        combined.setdefault(
            chunk_id,
            {
                "chunk": result["chunk"],
                "semantic_score": 0.0,
                "keyword_score": 0.0
            }
        )

        combined[chunk_id]["semantic_score"] = (
            result["score"]
        )


    for result in keyword_results:

        chunk_id = result["chunk"]["chunk_id"]

        combined.setdefault(
            chunk_id,
            {
                "chunk": result["chunk"],
                "semantic_score": 0.0,
                "keyword_score": 0.0
            }
        )

        combined[chunk_id]["keyword_score"] = (
            result["score"]
        )


    # --------------------------------------------------------
    # Normalize scores
    # --------------------------------------------------------

    results = []

    semantic_scores = [
        item["semantic_score"]
        for item in combined.values()
    ]

    keyword_scores = [
        item["keyword_score"]
        for item in combined.values()
    ]

    max_semantic = (
        max(semantic_scores)
        if semantic_scores
        else 1.0
    )

    max_keyword = (
        max(keyword_scores)
        if keyword_scores
        else 1.0
    )


    for item in combined.values():

        semantic_score = item["semantic_score"]

        keyword_score = item["keyword_score"]

        normalized_semantic = (
            semantic_score / max_semantic
            if max_semantic > 0
            else 0.0
        )

        normalized_keyword = (
            keyword_score / max_keyword
            if max_keyword > 0
            else 0.0
        )

        hybrid_score = (
            0.7 * normalized_semantic
            +
            0.3 * normalized_keyword
        )

        results.append(
            {
                "chunk": item["chunk"],
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
                "normalized_semantic": normalized_semantic,
                "normalized_keyword": normalized_keyword,
                "hybrid_score": hybrid_score,
            }
        )


    # --------------------------------------------------------
    # Remove duplicate chunks
    # --------------------------------------------------------

    unique_results = []

    seen_chunks = set()

    for result in results:

        chunk_id = result["chunk"]["chunk_id"]

        if chunk_id not in seen_chunks:

            seen_chunks.add(chunk_id)

            unique_results.append(result)


    # --------------------------------------------------------
    # Sort by hybrid score
    # --------------------------------------------------------

    unique_results.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True
    )


    return unique_results[:top_k]


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    query = input(
        "\nEnter your search question: "
    ).strip()

    if not query:

        print(
            "Please enter a question."
        )

    else:

        results = hybrid_search(
            query,
            top_k=5
        )

        print(
            "\nSearch Results:"
        )

        print(
            "=============================="
        )

        for result in results:

            print(
                f"\nScore: "
                f"{result['hybrid_score']:.4f}"
            )

            print(
                result["chunk"]["content"]
            )
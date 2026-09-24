import json
import time
from pathlib import Path

import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

INDEX_FILE = BASE_DIR / "data" / "processed" / "faiss.index"
KNOWLEDGE_BASE = BASE_DIR / "data" / "processed" / "knowledge_base.json"

MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# LOAD EMBEDDING MODEL ONCE
# ============================================================

print(f"\nLoading embedding model: {MODEL_NAME}")

model_start = time.perf_counter()

EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)

model_load_time = time.perf_counter() - model_start

print(
    f"Embedding model loaded in: "
    f"{model_load_time:.2f} seconds"
)


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
                "score": float(score),
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

    scores = bm25.get_scores(
        query_tokens
    )

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
                "score": float(scores[index_id]),
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

    # --------------------------------------------------------
    # 1. Load knowledge base
    # --------------------------------------------------------

    start_time = time.perf_counter()

    chunks = load_knowledge_base()

    knowledge_base_time = (
        time.perf_counter()
        - start_time
    )

    print(
        f"Knowledge base load time: "
        f"{knowledge_base_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # 2. Load FAISS index
    # --------------------------------------------------------

    index_start = time.perf_counter()

    index = faiss.read_index(
        str(INDEX_FILE)
    )

    index_load_time = (
        time.perf_counter()
        - index_start
    )

    print(
        f"FAISS index load time: "
        f"{index_load_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # 3. Build BM25
    # --------------------------------------------------------

    bm25_start = time.perf_counter()

    bm25 = build_bm25(chunks)

    bm25_build_time = (
        time.perf_counter()
        - bm25_start
    )

    print(
        f"BM25 build time: "
        f"{bm25_build_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # 4. Semantic search
    # --------------------------------------------------------

    semantic_start = time.perf_counter()

    semantic_results = semantic_search(
        query,
        chunks,
        EMBEDDING_MODEL,
        index,
        top_k
    )

    semantic_time = (
        time.perf_counter()
        - semantic_start
    )

    print(
        f"Semantic search time: "
        f"{semantic_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # 5. Keyword search
    # --------------------------------------------------------

    keyword_start = time.perf_counter()

    keyword_results = keyword_search(
        query,
        chunks,
        bm25,
        top_k
    )

    keyword_time = (
        time.perf_counter()
        - keyword_start
    )

    print(
        f"Keyword search time: "
        f"{keyword_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # 6. Combine semantic + keyword results
    # --------------------------------------------------------

    combined = {}


    # Semantic results

    for result in semantic_results:

        chunk_id = result["chunk"]["chunk_id"]

        combined.setdefault(
            chunk_id,
            {
                "chunk": result["chunk"],
                "semantic_score": 0.0,
                "keyword_score": 0.0,
            }
        )

        combined[chunk_id][
            "semantic_score"
        ] = result["score"]


    # Keyword results

    for result in keyword_results:

        chunk_id = result["chunk"]["chunk_id"]

        combined.setdefault(
            chunk_id,
            {
                "chunk": result["chunk"],
                "semantic_score": 0.0,
                "keyword_score": 0.0,
            }
        )

        combined[chunk_id][
            "keyword_score"
        ] = result["score"]


    # --------------------------------------------------------
    # 7. Normalize scores
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


    # --------------------------------------------------------
    # 8. Calculate hybrid score
    # --------------------------------------------------------

    for item in combined.values():

        semantic_score = (
            item["semantic_score"]
        )

        keyword_score = (
            item["keyword_score"]
        )


        # Normalize semantic score

        normalized_semantic = (
            semantic_score / max_semantic
            if max_semantic > 0
            else 0.0
        )


        # Normalize keyword score

        normalized_keyword = (
            keyword_score / max_keyword
            if max_keyword > 0
            else 0.0
        )


        # 70% semantic
        # 30% keyword

        hybrid_score = (
            0.7 * normalized_semantic
            + 0.3 * normalized_keyword
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
    # 9. Remove duplicate chunks
    # --------------------------------------------------------

    unique_results = []

    seen_chunks = set()

    for result in results:

        chunk_id = result[
            "chunk"
        ]["chunk_id"]

        if chunk_id not in seen_chunks:

            seen_chunks.add(
                chunk_id
            )

            unique_results.append(
                result
            )


    # --------------------------------------------------------
    # 10. Sort by hybrid score
    # --------------------------------------------------------

    unique_results.sort(
        key=lambda item: item[
            "hybrid_score"
        ],
        reverse=True
    )


    # --------------------------------------------------------
    # 11. Return top results
    # --------------------------------------------------------

    return unique_results[:top_k]


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    query = input(
        "\nEnter your UPI safety question: "
    ).strip()


    if not query:

        print(
            "Please enter a question."
        )


    else:

        results = hybrid_search(
            query
        )


        print(
            "\nHybrid Search Results:"
        )


        for rank, result in enumerate(
            results,
            start=1
        ):

            chunk = result[
                "chunk"
            ]


            print(
                "\n--------------------------------"
            )


            print(
                f"Rank: {rank}"
            )


            print(
                f"Hybrid Score: "
                f"{result['hybrid_score']:.4f}"
            )


            print(
                f"Semantic Score: "
                f"{result['semantic_score']:.4f}"
            )


            print(
                f"Keyword Score: "
                f"{result['keyword_score']:.4f}"
            )


            print(
                f"File: "
                f"{chunk['file_name']}"
            )


            print(
                f"Category: "
                f"{chunk['category']}"
            )


            print(
                f"Chunk ID: "
                f"{chunk['chunk_id']}"
            )


            print(
                "Content:"
            )


            print(
                chunk["content"][:500]
            )
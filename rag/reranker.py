import time

from sentence_transformers import CrossEncoder

from rag.hybrid_retriever import hybrid_search


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# Load the CrossEncoder only once when the application starts.
print(f"\nLoading reranking model: {MODEL_NAME}")

model_start = time.perf_counter()

RERANKER_MODEL = CrossEncoder(MODEL_NAME)

model_load_time = time.perf_counter() - model_start

print(
    f"Reranking model loaded in: "
    f"{model_load_time:.2f} seconds"
)


def rerank_results(query, results, top_k=3):
    """
    Rerank retrieved results using the already-loaded
    CrossEncoder model.
    """

    pairs = [
        (query, result["chunk"]["content"])
        for result in results
    ]

    # Measure only prediction time.
    prediction_start = time.perf_counter()

    scores = RERANKER_MODEL.predict(pairs)

    prediction_time = time.perf_counter() - prediction_start

    print(
        f"Reranking prediction time: "
        f"{prediction_time:.2f} seconds"
    )

    reranked_results = []

    for result, score in zip(results, scores):
        reranked_results.append(
            {
                "chunk": result["chunk"],
                "hybrid_score": result["hybrid_score"],
                "rerank_score": float(score),
            }
        )

    reranked_results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return reranked_results[:top_k]


def retrieve_and_rerank(query, retrieval_k=5, final_k=3):
    """
    Retrieve relevant chunks using hybrid search
    and then rerank them using CrossEncoder.

    retrieval_k:
        Number of results retrieved by hybrid search.

    final_k:
        Number of results returned after reranking.
    """

    hybrid_results = hybrid_search(
        query,
        top_k=retrieval_k
    )

    final_results = rerank_results(
        query,
        hybrid_results,
        top_k=final_k
    )

    return final_results


if __name__ == "__main__":

    query = input(
        "\nEnter your UPI safety question: "
    ).strip()

    if not query:
        print("Please enter a question.")

    else:

        reranked_results = retrieve_and_rerank(
            query,
            retrieval_k=5,
            final_k=3
        )

        print("\nReranked Results:")

        for rank, result in enumerate(
            reranked_results,
            start=1
        ):
            chunk = result["chunk"]

            print("\n--------------------------------")
            print(f"Rank: {rank}")

            print(
                f"Rerank Score: "
                f"{result['rerank_score']:.4f}"
            )

            print(
                f"Hybrid Score: "
                f"{result['hybrid_score']:.4f}"
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

            print("Content:")
            print(
                chunk["content"][:500]
            )
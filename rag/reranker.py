import time

from sentence_transformers import CrossEncoder
from rag.hybrid_retriever import hybrid_search


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# ============================================================
# LAZY MODEL LOADING
# ============================================================

RERANKER_MODEL = None


def get_reranker_model():
    """
    Load the reranking model only when it is actually needed.

    This prevents the model from consuming memory during
    FastAPI startup.
    """

    global RERANKER_MODEL

    if RERANKER_MODEL is None:

        print(
            f"\nLoading reranking model: {MODEL_NAME}"
        )

        model_start = time.perf_counter()

        RERANKER_MODEL = CrossEncoder(
            MODEL_NAME
        )

        model_load_time = (
            time.perf_counter() - model_start
        )

        print(
            f"Reranking model loaded in: "
            f"{model_load_time:.2f} seconds"
        )

    return RERANKER_MODEL


# ============================================================
# RERANK RESULTS
# ============================================================

def rerank_results(
    query,
    results,
    top_k=3
):

    # --------------------------------------------------------
    # Get reranking model
    # --------------------------------------------------------

    model = get_reranker_model()


    # --------------------------------------------------------
    # Build query/document pairs
    # --------------------------------------------------------

    pairs = [
        (
            query,
            result["chunk"]["content"]
        )
        for result in results
    ]


    # --------------------------------------------------------
    # Generate reranking scores
    # --------------------------------------------------------

    prediction_start = time.perf_counter()

    scores = model.predict(
        pairs
    )

    prediction_time = (
        time.perf_counter()
        -
        prediction_start
    )

    print(
        f"Reranking prediction time: "
        f"{prediction_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # Build reranked results
    # --------------------------------------------------------

    reranked_results = []

    for result, score in zip(
        results,
        scores
    ):

        reranked_results.append(
            {
                "chunk": result["chunk"],
                "hybrid_score": result["hybrid_score"],
                "rerank_score": float(score),
            }
        )


    # --------------------------------------------------------
    # Sort by reranking score
    # --------------------------------------------------------

    reranked_results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )


    return reranked_results[:top_k]


# ============================================================
# RETRIEVE AND RERANK
# ============================================================

def retrieve_and_rerank(
    query,
    retrieval_k=5,
    final_k=3
):

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

        results = retrieve_and_rerank(
            query,
            retrieval_k=5,
            final_k=3
        )

        print(
            "\nReranked Results:"
        )

        print(
            "=============================="
        )

        for result in results:

            print(
                f"\nHybrid Score: "
                f"{result['hybrid_score']:.4f}"
            )

            print(
                f"Rerank Score: "
                f"{result['rerank_score']:.4f}"
            )

            print(
                result["chunk"]["content"]
            )
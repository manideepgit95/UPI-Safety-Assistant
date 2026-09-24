def rerank_results(query, results, top_k=3):
    """
    Lightweight replacement for the CrossEncoder reranker.

    The original CrossEncoder produced a rerank_score.
    This lightweight version uses the existing hybrid_score
    as the rerank_score so the rest of the application
    continues to work without loading PyTorch.
    """

    reranked_results = []

    for result in results:
        hybrid_score = float(
            result.get("hybrid_score", 0.0)
        )

        reranked_results.append(
            {
                "chunk": result["chunk"],
                "hybrid_score": hybrid_score,
                "rerank_score": hybrid_score,
            }
        )

    reranked_results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return reranked_results[:top_k]


def retrieve_and_rerank(query, retrieval_k=5, final_k=3):
    """
    Retrieve knowledge-base results and apply lightweight
    ranking without using a neural CrossEncoder.
    """

    from rag.hybrid_retriever import hybrid_search

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
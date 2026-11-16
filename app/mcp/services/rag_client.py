from functools import lru_cache

from app.rag.pipeline import answer_question
from app.rag.reranker import Reranker
from app.mcp.services.knowledge_gap_client import notify_knowledge_gap

@lru_cache(maxsize=1)
def get_reranker():
    return Reranker()


def ask_rag(question: str) -> dict:

    result = answer_question(
        question=question,
        reranker=get_reranker(),
        candidate_top_k=10,
        final_top_k=5
    )

    search_output = result["search_output"]

    if result.get("knowledge_gap"):
        notify_knowledge_gap(
            question=result["question"],
            reason=result.get("knowledge_gap_reason") or "unknown",
            top_rerank_score=result.get("top_rerank_score")
        )

    sources = []

    for chunk in search_output["reranked_results"]:
        sources.append({
            "title": chunk["title"],
            "category": chunk["category"],
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
            "rerank_score": round(chunk["rerank_score"], 4),
            "distance": round(chunk["distance"], 4)
        })

    return {
        "question": result["question"],
        "answer": result["answer"],
        "selected_category": search_output["selected_category"],
        "category_filters": search_output["category_filters"],
        "sources": sources,

        # Knowledge Gap Detection bilgileri
        "knowledge_gap": result.get("knowledge_gap", False),
        "knowledge_gap_reason": result.get("knowledge_gap_reason"),
        "top_rerank_score": result.get("top_rerank_score")
    }
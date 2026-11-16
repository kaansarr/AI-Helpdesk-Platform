from functools import lru_cache

from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.pipeline import answer_question
from app.rag.reranker import Reranker


router = APIRouter(tags=["RAG"])


class AskRequest(BaseModel):
    question: str


@lru_cache(maxsize=1)
def get_reranker():
    return Reranker()


@router.post("/ask")
def ask(request: AskRequest):

    result = answer_question(
        question=request.question,
        reranker=get_reranker(),
        candidate_top_k=10,
        final_top_k=5
    )

    search_output = result["search_output"]

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
        "sources": sources
    }
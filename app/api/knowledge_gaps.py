from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.repositories.knowledge_gap_repository import save_knowledge_gap


router = APIRouter()


class KnowledgeGapRequest(BaseModel):
    question: str = Field(min_length=1)
    reason: str
    top_rerank_score: float | None = None


@router.post("/knowledge-gaps")
def create_knowledge_gap(payload: KnowledgeGapRequest):
    """
    n8n tarafından gönderilen Knowledge Gap bilgisini
    PostgreSQL veritabanına kaydeder.
    """

    result = save_knowledge_gap(
        question=payload.question,
        reason=payload.reason,
        top_rerank_score=payload.top_rerank_score
    )

    return {
        "success": True,
        "message": "Knowledge Gap kaydedildi.",
        "data": result
    }
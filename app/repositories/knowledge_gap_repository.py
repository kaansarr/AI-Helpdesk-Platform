from app.core.db import get_connection


def save_knowledge_gap(
    question: str,
    reason: str,
    top_rerank_score: float | None
) -> dict:
    """
    Knowledge Gap kaydını PostgreSQL'e ekler.

    Aynı soru tekrar gelirse yeni kayıt oluşturmak yerine
    occurrence_count değerini artırır.
    """

    query = """
        INSERT INTO knowledge_gaps (
            question,
            reason,
            top_rerank_score
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (question)
        DO UPDATE SET
            occurrence_count = knowledge_gaps.occurrence_count + 1,
            last_detected_at = NOW(),
            reason = EXCLUDED.reason,
            top_rerank_score = EXCLUDED.top_rerank_score
        RETURNING
            id,
            question,
            reason,
            top_rerank_score,
            occurrence_count;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (question, reason, top_rerank_score)
            )

            row = cur.fetchone()

    return {
        "id": row[0],
        "question": row[1],
        "reason": row[2],
        "top_rerank_score": row[3],
        "occurrence_count": row[4]
    }
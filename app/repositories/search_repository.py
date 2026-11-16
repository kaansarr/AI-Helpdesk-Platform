from app.core.db import get_connection


def search_old_chunks(
    query_vector: str,
    top_k: int = 10,
    category_filters: list[str] | None = None
) -> list[dict]:

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    source,
                    title,
                    category,
                    chunk_index,
                    content,
                    embedding <=> %s::vector AS distance
                FROM helpdesk_chunks
                WHERE (%s::text[] IS NULL OR category = ANY(%s::text[]))
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                (
                    query_vector,
                    category_filters,
                    category_filters,
                    query_vector,
                    top_k
                )
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "source": row[1],
            "title": row[2],
            "category": row[3],
            "chunk_index": row[4],
            "content": row[5],
            "distance": row[6]
        }
        for row in rows
    ]


def search_uploaded_chunks(
    query_vector: str,
    top_k: int = 10
) -> list[dict]:

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    dc.id,
                    d.filename,
                    dc.chunk_index,
                    dc.content,
                    dc.embedding <=> %s::vector AS distance
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE d.status = 'completed'
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s;
                """,
                (query_vector, query_vector, top_k)
            )

            rows = cur.fetchall()

    return [
        {
            "id": -row[0],
            "source": row[1],
            "title": row[1],
            "category": "Yüklenen Doküman",
            "chunk_index": row[2],
            "content": row[3],
            "distance": row[4]
        }
        for row in rows
    ]
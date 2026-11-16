from app.core.db import get_connection


def create_document_chunk_record(
    document_id: int,
    chunk_index: int,
    content: str,
    embedding: list[float]
) -> int:

    embedding_vector = "[" + ",".join(
        str(value) for value in embedding
    ) + "]"

    sql = """
        INSERT INTO document_chunks (
            document_id,
            chunk_index,
            content,
            embedding
        )
        VALUES (%s, %s, %s, %s::vector)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    document_id,
                    chunk_index,
                    content,
                    embedding_vector
                )
            )

            row = cur.fetchone()

    return row[0]
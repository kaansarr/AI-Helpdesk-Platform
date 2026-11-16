from app.core.db import get_connection


def create_document_record(
    filename: str,
    file_type: str,
    file_hash: str,
    file_path: str
) -> int:

    sql = """
        INSERT INTO documents (
            filename,
            file_type,
            file_hash,
            file_path
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (filename, file_type, file_hash, file_path)
            )

            row = cur.fetchone()

    return row[0]



def update_document_status(
    document_id: int,
    status: str,
    error_message: str | None = None
) -> bool:

    sql = """
        UPDATE documents
        SET status = %s,
            error_message = %s
        WHERE id = %s
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (status, error_message, document_id)
            )

            row = cur.fetchone()

    return row is not None



def get_document_by_hash(file_hash: str) -> dict | None:

    sql = """
        SELECT id, filename, status
        FROM documents
        WHERE file_hash = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (file_hash,))
            row = cur.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "filename": row[1],
        "status": row[2]
    }
from uuid import UUID
from app.core.db import get_connection


def create_message_record(
    session_id: str,
    role: str,
    content: str
) -> int:

    sql = """
        INSERT INTO chat_messages (
            session_id,
            role,
            content
        )
        VALUES (%s, %s, %s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    UUID(session_id),
                    role,
                    content
                )
            )

            row = cur.fetchone()

    return row[0]


def get_session_messages(session_id: str) -> list:

    sql = """
        SELECT
            id,
            role,
            content,
            created_at
        FROM chat_messages
        WHERE session_id = %s
        ORDER BY id ASC;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (UUID(session_id),))
            rows = cur.fetchall()

    messages = []

    for row in rows:
        messages.append({
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "created_at": row[3].isoformat()
        })

    return messages
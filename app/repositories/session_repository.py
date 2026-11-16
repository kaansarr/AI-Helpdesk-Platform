from uuid import uuid4
from app.core.db import get_connection


def create_session_record() -> str:

    session_id = str(uuid4())

    sql = """
        INSERT INTO chat_sessions (id)
        VALUES (%s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(sql, (session_id,))
            row = cur.fetchone()

    return str(row[0])



def session_exists(session_id: str) -> bool:

    sql = """
        SELECT EXISTS (
            SELECT 1
            FROM chat_sessions
            WHERE id = %s
        );
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (session_id,))
            row = cur.fetchone()

    return row[0]


def get_all_sessions() -> list:

    sql = """
        SELECT
            s.id,
            s.created_at,
            (
                SELECT LEFT(m.content, 45)
                FROM chat_messages m
                WHERE m.session_id = s.id
                  AND m.role = 'user'
                ORDER BY m.id ASC
                LIMIT 1
            ) AS title
        FROM chat_sessions s
        ORDER BY s.created_at DESC;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    sessions = []

    for row in rows:
        sessions.append({
            "session_id": str(row[0]),
            "created_at": row[1].isoformat(),
            "title": row[2] or "Yeni Sohbet"
        })

    return sessions
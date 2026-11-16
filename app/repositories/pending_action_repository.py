import json

from app.core.db import get_connection


def create_pending_action_record(
    session_id: str,
    action_data: dict
) -> int:

    sql = """
        INSERT INTO pending_actions (
            session_id,
            action_data
        )
        VALUES (%s, %s::jsonb)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    session_id,
                    json.dumps(action_data)
                )
            )

            row = cur.fetchone()

    return row[0]



def get_pending_action_record(session_id: str) -> dict | None:

    sql = """
        SELECT
            id,
            action_data,
            status,
            expires_at
        FROM pending_actions
        WHERE session_id = %s
          AND status = 'pending'
          AND expires_at > CURRENT_TIMESTAMP
        ORDER BY id DESC
        LIMIT 1;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (session_id,))
            row = cur.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "action_data": row[1],
        "status": row[2],
        "expires_at": row[3].isoformat()
    }



def claim_pending_action_record(
    action_id: int,
    session_id: str
) -> dict | None:

    sql = """
        UPDATE pending_actions
        SET status = 'processing'
        WHERE id = %s
          AND session_id = %s
          AND status = 'pending'
          AND expires_at > CURRENT_TIMESTAMP
        RETURNING id, session_id, action_data;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (action_id, session_id))
            row = cur.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "session_id": str(row[1]),
        "action_data": row[2]
    }


def update_pending_action_status(
    action_id: int,
    current_status: str,
    new_status: str
) -> bool:

    sql = """
        UPDATE pending_actions
        SET status = %s
        WHERE id = %s
          AND status = %s
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (new_status, action_id, current_status)
            )

            row = cur.fetchone()

    return row is not None
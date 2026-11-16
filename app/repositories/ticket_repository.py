from datetime import datetime
from app.mcp.services.workflow_client import send_ticket_created_event
from app.core.db import get_connection



def create_ticket_record(
    title: str,
    description: str,
    category: str = "other",
    priority: str = "medium"
) -> dict:

    ticket_code = f"TCK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    sql = """
    INSERT INTO tickets (
        ticket_code,
        title,
        description,
        status,
        category,
        priority
    )
    VALUES (
        %s, %s, %s, %s, %s, %s
    )
    RETURNING
        id,
        ticket_code,
        title,
        description,
        status,
        category,
        priority,
        created_at,
        updated_at;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    ticket_code,
                    title,
                    description,
                    "open",
                    category,
                    priority
                )
            )

            row = cur.fetchone()

    ticket = {
        "id": row[0],
        "ticket_id": row[1],
        "title": row[2],
        "description": row[3],
        "status": row[4],
        "category": row[5],
        "priority": row[6],
        "created_at": row[7].isoformat(),
        "updated_at": row[8].isoformat()
    }

    send_ticket_created_event(ticket)

    return ticket

def list_ticket_records(limit: int = 10) -> list:
    """
    PostgreSQL'den son ticket kayıtlarını getirir.
    """

    sql = """
    SELECT
        id,
        ticket_code,
        title,
        description,
        status,
        created_at,
        updated_at
    FROM tickets
    ORDER BY id DESC
    LIMIT %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()

    tickets = []

    for row in rows:
        tickets.append({
            "id": row[0],
            "ticket_id": row[1],
            "title": row[2],
            "description": row[3],
            "status": row[4],
            "created_at": row[5].isoformat(),
            "updated_at": row[6].isoformat()
        })

    return tickets


def get_ticket_record(ticket_id: str) -> dict | None:
    """
    Ticket koduna göre tek bir ticket kaydını getirir.
    """

    sql = """
    SELECT
        id,
        ticket_code,
        title,
        description,
        status,
        created_at,
        updated_at
    FROM tickets
    WHERE ticket_code = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (ticket_id,))
            row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "ticket_id": row[1],
        "title": row[2],
        "description": row[3],
        "status": row[4],
        "created_at": row[5].isoformat(),
        "updated_at": row[6].isoformat()
    }


def update_ticket_status_record(ticket_id: str, status: str) -> dict | None:
    """
    Ticket koduna göre ticket durumunu günceller.
    """

    sql = """
    UPDATE tickets
    SET
        status = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE ticket_code = %s
    RETURNING
        id,
        ticket_code,
        title,
        description,
        status,
        created_at,
        updated_at;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    status,
                    ticket_id
                )
            )

            row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "ticket_id": row[1],
        "title": row[2],
        "description": row[3],
        "status": row[4],
        "created_at": row[5].isoformat(),
        "updated_at": row[6].isoformat()
    }
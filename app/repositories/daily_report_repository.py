from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.db import get_connection


def get_daily_report_data():
    """
    Türkiye saatine göre bugün 00:00'dan
    şu ana kadar olan IT operasyon verilerini toplar.
    """

    now_tr = datetime.now(ZoneInfo("Europe/Istanbul"))
    start_tr = datetime.combine(
        now_tr.date(),
        time.min,
        tzinfo=ZoneInfo("Europe/Istanbul")
    )

    # Ticket tarihleri UTC olarak, timezone bilgisi olmadan tutuluyor.
    start_utc = start_tr.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end_utc = now_tr.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Bugün oluşturulan ticket sayısı
            cur.execute("""
                SELECT COUNT(*)
                FROM tickets
                WHERE created_at >= %s
                  AND created_at < %s
            """, (start_utc, end_utc))

            created_today = cur.fetchone()[0]

            # Bugün kapatılan ticket sayısı
            cur.execute("""
                SELECT COUNT(*)
                FROM tickets
                WHERE status = 'closed'
                  AND updated_at >= %s
                  AND updated_at < %s
            """, (start_utc, end_utc))

            closed_today = cur.fetchone()[0]

            # Mevcut ticket durumları
            cur.execute("""
                SELECT status, COUNT(*)
                FROM tickets
                GROUP BY status
            """)

            status_counts = dict(cur.fetchall())

            # Bugün oluşturulan ticket kategorileri
            cur.execute("""
                SELECT category, COUNT(*)
                FROM tickets
                WHERE created_at >= %s
                  AND created_at < %s
                GROUP BY category
                ORDER BY COUNT(*) DESC
            """, (start_utc, end_utc))

            categories = [
                {"category": category, "count": count}
                for category, count in cur.fetchall()
            ]

            # Bugün ilk kez tespit edilen Knowledge Gap soruları
            cur.execute("""
                SELECT question, reason, occurrence_count
                FROM knowledge_gaps
                WHERE first_detected_at >= %s
                  AND first_detected_at < %s
                ORDER BY first_detected_at DESC
            """, (
                start_utc.replace(tzinfo=ZoneInfo("UTC")),
                end_utc.replace(tzinfo=ZoneInfo("UTC"))
            ))

            knowledge_gaps = [
                {
                    "question": question,
                    "reason": reason,
                    "occurrence_count": count
                }
                for question, reason, count in cur.fetchall()
            ]

    return {
        "report_date": now_tr.date().isoformat(),
        "timezone": "Europe/Istanbul",
        "period_start": start_tr.isoformat(),
        "period_end": now_tr.isoformat(),
        "tickets": {
            "created_today": created_today,
            "closed_today": closed_today,
            "open_total": status_counts.get("open", 0),
            "pending_total": status_counts.get("pending", 0),
            "closed_total": status_counts.get("closed", 0),
            "categories_today": categories
        },
        "knowledge_gaps": knowledge_gaps
    }
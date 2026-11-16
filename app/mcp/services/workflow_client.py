import os
import requests

from dotenv import load_dotenv
from app.mcp.utils.logger import get_logger


load_dotenv()

logger = get_logger(__name__)


def send_ticket_created_event(ticket: dict) -> bool:
    """
    Ticket oluşturulduğunda n8n webhook'a event gönderir.
    Workflow hatası ticket oluşturma işlemini bozmamalıdır.
    """

    webhook_url = os.getenv("N8N_TICKET_CREATED_WEBHOOK_URL")

    if not webhook_url:
        logger.warning("N8N_TICKET_CREATED_WEBHOOK_URL tanımlı değil. Workflow tetiklenmedi.")
        return False

    payload = {
        "event": "ticket_created",
        "ticket": ticket
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )

        response.raise_for_status()

        logger.info(
            f"n8n ticket_created workflow tetiklendi. "
            f"ticket_id={ticket.get('ticket_id')}, "
            f"status_code={response.status_code}, "
            f"response={response.text}"
)

        return True

    except Exception as error:
        logger.exception(
            f"n8n workflow tetiklenirken hata oluştu. ticket_id={ticket.get('ticket_id')}"
        )

        return False
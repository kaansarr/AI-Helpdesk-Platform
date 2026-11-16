import os
import logging
import requests

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def notify_knowledge_gap(
    question: str,
    reason: str,
    top_rerank_score: float | None
) -> bool:
    """
    RAG bilgi eksikliği tespit ettiğinde
    n8n webhook'una HTTP POST gönderir.
    """

    webhook_url = os.getenv("N8N_KNOWLEDGE_GAP_WEBHOOK_URL")

    if not webhook_url:
        logger.warning("Knowledge Gap webhook adresi tanımlanmamış.")
        return False

    payload = {
        "question": question,
        "reason": reason,
        "top_rerank_score": top_rerank_score
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=5
        )

        response.raise_for_status()

        logger.info("Knowledge Gap bildirimi n8n'e gönderildi.")
        return True

    except requests.RequestException as error:
        logger.warning(
            "Knowledge Gap webhook hatası: %s",
            error
        )
        return False
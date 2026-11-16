import os
import requests
from dotenv import load_dotenv

load_dotenv()

N8N_WEBHOOK_URL = os.getenv(
    "N8N_DOCUMENT_WEBHOOK_URL",
    "http://localhost:5678/webhook-test/document-ingestion"
)


def trigger_document_workflow(stored_filename: str) -> dict:

    response = requests.post(
        N8N_WEBHOOK_URL,
        json={
            "stored_filename": stored_filename
        },
        timeout=15
    )

    response.raise_for_status()

    return {
        "success": True,
        "message": "n8n workflow tetiklendi."
    }
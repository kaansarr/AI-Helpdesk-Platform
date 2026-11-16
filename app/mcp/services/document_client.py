import os
import requests

RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8002")


def upload_document_to_rag(filename: str, content: bytes) -> dict:
    response = requests.post(
        f"{RAG_API_URL}/documents/upload",
        files={
            "file": (filename, content)
        },
        timeout=60
    )

    response.raise_for_status()
    return response.json()
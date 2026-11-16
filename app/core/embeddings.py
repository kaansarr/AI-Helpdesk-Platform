import os

import requests
from dotenv import load_dotenv


load_dotenv()


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_URL = f"{OLLAMA_BASE_URL}/api/embeddings"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


def embed_text(text: str) -> list[float]:
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }

    response = requests.post(
        OLLAMA_EMBEDDING_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["embedding"]
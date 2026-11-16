import os

import requests
from dotenv import load_dotenv


load_dotenv()


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3:latest")


def generate_answer(user_prompt: str, system_prompt: str | None = None) -> str:
    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": user_prompt
    })

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    response = requests.post(
        OLLAMA_CHAT_URL,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]


if __name__ == "__main__":
    system_prompt = """
Sen yalnızca Türkçe cevap veren bir şirket içi IT destek asistanısın.
İngilizce kelime kullanma.
Cevabına açıklama, not, kaynak etiketi veya meta cümle ekleme.
Sadece son kullanıcıya verilecek cevabı yaz.
"""

    user_prompt = """
Kullanıcı sorusu:
VPN bağlanmıyor ne yapmalıyım?

Kısa, net ve adım adım cevap ver.
"""

    answer = generate_answer(
        user_prompt=user_prompt,
        system_prompt=system_prompt
    )

    print("Model cevabı:")
    print("-" * 50)
    print(answer)
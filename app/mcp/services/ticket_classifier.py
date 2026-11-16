import requests

from app.mcp.agent.ticket_schema import TicketClassification


def classify_ticket(description: str) -> TicketClassification:

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3.2:3b",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Sen bir IT destek uzmanısın. "
                        "Kullanıcının destek talebini analiz et. "
                        "Destek talebi için kısa, açıklayıcı ve Türkçe bir başlık oluştur. "
                        "Başlık 5 ile 100 karakter arasında olmalıdır. "
                        "Başlıkta 'destek kaydı oluştur' gibi komut ifadelerini kullanma. "
                        "Kategoriler: network, hardware, software, other. "
                        "Öncelikler: low, medium, high. "
                        "Sadece title, category ve priority alanlarını içeren JSON döndür. "
                        "JSON alan adları İngilizce olmalıdır."
                    )
                },
                {
                    "role": "user",
                    "content": description
                }
            ],
            "format": TicketClassification.model_json_schema(),
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=120
    )

    response.raise_for_status()

    llm_response = response.json()["message"]["content"]

    classification = TicketClassification.model_validate_json(
        llm_response
    )

    return classification
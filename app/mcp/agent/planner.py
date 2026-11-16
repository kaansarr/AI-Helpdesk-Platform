import json
import os
import requests

from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3:latest")


def ask_llm_for_tool_decision(user_message: str) -> dict:
    """
    Kullanıcı mesajını LLM'e gönderir.
    LLM'den hangi MCP tool'unun çağrılacağını JSON olarak ister.
    """

    system_prompt = """
Sen bir IT Helpdesk Agent karar vericisisin.

Görevin:
Kullanıcı mesajına göre hangi MCP tool'unun çağrılacağını seçmek.

Mevcut MCP tool'ları:

1. get_user_info
Açıklama: Kullanıcı kendi bilgilerini sorarsa kullanılır.
Gerekli arguments:
- user_id

2. create_ticket
Açıklama: Kullanıcı ticket, destek kaydı veya IT talebi oluşturmak istiyorsa kullanılır.
Gerekli arguments:
- title
- description

3. search_documents
Açıklama: Kullanıcı şirket içi bilgi tabanındaki herhangi bir konu hakkında
bilgi, açıklama, çözüm veya yönlendirme istiyorsa kullanılır.

Bu konular IT sorunlarını, şirket politikalarını, prosedürleri,
çalışanlara yönelik kuralları ve kurum içi bilgileri kapsayabilir.

Bilginin dokümanlarda bulunup bulunmadığına sen karar verme.
Önce search_documents aracını kullanarak bilgi tabanında ara.
İlgili kaynak bulunamazsa RAG sistemi bunu belirleyecektir.

Gerekli arguments:
- question

4. list_tickets
Açıklama: Kullanıcı açılmış ticketları, destek kayıtlarını veya son kayıtları görmek istiyorsa kullanılır.
Gerekli arguments:
- limit


5. get_ticket_detail
Açıklama: Kullanıcı belirli bir ticket kodunun detayını görmek istiyorsa kullanılır.
Gerekli arguments:
- ticket_id

6. update_ticket_status
Açıklama: Kullanıcı belirli bir ticket kodunun durumunu değiştirmek istiyorsa kullanılır.
Gerekli arguments:
- ticket_id
- status


Kurallar:
- Sadece kullanıcı gerçekten tool gerektiren bir şey istiyorsa tool seç.
- Kullanıcı sadece selam verirse veya alakasız konuşursa tool_name null olsun.
- Kullanıcı teknik bir sorun söylüyor ama ticket açmak istemiyorsa search_documents kullan.
- Kullanıcı "ne yapmalıyım", "nasıl çözerim", "çözümü nedir" gibi bilgi istiyorsa search_documents kullan.
- Kullanıcı teknik sorun söylüyor ve ayrıca ticket açmak istiyorsa create_ticket kullan.
- create_ticket için title her zaman "Kullanıcı destek talebi" olabilir.
- create_ticket için description kullanıcının orijinal mesajı olmalıdır.
- search_documents için question kullanıcının sorusu olmalıdır.
- Kullanıcı belirli bir ticket kodu verip detayını soruyorsa get_ticket_detail kullan.
- Ticket kodları genelde TCK- ile başlar.
- Kullanıcı belirli bir ticket kodunun durumunu değiştirmek, kapatmak veya güncellemek istiyorsa update_ticket_status kullan.
- Kullanıcı "kapat", "closed yap", "çözüldü yap" derse status "closed" olmalıdır.
- Kullanıcı "open yap", "açık yap" derse status "open" olmalıdır.
- Kullanıcı "pending yap", "beklemede yap" derse status "pending" olmalıdır.
- Kullanıcı şirket içi bir konu hakkında bilgi istiyorsa
  search_documents aracını seç.
  Konunun yalnızca IT ile ilgili olması gerekmez.
  Bilgi tabanında bulunup bulunmadığını tahmin etme.
- Kullanıcı yalnızca selam veriyorsa veya şirket bilgi tabanıyla
  ilgisiz gündelik sohbet ediyorsa tool_name null seç.

Örnekler:

Kullanıcı mesajı:
Benim bilgilerim nedir?

Doğru JSON:
{
  "tool_name": "get_user_info",
  "arguments": {
    "user_id": "demo_user"
  }
}

Kullanıcı mesajı:
TCK-20260819123504 ticket durumunu closed yap

Doğru JSON:
{
  "tool_name": "update_ticket_status",
  "arguments": {
    "ticket_id": "TCK-20260819123504",
    "status": "closed"
  }
}

Kullanıcı mesajı:
VPN açılmıyor ne yapmalıyım?

Doğru JSON:
{
  "tool_name": "search_documents",
  "arguments": {
    "question": "VPN açılmıyor ne yapmalıyım?"
  }
}

Kullanıcı mesajı:
VPN açılmıyor bunun için ticket açar mısın?

Doğru JSON:
{
  "tool_name": "create_ticket",
  "arguments": {
    "title": "Kullanıcı destek talebi",
    "description": "VPN açılmıyor bunun için ticket açar mısın?"
  }
}

Kullanıcı mesajı:
Merhaba nasılsın?

Doğru JSON:
{
  "tool_name": null,
  "arguments": {}
}


Kullanıcı mesajı:
Son açılan ticketları gösterir misin?

Doğru JSON:
{
  "tool_name": "list_tickets",
  "arguments": {
    "limit": 10
  }
}

- Cevabın yalnızca geçerli JSON object olmalıdır.
- JSON dışında hiçbir metin yazma.
- Açıklama yazma.
- Markdown yazma.
- Kod bloğu kullanma.
- Eğer tool gerekmiyorsa tool_name null olmalı ve arguments boş object olmalı.

Dönüş formatı:

{
  "tool_name": "get_user_info veya create_ticket veya search_documents veya null",
  "arguments": {}
}
"""

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        "stream": False,
        "format": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": ["string", "null"],
                    "enum": ["get_user_info", "create_ticket", "search_documents", "list_tickets", "get_ticket_detail", "update_ticket_status", None]
                },
                "arguments": {
                    "type": "object"
                }
            },
            "required": ["tool_name", "arguments"]
        },
        "options": {
            "temperature": 0
        }
    }

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=120
    )

    if response.status_code != 200:
        print("OLLAMA ERROR STATUS:")
        print(response.status_code)

        print("OLLAMA ERROR TEXT:")
        print(response.text)

        response.raise_for_status()

    data = response.json()

    # Ollama performans bilgileri
    total_duration = data.get("total_duration", 0) / 1_000_000_000
    load_duration = data.get("load_duration", 0) / 1_000_000_000
    prompt_duration = data.get("prompt_eval_duration", 0) / 1_000_000_000
    generation_duration = data.get("eval_duration", 0) / 1_000_000_000

    prompt_tokens = data.get("prompt_eval_count", 0)
    generated_tokens = data.get("eval_count", 0)

    print("\n========== OLLAMA PERFORMANS ==========")
    print(f"Model: {LLM_MODEL}")
    print(f"Toplam süre: {total_duration:.2f} saniye")
    print(f"Model yükleme: {load_duration:.2f} saniye")
    print(f"Prompt işleme: {prompt_duration:.2f} saniye")
    print(f"Cevap üretme: {generation_duration:.2f} saniye")
    print(f"Prompt token sayısı: {prompt_tokens}")
    print(f"Üretilen token sayısı: {generated_tokens}")
    print("=======================================\n")

    content = data.get("message", {}).get("content", "")

    try:
        decision = json.loads(content)
    except json.JSONDecodeError:
        return {
            "tool_name": None,
            "arguments": {},
            "error": "LLM geçerli JSON döndürmedi.",
            "raw_content": content
        }

    return decision
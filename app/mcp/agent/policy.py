RISKY_TOOLS = {
    "create_ticket": {
        "requires_confirmation": True,
        "reason": "Bu tool sistemde yeni destek kaydı oluşturur."
    },
    "get_user_info": {
        "requires_confirmation": False,
        "reason": "Bu tool sadece kullanıcı bilgisini okur."
    },
    "search_documents": {
        "requires_confirmation": False,
        "reason": "Bu tool sadece dokümanlarda arama yapar."
    },

    "list_tickets": {
    "requires_confirmation": False,
    "reason": "Bu tool sadece destek kayıtlarını okur."
    },

    "get_ticket_detail": {
    "requires_confirmation": False,
    "reason": "Bu tool sadece belirli bir destek kaydını okur."
    },

    "update_ticket_status": {
    "requires_confirmation": True,
    "reason": "Bu tool destek kaydının durumunu günceller."
    }
}


APPROVE_WORDS = [
    "evet",
    "tamam",
    "onaylıyorum",
    "olur",
    "kabul",
    "devam et"
]


REJECT_WORDS = [
    "hayır",
    "hayir",
    "iptal",
    "vazgeç",
    "vazgec",
    "istemiyorum"
]


def tool_requires_confirmation(tool_name: str) -> bool:
    """
    Tool'un confirmation gerektirip gerektirmediğini döndürür.
    """

    tool_policy = RISKY_TOOLS.get(tool_name)

    if not tool_policy:
        return True

    return tool_policy.get("requires_confirmation", True)


def detect_confirmation_intent(message: str) -> str:
    """
    Kullanıcı mesajının onay mı, red mi, yoksa belirsiz mi olduğunu anlar.

    Gerçek projelerde kullanıcı sadece 'evet' yazmaz.
    Örnek:
    - evet yapalım
    - tamam aç
    - olur devam et
    - hayır gerek yok
    - iptal edelim
    """

    normalized_message = message.lower().strip()

    reject_phrases = [
        "hayır",
        "hayir",
        "iptal",
        "vazgeç",
        "vazgec",
        "istemiyorum",
        "gerek yok",
        "oluşturma",
        "acma",
        "açma"
    ]

    approve_phrases = [
        "evet",
        "tamam",
        "onaylıyorum",
        "olur",
        "kabul",
        "devam et",
        "yapalım",
        "yapalim",
        "aç",
        "ac",
        "oluştur",
        "olustur"
    ]

    for phrase in reject_phrases:
        if phrase in normalized_message:
            return "reject"

    for phrase in approve_phrases:
        if phrase in normalized_message:
            return "approve"

    return "unknown"



def validate_decision(decision: dict, user_message: str) -> dict:
    """
    LLM kararını backend tarafında güvenli hale getirir.

    LLM tool seçebilir ama sistem son kararı burada kontrol eder.
    """

    allowed_tools = [
        "get_user_info",
        "create_ticket",
        "search_documents",
        "list_tickets",
        "get_ticket_detail",
        "update_ticket_status",
        None
    ]

    tool_name = decision.get("tool_name")
    arguments = decision.get("arguments", {})

    if tool_name not in allowed_tools:
        return {
            "tool_name": None,
            "arguments": {},
            "error": f"Bilinmeyen tool: {tool_name}"
        }

    if tool_name is None:
        return {
            "tool_name": None,
            "arguments": {}
        }

    if tool_name == "get_user_info":
        return {
            "tool_name": "get_user_info",
            "arguments": {
                "user_id": arguments.get("user_id") or "demo_user"
            }
        }

    if tool_name == "search_documents":
        return {
            "tool_name": "search_documents",
            "arguments": {
                "question": arguments.get("question") or user_message
            }
        }

    if tool_name == "list_tickets":
        limit = arguments.get("limit") or 10

        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10

        if limit < 1:
            limit = 10

        if limit > 50:
            limit = 50

        return {
            "tool_name": "list_tickets",
            "arguments": {
                "limit": limit
            }
        }

    if tool_name == "get_ticket_detail":
        ticket_id = arguments.get("ticket_id")

        if not ticket_id:
            return {
                "tool_name": None,
                "arguments": {},
                "error": "Ticket detayı için ticket_id gereklidir."
            }

        return {
            "tool_name": "get_ticket_detail",
            "arguments": {
                "ticket_id": ticket_id
            }
        }


    if tool_name == "update_ticket_status":
        ticket_id = arguments.get("ticket_id")
        status = arguments.get("status")

        allowed_statuses = ["open", "pending", "closed"]

        if not ticket_id:
            return {
                "tool_name": None,
                "arguments": {},
                "error": "Ticket durumu güncellemek için ticket_id gereklidir."
            }

        if not status:
            return {
                "tool_name": None,
                "arguments": {},
                "error": "Ticket durumu güncellemek için status gereklidir."
            }

        status = status.lower().strip()

        if status not in allowed_statuses:
            return {
                "tool_name": None,
                "arguments": {},
                "error": f"Geçersiz ticket durumu: {status}"
            }

        return {
            "tool_name": "update_ticket_status",
            "arguments": {
                "ticket_id": ticket_id,
                "status": status
            }
        }


    if tool_name == "create_ticket":

        title = arguments.get("title")
        description = arguments.get("description")

        # LLM'in oluşturduğu parametreleri doğrula.
        if not isinstance(title, str) or not title.strip():
            return {
                "tool_name": None,
                "arguments": {},
                "error": "Destek talebi için geçerli bir başlık gereklidir."
            }

        if not isinstance(description, str) or not description.strip():
            return {
                "tool_name": None,
                "arguments": {},
                "error": "Destek talebi için geçerli bir açıklama gereklidir."
            }

        return {
            "tool_name": "create_ticket",
            "arguments": {
                "title": title.strip()[:200],
                "description": user_message.strip()
            }
        }

    return {
        "tool_name": None,
        "arguments": {}
    }
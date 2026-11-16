
import requests
from app.mcp.services.rag_client import ask_rag
from mcp.server import MCPServer
from app.repositories.ticket_repository import (
    create_ticket_record,
    list_ticket_records,
    get_ticket_record,
    update_ticket_status_record
)
from app.mcp.services.ticket_classifier import classify_ticket

mcp = MCPServer("helpdesk-mcp-server")


@mcp.tool()
def get_user_info(user_id: str) -> dict:
    """
    Kullanıcı bilgilerini getirir.
    """

    return {
        "user_id": user_id,
        "name": "Demo User",
        "tenant_id": "firma_a",
        "role": "employee"
    }


@mcp.tool()
def create_ticket(title: str, description: str) -> dict:
    """
    IT destek talebini AI ile sınıflandırır
    ve PostgreSQL'e kaydeder.
    """

    # 1. LLM ile ticket sınıflandırması
    classification = classify_ticket(description)

    # 2. Doğrulanmış kategori ve önceliği al
    category = classification.category
    priority = classification.priority

    # 3. PostgreSQL'e kaydet
    return create_ticket_record(
        title=classification.title,
        description=description,
        category=category,
        priority=priority
    )

@mcp.tool()
def search_documents(question: str) -> dict:
    """
    Yerel RAG sistemi üzerinden IT destek dokümanlarında arama yapar.
    """

    result = ask_rag(question)

    return {
        "question": result.get("question"),
        "answer": result.get("answer"),
        "selected_category": result.get("selected_category"),
        "category_filters": result.get("category_filters", []),

        "knowledge_gap": result.get("knowledge_gap", False),
        "knowledge_gap_reason": result.get("knowledge_gap_reason"),
        "top_rerank_score": result.get("top_rerank_score"),

        "sources": [
            {
                "title": item.get("title"),
                "category": item.get("category"),
                "source": item.get("source"),
                "chunk_index": item.get("chunk_index"),
                "rerank_score": item.get("rerank_score"),
                "distance": item.get("distance")
            }
            for item in result.get("sources", [])
        ] if not result.get("knowledge_gap") else []
    }


@mcp.tool()
def list_tickets(limit: int = 10) -> dict:
    """
    PostgreSQL'den son destek kayıtlarını listeler.
    """

    tickets = list_ticket_records(limit=limit)

    return {
        "count": len(tickets),
        "tickets": tickets
    }



@mcp.tool()
def get_ticket_detail(ticket_id: str) -> dict:
    """
    PostgreSQL'den belirli bir destek kaydının detayını getirir.
    """

    ticket = get_ticket_record(ticket_id=ticket_id)

    if not ticket:
        return {
            "found": False,
            "message": f"{ticket_id} kodlu destek kaydı bulunamadı."
        }

    return {
        "found": True,
        "ticket": ticket
    }

@mcp.tool()
def update_ticket_status(ticket_id: str, status: str) -> dict:
    """
    PostgreSQL'de belirli bir destek kaydının durumunu günceller.
    """

    updated_ticket = update_ticket_status_record(
        ticket_id=ticket_id,
        status=status
    )

    if not updated_ticket:
        return {
            "updated": False,
            "message": f"{ticket_id} kodlu destek kaydı bulunamadı."
        }

    return {
        "updated": True,
        "ticket": updated_ticket
    }


if __name__ == "__main__":
    mcp.run()
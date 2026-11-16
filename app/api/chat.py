import os
import requests

from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    UploadFile,
    File
)

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.mcp.llm_mcp_agent import (
    run_llm_mcp_agent,
    execute_pending_action
)

from app.repositories.session_repository import (
    create_session_record,
    session_exists,
    get_all_sessions
)

from app.repositories.message_repository import (
    create_message_record,
    get_session_messages
)

from app.repositories.pending_action_repository import (
    create_pending_action_record,
    get_pending_action_record,
    claim_pending_action_record,
    update_pending_action_status
)

from app.mcp.services.document_client import upload_document_to_rag


router = APIRouter()



templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    session_id: UUID
    message: str


class ActionRequest(BaseModel):
    session_id: UUID

@router.get("/")
def home():
    return {"message": "MCP Helpdesk API çalışıyor!"}


@router.post("/chat")
async def chat(request: ChatRequest):

    session_id = str(request.session_id)

    # 1. Sohbet oturumu var mı?
    if not session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="Sohbet oturumu bulunamadı."
        )


    # Bu sohbette onay bekleyen işlem var mı?
    pending_action = get_pending_action_record(session_id)

    if pending_action is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Bu sohbette onay bekleyen bir işlem bulunuyor. "
                "Yeni mesaj göndermeden önce işlemi onaylayın veya iptal edin."
            )
    )

    # 2. Kullanıcı mesajını kaydet
    create_message_record(
        session_id=session_id,
        role="user",
        content=request.message
    )

    # 3. AI Agent'ı çalıştır
    result = await run_llm_mcp_agent(request.message)

    # 4. Agent cevabını belirle
    if result.get("requires_confirmation"):

    # Agent'ın hazırladığı işlemi al
        pending_action = result.get("pending_action")

        # PostgreSQL'e kaydet
        action_id = create_pending_action_record(
            session_id=session_id,
            action_data=pending_action
        )

    # Kullanıcıya onay mesajını hazırla
        answer = result.get("confirmation_message")

    else:
        action_id = None

        answer = (
            result.get("final_answer")
            or result.get("answer")
            or "Cevap üretilemedi."
        )
    # 5. Agent cevabını kaydet
    create_message_record(
        session_id=session_id,
        role="assistant",
        content=answer
    )

    # 6. Kullanıcıya cevap gönder
    return {
        "answer": answer,
        "requires_confirmation": bool(
            result.get("requires_confirmation")
        ),
        "pending_action_id": action_id
}


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: UUID):

    if not session_exists(str(session_id)):
        raise HTTPException(
            status_code=404,
            detail="Sohbet oturumu bulunamadı."
        )

    messages = get_session_messages(str(session_id))

    return {
        "session_id": str(session_id),
        "messages": messages
    }



@router.post("/sessions")
def create_session():

    session_id = create_session_record()

    return {
        "session_id": session_id
    }


@router.post("/actions/{action_id}/approve")
async def approve_action(action_id: int, request: ActionRequest):

    session_id = str(request.session_id)

    if not session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="Sohbet oturumu bulunamadı."
        )

    # 1. Bekleyen işlemi yalnızca bir kez başlat
    pending_action = claim_pending_action_record(
        action_id=action_id,
        session_id=session_id
    )

    if pending_action is None:
        raise HTTPException(
            status_code=409,
            detail="İşlem bulunamadı, süresi doldu veya daha önce işlendi."
        )

    # 2. Gerçek MCP aracını çalıştır
    try:
        result = await execute_pending_action(
            pending_action["action_data"]
        )

        if result.get("error"):
            update_pending_action_status(
                action_id,
                "processing",
                "failed"
            )

            answer = result.get("final_answer") or "İşlem başarısız oldu."

        else:
            update_pending_action_status(
                action_id,
                "processing",
                "completed"
            )

            answer = result.get("final_answer") or "İşlem tamamlandı."

    except Exception:
        update_pending_action_status(
            action_id,
            "processing",
            "failed"
        )
        answer = "İşlem sırasında beklenmeyen bir hata oluştu."

    # 3. Agent cevabını sohbet geçmişine kaydet
    create_message_record(
        session_id=session_id,
        role="assistant",
        content=answer
    )

    return {
        "answer": answer
    }



@router.post("/actions/{action_id}/cancel")
def cancel_action(action_id: int, request: ActionRequest):

    session_id = str(request.session_id)

    if not session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="Sohbet oturumu bulunamadı."
        )

    # İşlemin bu oturuma ait olduğunu ve hâlâ beklediğini kontrol et
    pending_action = get_pending_action_record(session_id)

    if pending_action is None or pending_action["id"] != action_id:
        raise HTTPException(
            status_code=409,
            detail="İptal edilebilecek bekleyen işlem bulunamadı."
        )

    # İşlemi iptal et
    cancelled = update_pending_action_status(
        action_id,
        "pending",
        "cancelled"
    )

    if not cancelled:
        raise HTTPException(
            status_code=409,
            detail="İşlem daha önce tamamlanmış veya iptal edilmiş."
        )

    answer = "İşlem iptal edildi. Destek kaydı oluşturulmadı."

    create_message_record(
        session_id=session_id,
        role="assistant",
        content=answer
    )

    return {
        "answer": answer,
        "status": "cancelled"
    }


@router.get("/chat-ui", response_class=HTMLResponse)
def chat_ui(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )




@router.get("/sessions")
def list_sessions():

    sessions = get_all_sessions()

    return {
        "sessions": sessions
    }



@router.get("/sessions/{session_id}/pending-action")
def get_session_pending_action(session_id: UUID):

    # 1. Sohbet mevcut mu?
    if not session_exists(str(session_id)):
        raise HTTPException(
            status_code=404,
            detail="Sohbet oturumu bulunamadı."
        )

    # 2. PostgreSQL'den bekleyen işlemi getir
    pending_action = get_pending_action_record(str(session_id))

    # 3. Bekleyen işlem yoksa
    if pending_action is None:
        return {
            "has_pending_action": False,
            "pending_action_id": None
        }

    # 4. Bekleyen işlem varsa
    return {
        "has_pending_action": True,
        "pending_action_id": pending_action["id"]
    }

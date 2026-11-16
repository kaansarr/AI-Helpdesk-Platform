import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.workflow_client import trigger_document_workflow
from app.ingestion.ingestion_service import ingest_document


router = APIRouter(tags=["Documents"])

templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.get("/documents-ui", response_class=HTMLResponse)
def documents_ui(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="documents.html"
    )


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Yalnızca PDF, TXT ve DOCX dosyaları yüklenebilir."
        )

    stored_filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / stored_filename
    file_size = 0

    try:
        with file_path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Dosya boyutu 10 MB sınırını aşıyor."
                    )

                output.write(chunk)

    except Exception:
        file_path.unlink(missing_ok=True)
        raise

    finally:
        await file.close()

    try:
        trigger_document_workflow(stored_filename)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Dosya kaydedildi ancak n8n tetiklenemedi: {error}"
        )

    return {
        "success": True,
        "filename": filename,
        "stored_filename": stored_filename,
        "file_type": extension.lstrip("."),
        "file_size": file_size,
        "message": "Dosya yüklendi ve işleme süreci başlatıldı."
    }


@router.post("/documents/process")
def process_document(stored_filename: str):

    if not re.fullmatch(
        r"[0-9a-f]{32}\.(pdf|txt|docx)",
        stored_filename
    ):
        raise HTTPException(
            status_code=400,
            detail="Geçersiz dosya adı."
        )

    file_path = UPLOAD_DIR / stored_filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Dosya bulunamadı."
        )

    return ingest_document(file_path)
import hashlib
from pathlib import Path

from app.ingestion.document_loader import load_uploaded_document
from app.ingestion.chunker import create_chunks_from_document

from app.core.embeddings import embed_text

from app.repositories.document_repository import (
    create_document_record,
    get_document_by_hash,
    update_document_status
)

from app.repositories.document_chunk_repository import (
    create_document_chunk_record
)


def ingest_document(file_path: Path) -> dict:

    # 1. Dosya mevcut mu?
    if not file_path.is_file():
        raise FileNotFoundError("Dosya bulunamadı.")

    # 2. Dosyanın hash değerini hesapla
    file_hash = hashlib.sha256(
        file_path.read_bytes()
    ).hexdigest()

    # 3. Aynı dosya daha önce yüklenmiş mi?
    existing_document = get_document_by_hash(file_hash)

    if existing_document:
        return {
            "success": False,
            "message": "Bu doküman daha önce yüklenmiş.",
            "document_id": existing_document["id"],
            "status": existing_document["status"]
        }

    # 4. Dosyayı veritabanına kaydet
    document_id = create_document_record(
        filename=file_path.name,
        file_type=file_path.suffix.lower().lstrip("."),
        file_hash=file_hash,
        file_path=str(file_path)
    )

    # 5. İşlem başladı
    update_document_status(document_id, "processing")

    try:

        # 6. Dosyadan metin çıkar
        document = load_uploaded_document(file_path)

        # 7. Metni chunk'lara ayır
        chunks = create_chunks_from_document(document)

        if not chunks:
            raise ValueError("Dokümandan chunk oluşturulamadı.")

        print("Toplam chunk:", len(chunks))

        # 8. Embedding oluştur ve kaydet
        for chunk in chunks:

            embedding = embed_text(chunk["content"])

            create_document_chunk_record(
                document_id=document_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding=embedding
            )

        # 9. İşlem başarıyla tamamlandı
        update_document_status(document_id, "completed")

        return {
            "success": True,
            "document_id": document_id,
            "filename": file_path.name,
            "chunk_count": len(chunks),
            "status": "completed"
        }

    except Exception as error:

        update_document_status(
            document_id,
            "failed",
            str(error)
        )

        raise
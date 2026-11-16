from app.ingestion.chunker import create_chunks_from_documents
from app.core.embeddings import embed_text
from app.core.db import get_connection


def embedding_to_pgvector(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


def clear_old_chunks():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM helpdesk_chunks;")
            conn.commit()

    print("Eski chunk kayıtları temizlendi.")


def build_index():
    clear_old_chunks()

    chunks = create_chunks_from_documents()


    print("Toplam chunk sayısı:", len(chunks))

    with get_connection() as conn:
        with conn.cursor() as cur:
            for index, chunk in enumerate(chunks):
                print(f"Embedding oluşturuluyor ve kaydediliyor: {index + 1}/{len(chunks)}")

                embedding = embed_text(chunk["content"])
                embedding_vector = embedding_to_pgvector(embedding)

                cur.execute(
                    """
                    INSERT INTO helpdesk_chunks (
                        source,
                        title,
                        category,
                        chunk_index,
                        content,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::vector);
                    """,
                    (
                        chunk["source"],
                        chunk["title"],
                        chunk["category"],
                        chunk["chunk_index"],
                        chunk["content"],
                        embedding_vector
                    )
                )

            conn.commit()

    print("Helpdesk RAG index oluşturuldu.")


if __name__ == "__main__":
    build_index()
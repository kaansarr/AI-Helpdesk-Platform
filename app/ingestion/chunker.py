from app.ingestion.document_loader import load_knowledge_base_documents


def split_text_into_paragraphs(text: str) -> list[str]:
    paragraphs = []

    raw_paragraphs = text.split("\n\n")

    for paragraph in raw_paragraphs:
        cleaned_paragraph = " ".join(paragraph.split())

        if cleaned_paragraph:
            paragraphs.append(cleaned_paragraph)

    return paragraphs


def get_word_overlap(text: str, overlap_word_count: int = 25) -> str:
    words = text.split()

    if len(words) <= overlap_word_count:
        return text

    return " ".join(words[-overlap_word_count:])


def split_text_into_chunks(
    text: str,
    chunk_size: int = 900,
    overlap_word_count: int = 25
) -> list[str]:
    paragraphs = split_text_into_paragraphs(text)

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        new_length = len(current_chunk) + len(paragraph) + 1

        if new_length <= chunk_size:
            current_chunk = f"{current_chunk} {paragraph}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)

            overlap_text = get_word_overlap(
                text=current_chunk,
                overlap_word_count=overlap_word_count
            )

            current_chunk = f"{overlap_text} {paragraph}".strip()

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def create_chunks_from_document(document: dict) -> list[dict]:

    text_chunks = split_text_into_chunks(
        text=document["content"],
        chunk_size=900,
        overlap_word_count=25
    )

    chunks = []

    for index, chunk_text in enumerate(text_chunks):

        chunk = {
            "source": document["source"],
            "title": document["title"],
            "category": document["category"],
            "chunk_index": index,
            "content": chunk_text
        }

        chunks.append(chunk)

    return chunks



def create_chunks_from_documents() -> list[dict]:

    documents = load_knowledge_base_documents()

    all_chunks = []

    for document in documents:

        chunks = create_chunks_from_document(document)

        all_chunks.extend(chunks)

    return all_chunks

if __name__ == "__main__":
    chunks = create_chunks_from_documents()

    print("Toplam chunk sayısı:", len(chunks))
    print("-" * 50)

    for chunk in chunks[:10]:
        print("Kaynak:", chunk["source"])
        print("Başlık:", chunk["title"])
        print("Kategori:", chunk["category"])
        print("Chunk Index:", chunk["chunk_index"])
        print("İçerik:")
        print(chunk["content"][:700])
        print("-" * 50)
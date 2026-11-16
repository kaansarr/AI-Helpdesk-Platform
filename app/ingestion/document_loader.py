from pathlib import Path
import pymupdf
from docx import Document


KNOWLEDGE_BASE_PATH = Path("data/knowledge_base")


def extract_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.replace("# ", "").strip()

    return "Başlık bulunamadı"


def extract_category(text: str) -> str:
    lines = text.splitlines()

    for index, line in enumerate(lines):
        if line.strip() == "## Kategori":
            if index + 1 < len(lines):
                return lines[index + 1].strip()

    return "Kategori bulunamadı"


def load_markdown_file(file_path: Path) -> dict:
    text = file_path.read_text(encoding="utf-8")

    document = {
        "source": str(file_path),
        "title": extract_title(text),
        "category": extract_category(text),
        "content": text
    }

    return document


def load_knowledge_base_documents() -> list[dict]:
    documents = []

    markdown_files = sorted(KNOWLEDGE_BASE_PATH.glob("*.md"))

    for file_path in markdown_files:
        document = load_markdown_file(file_path)
        documents.append(document)

    return documents



def load_uploaded_document(file_path: Path) -> dict:

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        with pymupdf.open(file_path) as pdf:
            text = "\n".join(page.get_text() for page in pdf)

    elif extension == ".docx":
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)

    elif extension == ".txt":
        text = file_path.read_text(encoding="utf-8-sig")

    else:
        raise ValueError("Desteklenmeyen dosya formatı.")

    if not text.strip():
        raise ValueError("Dokümandan metin çıkarılamadı.")

    return {
        "source": str(file_path),
        "title": file_path.stem,
        "category": "Yüklenen Doküman",
        "content": text
    }


if __name__ == "__main__":
    documents = load_knowledge_base_documents()

    print("Toplam doküman sayısı:", len(documents))
    print("-" * 50)

    for document in documents:
        print("Kaynak:", document["source"])
        print("Başlık:", document["title"])
        print("Kategori:", document["category"])
        print("Karakter sayısı:", len(document["content"]))
        print("-" * 50)
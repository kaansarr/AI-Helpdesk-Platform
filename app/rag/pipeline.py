from app.rag.search import search_with_router_and_rerank
from app.rag.reranker import Reranker
from app.core.llm import generate_answer


def build_context(chunks: list[dict]) -> str:
    context_parts = []

    for chunk in chunks:
        context_parts.append(
            f"""
Başlık: {chunk["title"]}
Kategori: {chunk["category"]}
Destek bilgisi:
{chunk["content"]}
"""
        )

    return "\n---\n".join(context_parts)


def build_system_prompt() -> str:
    return """
Sen Türkçe cevap veren bir şirket içi IT destek asistanısın.
Sadece verilen destek bilgilerini kullan.
Cevabı kısa ve madde madde yaz.
Kullanıcı sorusunu tekrar etme.
Giriş cümlesi, başlık, kaynak etiketi veya açıklama yazma.
Kullanıcıya soru sorma.
Son maddede, sorun devam ederse IT destek talebi açılabileceğini belirt.
"""

def build_user_prompt(question: str, context: str) -> str:
    return f"""
Destek bilgileri:
{context}

Kullanıcı sorusu:
{question}

Yalnızca cevabı yaz.
"""

def clean_answer(answer: str, question: str | None = None) -> str:
    unwanted_line_starts = [
        "Kullanıcı sorusunu",
        "Giriş cümlesi",
        "Giriş:",
        "Yapılacak işlemler",
        "Son madde",
        "IT destek talebi açma yönlendirmesi",
        "Kaynak:",
        "KAYNAK",
        "[KAYNAK",
        "(KAYNAK",
        "Here is",
        "Not:",
        "Sonuç:",
        "Merhaba",
        "Sorununuza yardımcı olalım",
        "Sorun devam ederse, IT destek talebi açılabileceğini belirtelim",
        "Sorun devam ederse IT destek talebi açılabileceğini belirtelim",
    ]

    lines = answer.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped_line = line.strip()

        if not stripped_line:
            continue

        if question and stripped_line == question.strip():
            continue

        should_skip = False

        for start_text in unwanted_line_starts:
            if stripped_line.startswith(start_text):
                should_skip = True
                break

        if should_skip:
            continue

        cleaned_lines.append(stripped_line)

    cleaned_answer = "\n".join(cleaned_lines).strip()

    replacements = {
        "Eğer sorun devam ederse, IT destek birimine bildirilmelidir.": "Sorun devam ederse IT destek talebi açabilirsiniz.",
        "Eğer sorun devam ederse IT destek birimine bildirilmelidir.": "Sorun devam ederse IT destek talebi açabilirsiniz.",
        "Sorun devam ederse IT destek birimine bildirilmelidir.": "Sorun devam ederse IT destek talebi açabilirsiniz.",
        "Sorun devam ederse IT destek talebi açılabilir.": "Sorun devam ederse IT destek talebi açabilirsiniz.",
        "Sorun devam ederse IT destek talebi açılmalıdır.": "Sorun devam ederse IT destek talebi açabilirsiniz.",
        "IT destek talebi açılması gerekiyorsa, IT ekibine bildirilmelidir.": "Sorun devam ederse IT destek talebi açabilirsiniz.",
        "Eğer sorun devam ederse, IT destek talebi açılması gerekebilir.": "Sorun devam ederse IT destek talebi açabilirsiniz.",
        "Sorun devam ederse IT destek talebi açılması gerekebilir.": "Sorun devam ederse IT destek talebi açabilirsiniz.",
    }

    for old_text, new_text in replacements.items():
        cleaned_answer = cleaned_answer.replace(old_text, new_text)

    final_sentence = "Sorun devam ederse IT destek talebi açabilirsiniz."

    while cleaned_answer.count(final_sentence) > 1:
        cleaned_answer = cleaned_answer.replace(final_sentence, "", 1).strip()

    if final_sentence not in cleaned_answer:
        cleaned_answer = cleaned_answer.rstrip(".")
        cleaned_answer = cleaned_answer + ".\n" + final_sentence

    return cleaned_answer


def answer_question(
    question: str,
    reranker: Reranker,
    candidate_top_k: int = 10,
    final_top_k: int = 5
) -> dict:
    search_output = search_with_router_and_rerank(
        query=question,
        reranker=reranker,
        candidate_top_k=candidate_top_k,
        final_top_k=final_top_k
    )

    chunks = search_output["reranked_results"]
        # RAG hiçbir kaynak bulamadıysa cevap uydurmasını engelle.
        # En yüksek reranker skorunu bul.
    top_score = max(
        (chunk["rerank_score"] for chunk in chunks),
        default=None
    )

    # Deneysel eşik: mevcut test sonuçlarına göre belirlendi.
    KNOWLEDGE_GAP_THRESHOLD = 0.10

    # Kaynak yoksa veya bulunan kaynakların ilişkisi çok düşükse
    # olası bilgi eksikliği olarak işaretle.
    if not chunks or top_score < KNOWLEDGE_GAP_THRESHOLD:

        reason = (
            "no_documents_found"
            if not chunks
            else "low_relevance"
        )

        return {
            "question": question,
            "answer": (
                "Bu soruyla ilgili bilgi tabanında yeterli kaynak bulunamadı. "
                "Konunun IT ekibi tarafından incelenmesi gerekiyor."
            ),
            "search_output": search_output,
            "context": "",
            "system_prompt": "",
            "user_prompt": "",
            "knowledge_gap": True,
            "knowledge_gap_reason": reason,
            "top_rerank_score": top_score
        }

    context = build_context(chunks)

    system_prompt = build_system_prompt()

    user_prompt = build_user_prompt(
        question=question,
        context=context
    )

    answer = generate_answer(
        user_prompt=user_prompt,
        system_prompt=system_prompt
    )

    answer = clean_answer(answer, question=question)

    return {
            "question": question,
            "answer": answer,
            "search_output": search_output,
            "context": context,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "knowledge_gap": False,
            "knowledge_gap_reason": None,
            "top_rerank_score": top_score
    }


if __name__ == "__main__":
    reranker = Reranker()

    test_questions = [
        "VPN bağlanmıyor ne yapmalıyım?",
        "Mail hesabım telefonda senkronize olmuyor.",
        "Yazıcıdan çıktı alamıyorum.",
        "Laptopum çok yavaşladı.",
        "Evdeyken şirket uygulamalarına giremiyorum."
    ]

    for question in test_questions:
        result = answer_question(
            question=question,
            reranker=reranker,
            candidate_top_k=10,
            final_top_k=5
        )

        print("Soru:")
        print(result["question"])
        print("-" * 50)

        print("Cevap:")
        print(result["answer"])
        print("-" * 50)

        print("Kullanılan kaynaklar:")
        for chunk in result["search_output"]["reranked_results"]:
            print(
                "-",
                chunk["title"],
                "|",
                chunk["category"],
                "| rerank:",
                round(chunk["rerank_score"], 4)
            )

        print("=" * 80)
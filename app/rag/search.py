from app.repositories.search_repository import (
    search_old_chunks,
    search_uploaded_chunks
)
from app.core.embeddings import embed_text
from app.rag.semantic_router import route_query_to_category
from app.rag.reranker import Reranker


def embedding_to_pgvector(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


def search_similar_chunks(
    query: str,
    top_k: int = 10,
    category_filters: list[str] | None = None
) -> list[dict]:

    # Kullanıcı sorusunun embedding'ini oluştur.
    query_embedding = embed_text(query)
    query_vector = embedding_to_pgvector(query_embedding)

    # Eski bilgi tabanında ara.
    old_results = search_old_chunks(
        query_vector=query_vector,
        top_k=top_k,
        category_filters=category_filters
    )

    # Kullanıcının yüklediği dokümanlarda ara.
    uploaded_results = search_uploaded_chunks(
        query_vector=query_vector,
        top_k=top_k
    )

    # İki kaynaktan gelen sonuçları birleştir.
    results = old_results + uploaded_results

    # En benzer chunk'lar önce gelsin.
    results.sort(key=lambda item: item["distance"])

    return results[:top_k]

def decide_category_filters(
    selected_category: str | None,
    router_score: float,
    scored_categories: list[dict],
    fallback_score_threshold: float = 0.75,
    fallback_top_n: int = 2
) -> list[str] | None:
    if selected_category:
        return [selected_category]

    if router_score >= fallback_score_threshold:
        top_categories = []

        for item in scored_categories[:fallback_top_n]:
            top_categories.append(item["name"])

        return top_categories

    return None


def search_with_router(
    query: str,
    candidate_top_k: int = 10
) -> dict:
    selected_category, router_score, scored_categories = route_query_to_category(query)

    category_filters = decide_category_filters(
        selected_category=selected_category,
        router_score=router_score,
        scored_categories=scored_categories,
        fallback_score_threshold=0.75,
        fallback_top_n=2
    )

    results = search_similar_chunks(
        query=query,
        top_k=candidate_top_k,
        category_filters=category_filters
    )

    return {
        "query": query,
        "selected_category": selected_category,
        "router_score": router_score,
        "category_filters": category_filters,
        "scored_categories": scored_categories,
        "results": results
    }


def search_with_router_and_rerank(
    query: str,
    reranker: Reranker,
    candidate_top_k: int = 10,
    final_top_k: int = 5
) -> dict:
    search_output = search_with_router(
        query=query,
        candidate_top_k=candidate_top_k
    )

    reranked_results = reranker.rerank(
        query=query,
        results=search_output["results"],
        top_k=final_top_k
    )

    search_output["reranked_results"] = reranked_results

    return search_output


if __name__ == "__main__":
    test_questions = [
        "VPN bağlanmıyor ne yapmalıyım?",
        "VPN sürekli hata veriyor ve bağlanamıyorum.",
        "Mail hesabım telefonda senkronize olmuyor.",
        "Yazıcıdan çıktı alamıyorum.",
        "Laptopum çok yavaşladı.",
        "Evdeyken şirket uygulamalarına giremiyorum."
    ]

    reranker = Reranker()

    for question in test_questions:
        search_output = search_with_router_and_rerank(
            query=question,
            reranker=reranker,
            candidate_top_k=10,
            final_top_k=5
        )

        print("Soru:", search_output["query"])
        print("Router seçimi:", search_output["selected_category"])
        print("Router skoru:", search_output["router_score"])
        print("Aranacak kategoriler:", search_output["category_filters"])
        print("-" * 50)

        print("RERANK SONRASI SONUÇLAR")
        print("-" * 50)

        for result in search_output["reranked_results"]:
            print("ID:", result["id"])
            print("Başlık:", result["title"])
            print("Kategori:", result["category"])
            print("Chunk Index:", result["chunk_index"])
            print("Vector Distance:", result["distance"])
            print("Rerank Score:", result["rerank_score"])
            print("İçerik:")
            print(result["content"][:500])
            print("-" * 50)

        print("=" * 80)
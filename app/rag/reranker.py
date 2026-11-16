from sentence_transformers import CrossEncoder


RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"


class Reranker:
    def __init__(self, model_name: str = RERANKER_MODEL_NAME):
        print("Reranker modeli yükleniyor:", model_name)

        self.model = CrossEncoder(
            model_name,
            max_length=512
        )

        print("Reranker modeli hazır.")

    def rerank(
        self,
        query: str,
        results: list[dict],
        top_k: int = 5
    ) -> list[dict]:
        if not results:
            return []

        pairs = []

        for result in results:
            pairs.append([
                query,
                result["content"]
            ])

        scores = self.model.predict(pairs)

        reranked_results = []

        for result, score in zip(results, scores):
            new_result = result.copy()
            new_result["rerank_score"] = float(score)
            reranked_results.append(new_result)

        reranked_results.sort(
            key=lambda item: item["rerank_score"],
            reverse=True
        )

        return reranked_results[:top_k]


if __name__ == "__main__":
    sample_query = "VPN bağlanmıyor ne yapmalıyım?"

    sample_results = [
        {
            "title": "VPN Kurulumu ve Bağlantı Sorunları",
            "category": "VPN ve Uzaktan Erişim",
            "content": "VPN bağlanmıyorsa internet bağlantısı, kullanıcı adı, şifre ve çok faktörlü doğrulama kontrol edilmelidir."
        },
        {
            "title": "Yazıcı Kurulumu ve Yazdırma Sorunları",
            "category": "Yazıcı ve Donanım",
            "content": "Yazıcı çıktı vermiyorsa kağıt, toner ve yazdırma kuyruğu kontrol edilmelidir."
        },
        {
            "title": "Şirket E-Posta Kurulumu",
            "category": "E-Posta ve İletişim",
            "content": "E-posta senkronizasyonu çalışmıyorsa internet bağlantısı ve hesap ayarları kontrol edilmelidir."
        }
    ]

    reranker = Reranker()

    results = reranker.rerank(
        query=sample_query,
        results=sample_results,
        top_k=3
    )

    print("Soru:", sample_query)
    print("-" * 50)

    for result in results:
        print("Başlık:", result["title"])
        print("Kategori:", result["category"])
        print("Rerank Score:", result["rerank_score"])
        print("İçerik:", result["content"])
        print("-" * 50)
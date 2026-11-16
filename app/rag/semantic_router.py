from math import sqrt

from app.core.embeddings import embed_text


CATEGORIES = [
    {
        "name": "VPN ve Uzaktan Erişim",
        "examples": [
            "VPN bağlanmıyor ne yapmalıyım?",
            "VPN açılmıyor.",
            "Evden şirket ağına bağlanamıyorum.",
            "Uzaktan erişim çalışmıyor.",
            "VPN bağlı ama şirket uygulamaları açılmıyor.",
            "MFA onayı gelmediği için VPN'e giremiyorum.",
            "VPN bağlantısı sürekli kopuyor.",
            "Şirket ağına dışarıdan erişemiyorum."
        ]
    },
    {
        "name": "Hesap ve Kimlik Doğrulama",
        "examples": [
            "Şifremi unuttum nasıl sıfırlarım?",
            "Hesabıma giriş yapamıyorum.",
            "Hesabım kilitlendi.",
            "Yeni şifrem kabul edilmiyor.",
            "Parolamı değiştirdim ama giriş yapamıyorum.",
            "Kullanıcı hesabım kilitli görünüyor.",
            "Oturum açarken hata alıyorum.",
            "Şifre sıfırlama bağlantısı gelmedi."
        ]
    },
    {
        "name": "E-Posta ve İletişim",
        "examples": [
            "Mail gönderemiyorum.",
            "Mail alamıyorum.",
            "Şirket e-postam telefonda çalışmıyor.",
            "E-posta hesabımı nasıl kurarım?",
            "Outlook mailleri senkronize etmiyor.",
            "Mail kutum güncellenmiyor.",
            "Telefonda şirket maili açılmıyor.",
            "E-posta ekleri açılmıyor."
        ]
    },
    {
        "name": "Yazıcı ve Donanım",
        "examples": [
            "Yazıcı çıktı vermiyor.",
            "Yazıcı çalışmıyor.",
            "Yazıcı ağda görünmüyor.",
            "Kağıt sıkıştı.",
            "Yazdırma kuyruğunda belge kaldı.",
            "Renkli çıktı alamıyorum.",
            "Yazıcıdan boş sayfa çıkıyor.",
            "Toner bitti uyarısı alıyorum."
        ]
    },
    {
        "name": "Ağ ve İnternet",
        "examples": [
            "İnternet bağlantım yok.",
            "Wi-Fi bağlanmıyor.",
            "Ağ bağlantısı sürekli kopuyor.",
            "Ethernet kablosu takılı ama internet yok.",
            "Şirket ağına bağlanamıyorum.",
            "İnternet çok yavaş.",
            "Kablosuz ağ görünmüyor.",
            "Web sitelerine erişemiyorum."
        ]
    },
    {
        "name": "Uzaktan Çalışma ve Destek",
        "examples": [
            "Evden çalışırken destek almam gerekiyor.",
            "Uzaktan destek talebi açmak istiyorum.",
            "Evden çalışırken sistemlere erişemiyorum.",
            "Uzaktan çalışma için hangi araçları kullanmalıyım?",
            "IT ekibi bilgisayarıma uzaktan bağlanabilir mi?",
            "Evden çalışırken bağlantı sorunu yaşıyorum.",
            "Uzaktan çalışma sırasında teknik sorun yaşıyorum.",
            "Remote çalışırken uygulamalar açılmıyor."
        ]
    },
    {
        "name": "Cihaz ve Donanım Yönetimi",
        "examples": [
            "Laptopum çok yavaşladı ne yapmalıyım?",
            "Bilgisayarım çok yavaş çalışıyor.",
            "Laptop geç açılıyor.",
            "Bilgisayarım donuyor.",
            "Uygulamalar çok yavaş açılıyor.",
            "Bilgisayar performans sorunu yaşıyorum.",
            "Laptop performansı düştü.",
            "Bilgisayarım kasıyor."
        ]
    },
    {
        "name": "Bilgi Güvenliği",
        "examples": [
            "Şüpheli bir mail aldım ne yapmalıyım?",
            "Phishing e-postası aldım.",
            "Şifremi yanlışlıkla biriyle paylaştım.",
            "Güvenlik ihlali olduğunu düşünüyorum.",
            "Bilinmeyen bir bağlantıya tıkladım.",
            "Cihazımı kaybettim ne yapmalıyım?",
            "Şirket verisini yanlış kişiye gönderdim.",
            "Şüpheli bir dosya açtım."
        ]
    },
    {
        "name": "Dosya Paylaşımı ve Yetkilendirme",
        "examples": [
            "Dosya klasörüne erişimim yok.",
            "Ortak klasöre giremiyorum.",
            "Paylaşılan dosyayı açamıyorum.",
            "Yetkim olmadığı için dosya açılmıyor.",
            "Dosya paylaşım bağlantısı çalışmıyor.",
            "Klasör yetkisi nasıl verilir?",
            "Erişim reddedildi hatası alıyorum.",
            "Dosyalar senkronize olmuyor."
        ]
    },
    {
        "name": "Toplantı ve İletişim Araçları",
        "examples": [
            "Toplantıda mikrofonum çalışmıyor.",
            "Teams toplantısına katılamıyorum.",
            "Kameram açılmıyor.",
            "Toplantıda ses gelmiyor.",
            "Mikrofon karşı tarafa gitmiyor.",
            "Online toplantı bağlantısı açılmıyor.",
            "Toplantıda görüntüm görünmüyor.",
            "Teams ses ayarlarını nasıl düzeltirim?"
        ]
    }
]


KEYWORD_HINTS = {
    "VPN ve Uzaktan Erişim": [
        "vpn",
        "uzaktan erişim",
        "dışarıdan erişim",
        "şirket ağına",
        "mfa",
        "çok faktörlü",
        "remote access"
    ],
    "Hesap ve Kimlik Doğrulama": [
        "şifre",
        "sifre",
        "parola",
        "hesap",
        "giriş",
        "oturum",
        "kilitlendi",
        "login"
    ],
    "E-Posta ve İletişim": [
        "mail",
        "e-posta",
        "eposta",
        "outlook",
        "posta",
        "gelen kutusu",
        "senkronize",
        "telefon"
    ],
    "Yazıcı ve Donanım": [
        "yazıcı",
        "yazici",
        "çıktı",
        "cikti",
        "yazdır",
        "toner",
        "kağıt",
        "kagit"
    ],
    "Ağ ve İnternet": [
        "internet",
        "wi-fi",
        "wifi",
        "ağ",
        "ag",
        "ethernet",
        "bağlantı",
        "baglanti",
        "kopuyor"
    ],
    "Uzaktan Çalışma ve Destek": [
        "evden",
        "uzaktan çalışma",
        "remote",
        "destek",
        "teknik destek"
    ],
    "Cihaz ve Donanım Yönetimi": [
        "bilgisayar",
        "laptop",
        "cihaz",
        "batarya",
        "ekran",
        "klavye",
        "mouse",
        "yavaş",
        "yavas"
    ],
    "Bilgi Güvenliği": [
        "şüpheli",
        "supheli",
        "phishing",
        "güvenlik",
        "guvenlik",
        "bilinmeyen bağlantı",
        "veri sızıntısı",
        "ihlal"
    ],
    "Dosya Paylaşımı ve Yetkilendirme": [
        "dosya",
        "klasör",
        "klasor",
        "yetki",
        "erişim izni",
        "paylaşım",
        "paylasim",
        "ortak klasör",
        "erişim reddedildi"
    ],
    "Toplantı ve İletişim Araçları": [
        "teams",
        "toplantı",
        "toplanti",
        "mikrofon",
        "kamera",
        "ses",
        "görüntü",
        "goruntu"
    ]
}

def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for a, b in zip(vector_a, vector_b):
        dot_product += a * b
        norm_a += a * a
        norm_b += b * b

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (sqrt(norm_a) * sqrt(norm_b))



def get_keyword_boost(query: str, category_name: str) -> float:
    query_lower = query.lower()

    keywords = KEYWORD_HINTS.get(category_name, [])

    matched_count = 0

    for keyword in keywords:
        if keyword in query_lower:
            matched_count += 1

    if matched_count == 0:
        return 0.0

    boost = matched_count * 0.06

    return min(boost, 0.18)

def score_category(
    query: str,
    query_embedding: list[float],
    category: dict
) -> dict:
    example_scores = []

    for example in category["examples"]:
        example_embedding = embed_text(example)
        score = cosine_similarity(query_embedding, example_embedding)

        example_scores.append({
            "example": example,
            "score": score
        })

    example_scores.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    best_example = example_scores[0]

    keyword_boost = get_keyword_boost(
        query=query,
        category_name=category["name"]
    )

    final_score = best_example["score"] + keyword_boost

    return {
        "name": category["name"],
        "score": final_score,
        "embedding_score": best_example["score"],
        "keyword_boost": keyword_boost,
        "best_example": best_example["example"],
        "example_scores": example_scores
    }


def route_query_to_category(
    query: str,
    min_confidence: float = 0.60,
    min_margin: float = 0.03
) -> tuple[str | None, float, list[dict]]:
    query_embedding = embed_text(query)

    scored_categories = []

    for category in CATEGORIES:
        scored_category = score_category(
            query=query,
            query_embedding=query_embedding,
            category=category
        )

        scored_categories.append(scored_category)

    scored_categories.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    best_category = scored_categories[0]
    second_best_category = scored_categories[1]

    best_score = best_category["score"]
    second_best_score = second_best_category["score"]
    margin = best_score - second_best_score

    if best_score < min_confidence:
        return None, best_score, scored_categories

    if margin < min_margin:
        return None, best_score, scored_categories

    return best_category["name"], best_score, scored_categories


if __name__ == "__main__":
    test_questions = [
    "VPN sürekli hata veriyor ve bağlanamıyorum.",
    "Evdeyken şirket uygulamalarına giremiyorum.",
    "Parolamı hatırlamıyorum, hesabıma nasıl girerim?",
    "Yazıcıdan çıktı alamıyorum.",
    "Teams toplantısında sesim karşı tarafa gitmiyor.",
    "Ortak klasöre erişim yetkim yok.",
    "Tanımadığım bir adresten şüpheli e-posta geldi.",
    "İnternet bağlantım sürekli kopuyor.",
    "Laptopum çok yavaşladı.",
    "Mail hesabım telefonda senkronize olmuyor."
    ]

    for question in test_questions:
        category, score, scored_categories = route_query_to_category(question)

        print("Soru:", question)
        print("Seçilen kategori:", category)
        print("Skor:", score)

        best = scored_categories[0]
        second = scored_categories[1]
        margin = best["score"] - second["score"]

        print("Margin:", margin)
        print("İlk 3 kategori:")

        for item in scored_categories[:3]:
           print(
            "-",
            item["name"],
            "| final score:",
            item["score"],
            "| embedding:",
            item["embedding_score"],
            "| boost:",
            item["keyword_boost"],
            "| best example:",
            item["best_example"]
        )

        print("-" * 50)
import os
import json

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

from app.repositories.daily_report_repository import get_daily_report_data


load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3:latest")

router = APIRouter(
    prefix="/reports",
    tags=["Daily IT Reports"]
)


@router.get("/daily")
def get_daily_report():
    return get_daily_report_data()


@router.get("/daily/ai")
def get_ai_daily_report():

    # 1. Gerçek verileri al
    data = get_daily_report_data()
    tickets = data["tickets"]
    gaps = data["knowledge_gaps"]

    # 2. Kesin istatistikleri Python ile oluştur
    report_lines = [
        f"GÜNLÜK IT OPERASYON RAPORU - {data['report_date']}",
        "",
        "1. GÜNLÜK OPERASYON ÖZETİ",
        f"Bugün oluşturulan destek talepleri: {tickets['created_today']}",
        f"Bugün kapatılan destek talepleri: {tickets['closed_today']}",
        "",
        "2. DESTEK TALEPLERİNİN MEVCUT DURUMU",
        f"Toplam açık talepler: {tickets['open_total']}",
        f"Toplam bekleyen talepler: {tickets['pending_total']}",
        f"Toplam kapalı talepler: {tickets['closed_total']}",
        "",
        "3. BİLGİ TABANINDAKİ EKSİKLİKLER",
        f"Bugün ilk kez tespit edilen bilgi eksikliği: {len(gaps)}"
    ]

    for gap in gaps:
        report_lines.append(
            f"- {gap['question']} "
            f"(Sebep: {gap['reason']}, "
            f"Toplam tespit: {gap['occurrence_count']})"
        )

    if not gaps:
        report_lines.append("Bugün yeni bilgi eksikliği tespit edilmedi.")

    # 3. Verilerle desteklenen öneri seçeneklerini hazırla
    available_suggestions = {}

    if gaps:
        available_suggestions["knowledge_gap"] = (
            "Tespit edilen bilgi eksiklikleri için doğrulanmış "
            "dokümanlar hazırlanarak bilgi tabanı güncellenmeli."
        )

    if tickets["open_total"] > 0:
        available_suggestions["open_tickets"] = (
            "Açık destek talepleri öncelik ve bekleme sürelerine "
            "göre gözden geçirilmeli."
        )

    if tickets["created_today"] > 0:
        available_suggestions["new_tickets"] = (
            "Yeni oluşturulan destek taleplerinin ilgili "
            "ekiplere yönlendirildiği kontrol edilmeli."
        )

    if tickets["pending_total"] > 0:
        available_suggestions["pending_tickets"] = (
            "Bekleyen destek taleplerinin ilerlemesi için "
            "gerekli bilgiler kontrol edilmeli."
        )

    # 4. Ollama yalnızca öneri kodlarını seçsin
    selected_codes = []

    if available_suggestions:

        prompt = f"""
Sen bir IT operasyon analistisin.

Aşağıdaki verileri değerlendirerek en önemli
3 önerinin kodunu seç.

MEVCUT VERİLER:
{json.dumps(data, ensure_ascii=False)}

SEÇİLEBİLİR ÖNERİ KODLARI:
{json.dumps(list(available_suggestions.keys()))}

KURALLAR:
- Sadece verilen kodları kullan.
- En fazla 3 farklı kod seç.
- Önem sırasına göre sırala.
- Açıklama veya ek metin yazma.

Yalnızca şu JSON biçiminde cevap ver:
{{"suggestions": ["kod1", "kod2"]}}
"""

        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "keep_alive": "10m",
                    "options": {
                        "temperature": 0,
                        "num_predict": 100
                    }
                },
                timeout=180
            )

            response.raise_for_status()

            result = json.loads(
                response.json().get("response", "{}")
            )

            codes = result.get("suggestions", [])

            if isinstance(codes, list):
                for code in codes:
                    if (
                        isinstance(code, str)
                        and code in available_suggestions
                        and code not in selected_codes
                    ):
                        selected_codes.append(code)

                    if len(selected_codes) == 3:
                        break

        except (requests.RequestException, ValueError, TypeError):
            # Model yanıtı geçersizse rapor yine oluşturulur.
            pass

        # Geçerli seçim yapılamazsa veri temelli önerilere dön
        if not selected_codes:
            selected_codes = list(available_suggestions.keys())[:3]

    # 5. Onaylanan önerileri Türkçe rapora ekle
    report_lines.extend([
        "",
        "4. YAPAY ZEKA DESTEKLİ ÖNERİLER"
    ])

    if selected_codes:
        for index, code in enumerate(selected_codes, start=1):
            report_lines.append(
                f"{index}. {available_suggestions[code]}"
            )
    else:
        report_lines.append(
            "Mevcut veriler için ek bir işlem önerisi bulunmuyor."
        )

    return {
        "report_date": data["report_date"],
        "model": LLM_MODEL,
        "report": "\n".join(report_lines)
    }
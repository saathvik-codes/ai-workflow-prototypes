from __future__ import annotations


def analyze(text: str) -> dict:
    t = text.lower()
    terms = [term for term in ["cicilan", "tenor", "denda", "dp", "jatuh tempo", "angsuran", "pembiayaan"] if term in t]
    if any(word in t.split() for word in ["halo", "hello", "hi"]):
        return _payload(text, "greeting", "bahasa_formal", terms, "Halo, saya bisa bantu soal cicilan, tenor, DP, jatuh tempo, denda, angsuran, atau pembiayaan.", "continue_finance_support", "The bot greets in Bahasa Indonesia and offers sector-specific finance help.")
    if "human" in t or "cs" in t or "customer service" in t:
        return _payload(text, "human_escalation", "bahasa_formal", terms, "Baik, saya alihkan ke agen manusia ya. Kalau perlu, nanti kami follow up lagi.", "handoff_to_cs", "The bot confirms handoff to a human customer-service agent in formal Bahasa Indonesia.")
    if "kulo" in t or "pripun" in t:
        return _payload(text, "regional_accent_payment_issue", "javanese_influenced_bahasa", terms, "Nggih, saya bantu arahkan ya. Kalau telat bayar cicilan dan ada denda, saya tidak akan mengarang; opsi resminya perlu dicek oleh tim.", "route_to_collections_support", "The bot recognizes Javanese-influenced wording, acknowledges late installment/payment penalty concerns, and routes to official support.")
    if "cicilan" in t or "tenor" in t or "jatuh tempo" in t or "dp" in t:
        return _payload(text, "installment_or_terms", "colloquial_bahasa", terms, "Saya bantu cek ya. Kita bisa bahas cicilan, tenor, DP, dan tanggal jatuh tempo dengan bahasa yang santai tapi tetap jelas.", "continue_installment_review", "The bot detects consumer-finance terms and continues in clear, colloquial Bahasa Indonesia.")
    if "collections" in t or "tagihan" in t or "penagihan" in t:
        return _payload(text, "collections_support", "bahasa_formal", terms, "Saya bantu arahkan ke tim bantuan pembayaran resmi agar penanganannya sesuai prosedur.", "route_to_collections_support", "The bot recognizes collections context and routes to approved support.")
    if "loan" in t and "overdue" in t:
        return _payload(text, "mixed_english_overdue", "colloquial_bahasa_with_english_loanword", terms, "Saya paham loan-nya overdue. Saya tidak akan mengarang status akun; saya bantu arahkan ke opsi follow-up resmi.", "offer_payment_support", "The bot handles English loanwords inside Bahasa context without switching into literal translation.")
    if "telat" in t or "denda" in t or "angsuran" in t or "besok" in t:
        return _payload(text, "late_payment_objection", "colloquial_bahasa", terms, "Kalau ada kendala angsuran atau denda, saya tidak mau mengarang. Saya bantu arahkan ke opsi bantuan resmi.", "offer_payment_support", "The bot handles late-payment or penalty concerns safely and points to approved payment-support options.")
    if "mau" in t and "cek" in t:
        return _payload(text, "check_request", "colloquial_bahasa", terms, "Siap, saya cek dulu ya. Kalau datanya belum lengkap, nanti saya minta tim follow up supaya tidak salah info.", "collect_missing_details", "The bot treats the turn as an account-check request and asks for follow-up when data is incomplete.")
    return _payload(text, "localized_fallback", "bahasa_formal", terms, "Maaf, saya belum yakin jawabannya dari knowledge yang tersedia, jadi saya lebih aman eskalasi ke tim manusia.", "handoff_to_cs", "The bot states it cannot safely answer from available knowledge and escalates in Bahasa Indonesia.")


def respond(text: str) -> str:
    return analyze(text)["response"]


def _payload(user_text: str, intent: str, register: str, terms: list[str], response: str, next_action: str, english_explanation: str) -> dict:
    return {
        "market": "indonesia",
        "sector": "multifinance_consumer_finance",
        "input": user_text,
        "intent": intent,
        "language_mix": "formal_colloquial_bahasa_with_finance_loanwords",
        "register": register,
        "terms_detected": terms,
        "response": response,
        "english_explanation": english_explanation,
        "next_action": next_action,
        "fallback_language_preserved": intent == "localized_fallback",
    }

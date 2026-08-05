from __future__ import annotations


def analyze(text: str) -> dict:
    t = text.lower()
    terms = [term for term in ["premium", "policy", "beneficiary", "rider", "lapse", "coverage", "bank referral"] if term in t]
    if any(word in t.split() for word in ["hello", "hi", "kumusta"]):
        return _payload(text, "greeting", "taglish_polite", terms, "Hello po. I can help with premium, policy, beneficiary, rider, lapse, coverage, or bank referral questions.", "continue_qualification", "The bot greets politely and offers market-specific insurance help.")
    if "human" in t or "agent" in t:
        return _payload(text, "human_escalation", "taglish_formal", terms, "Sige po, iha-handover ko na kayo sa human agent. Tatawagan po kayo pabalik para ma-assist nang maayos.", "handoff_to_human", "The bot confirms a human-agent handoff and keeps a polite Filipino/Taglish tone.")
    if "mahal" in t or "expensive" in t:
        return _payload(text, "premium_objection", "taglish_consultative", terms, "Gets ko po yung concern sa premium. I can explain the high-level options, pero final pricing should be confirmed by a licensed advisor.", "licensed_advisor_pricing_review", "The bot acknowledges the price objection, explains only high-level options, and routes final pricing to a licensed advisor.")
    if "lapse" in t or "renewal" in t or "reminder" in t:
        return _payload(text, "lapse_or_reminder", "taglish_polite", terms, "Noted po. Kung may risk na mag-lapse ang policy, mas safe na mag-set tayo ng reminder or callback para ma-check ang premium status.", "set_reminder_or_callback", "The bot identifies a possible lapse risk and proposes a reminder or callback rather than guessing policy status.")
    if "kailangan" in t and "insurance" in t:
        return _payload(text, "insurance_need", "filipino_taglish", terms, "Sige po. Para makatulong nang tama, kukunin ko muna ang edad, city, at coverage need ninyo.", "collect_qualification_fields", "The bot understands Tagalog/Taglish insurance intent and asks for qualification fields.")
    if "premium" in t or "magkano" in t or "policy" in t or "beneficiary" in t or "rider" in t or "bank referral" in t:
        return _payload(text, "policy_faq", "taglish", terms, "Thanks po. For your policy, we can discuss premium, beneficiary, rider, and coverage in Taglish if that is easier.", "continue_qualification", "The bot recognizes life-insurance terminology and offers to continue qualification in natural Taglish.")
    if "family" in t or "coverage" in t:
        return _payload(text, "family_coverage", "taglish_polite", terms, "Noted po. Kung family coverage ang kailangan, i-check natin ang policy and rider options nang hindi tayo mag-assume.", "collect_dependents", "The bot collects dependent/family coverage needs and explicitly avoids assuming exact rider eligibility.")
    if "later" in t or "callback" in t:
        return _payload(text, "callback_request", "taglish_polite", terms, "No problem po, pwede tayong mag-set ng callback. I will keep it in the same conversational tone.", "schedule_callback", "The bot treats the turn as a callback request and preserves the customer's conversational register.")
    return _payload(text, "localized_fallback", "filipino_polite", terms, "Pasensya na po, hindi ko muna masasagot 'yan nang siguradong grounded sa available info. I will connect you to a human specialist.", "handoff_to_human", "The bot says the information is not safely available and escalates without switching abruptly into English.")


def respond(text: str) -> str:
    return analyze(text)["response"]


def _payload(user_text: str, intent: str, register: str, terms: list[str], response: str, next_action: str, english_explanation: str) -> dict:
    return {
        "market": "philippines",
        "sector": "life_insurance_bancassurance",
        "input": user_text,
        "intent": intent,
        "language_mix": "english_filipino_taglish",
        "register": register,
        "terms_detected": terms,
        "response": response,
        "english_explanation": english_explanation,
        "next_action": next_action,
        "fallback_language_preserved": intent == "localized_fallback",
    }

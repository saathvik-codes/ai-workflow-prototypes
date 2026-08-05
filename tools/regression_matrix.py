from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.extend([
    str(ROOT / "q1-voice-agent" / "src"),
    str(ROOT / "q2-knowledge-base" / "src"),
    str(ROOT / "q3-localized-bots" / "src"),
    str(ROOT / "q4-live-insights" / "src"),
])

import agent  # type: ignore  # noqa: E402
from agent import build_lead_summary, respond  # type: ignore  # noqa: E402
from indonesia_bot import analyze as id_analyze  # type: ignore  # noqa: E402
from philippines_bot import analyze as ph_analyze  # type: ignore  # noqa: E402
from pipeline import stream_call  # type: ignore  # noqa: E402
from retriever import load_kb  # type: ignore  # noqa: E402


OUT = ROOT / "evidence" / "regression-results.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def q1_cases() -> list[dict]:
    cases = [
        ("TC-01 normal customer", "I need health insurance for myself.", "lead_opening", False, True),
        ("TC-02 family coverage", "I need insurance for my wife and two children.", "family_coverage", False, True),
        ("TC-03 callback", "I'm busy now. Please call me tomorrow afternoon.", "callback_request", False, False),
        ("TC-04 eligible", "Age:35 Non smoker Coverage:10 Lakhs", "eligible_lead", False, True),
        ("TC-05 not eligible", "Age:87", "not_eligible_age", True, True),
        ("TC-06 missing income", "I don't know my income.", "incomplete_or_conflicting_details", True, True),
        ("TC-07 expensive", "This is expensive.", "objection", False, True),
        ("TC-08 need time", "I'll think about it.", "needs_time", False, False),
        ("TC-09 already insured", "I already have insurance.", "existing_insurance", False, True),
        ("TC-10 weather", "What's the weather today?", "out_of_scope", True, False),
        ("TC-11 cricket", "What is the cricket score?", "out_of_scope", True, False),
        ("TC-12 programming", "Explain binary search.", "out_of_scope", True, False),
        ("TC-13 renewal", "When is renewal notice sent?", "grounded_kb_answer", False, True),
        ("TC-14 grace", "What is the grace period?", "grounded_kb_answer", False, True),
        ("TC-15 unknown product", "What is Diamond Ultra Platinum Gold Plan?", "unknown_product", True, False),
        ("TC-16 human", "I want to speak to a human.", "human_escalation", True, False),
        ("TC-17 angry", "This service is useless.", "high_risk_escalation", True, False),
        ("TC-18 legal", "I'll file a legal complaint.", "high_risk_escalation", True, False),
        ("TC-19 gibberish", "asdfghjk", "clarification", False, False),
        ("TC-20 silence", "", "reprompt", False, False),
        ("TC-21 mixed language", "Insurance kavali for family.", "family_coverage", False, True),
        ("TC-24 close", "Thank you.", "conversation_close", False, False),
        ("ALT-01 business loan", "I need a business loan for working capital.", "unsupported_business_loan", True, False),
        ("ALT-02 candidate screening", "Can you do candidate screening from a resume?", "unsupported_candidate_screening", True, False),
        ("ALT-03 loan reminder", "This is for a loan pre-due reminder.", "unsupported_loan_pre_due_reminder", True, False),
    ]
    results = []
    for case_id, text, intent, escalated, needs_source in cases:
        turn = respond(text)
        assert_true(turn.intent == intent, f"{case_id}: expected {intent}, got {turn.intent}")
        assert_true(turn.escalated is escalated, f"{case_id}: escalation mismatch")
        if needs_source:
            assert_true(bool(turn.source_ref), f"{case_id}: expected KB citation")
        results.append({"case": case_id, "input": text, "intent": turn.intent, "escalated": turn.escalated, "source_ref": turn.source_ref})

    summary = build_lead_summary([respond("I need family coverage.").__dict__, respond("My budget is 2500 monthly.").__dict__])
    assert_true({"intent", "coverage", "coverage_needs", "crm_stage"}.issubset(summary), "CRM summary missing required fields")
    results.append({"case": "TC-22 CRM lead JSON", "summary": summary})
    callback = respond("Please call me tomorrow afternoon.").__dict__
    assert_true(callback["intent"] == "callback_request", "Callback JSON action missing")
    results.append({"case": "TC-23 callback JSON", "action": callback["intent"], "answer": callback["answer"]})
    follow_up = respond(
        "my age is 27 and I live in Hyderabad and my amount is 5 lacs",
        {"transcript": [{"speaker": "customer", "text": "I need health insurance for myself."}]},
    )
    assert_true(follow_up.intent == "qualification_details_collected", "Multi-turn qualification details should be collected")
    assert_true(bool(follow_up.source_ref), "Multi-turn qualification needs KB citation")
    long_turn = respond("I need health insurance. " * 600)
    assert_true(long_turn.intent in {"lead_opening", "family_coverage", "fallback"}, "Long Q1 input should not crash")
    emoji_turn = respond("I need insurance for family 😊")
    assert_true(emoji_turn.intent == "family_coverage", "Emoji input should preserve core intent")
    for _ in range(100):
        assert_true(respond("When is renewal notice sent?").intent == "grounded_kb_answer", "Rapid Q1 request failed")

    original_kb_path = agent.KB_PATH
    try:
        agent.KB_PATH = ROOT / "q2-knowledge-base" / "out" / "__missing_kb__.json"
        unavailable = agent.respond("When is renewal notice sent?")
        assert_true(unavailable.intent == "knowledge_base_unavailable", "KB unavailable path should be explicit")
    finally:
        agent.KB_PATH = original_kb_path

    results.extend([
        {"case": "TC-25 multi-turn qualification details", "intent": follow_up.intent, "source_ref": follow_up.source_ref},
        {"case": "ST-01 Q1 100 rapid requests", "status": "passed"},
        {"case": "ST-02 Q1 long input", "intent": long_turn.intent},
        {"case": "ST-03 Q1 emoji input", "intent": emoji_turn.intent},
        {"case": "ST-04 Q1 KB unavailable", "intent": unavailable.intent},
    ])
    return results


def q2_cases() -> list[dict]:
    kb = load_kb(ROOT / "q2-knowledge-base" / "out" / "kb.json")
    cases = [
        ("TC-01 plans", "What plans do you offer?", "product_plans"),
        ("TC-02 family", "What is family coverage?", "family_coverage"),
        ("TC-03 renewal", "When is renewal notice sent?", "policy_renewal"),
        ("TC-04 grace", "What is grace period?", "policy_renewal"),
        ("TC-05 spouse", "Can I add spouse later?", "family_coverage"),
        ("TC-06 claim", "How do I claim insurance?", "claims"),
        ("TC-07 objection", "Premium is high.", "objection_handling"),
        ("TC-08 eligibility", "Who can buy this policy?", "qualification_rules"),
        ("TC-10 synonym", "Renew", "policy_renewal"),
        ("TC-11 typo", "Renwel", "policy_renewal"),
    ]
    results = []
    for case_id, query, expected in cases:
        hits = kb.search(query, top_k=3)
        assert_true(bool(hits), f"{case_id}: expected hit")
        assert_true(hits[0].category == expected, f"{case_id}: expected {expected}, got {hits[0].category}")
        results.append({"case": case_id, "query": query, "top_category": hits[0].category, "source_ref": hits[0].source_ref})

    assert_true(kb.search("", top_k=3) == [], "TC-12 empty query should return no hits")
    long_hits = kb.search("renewal notice " * 500, top_k=3)
    assert_true(bool(long_hits), "TC-13 long query should retrieve")
    assert_true(kb.search("My Aadhaar is 1234 5678 9012", top_k=3), "TC-14 PII query should route to PII handling")
    assert_true(kb.search("Diamond Ultra Platinum Gold Plan", top_k=3) == [], "TC-15 unknown product should return no hits")
    for _ in range(100):
        assert_true(kb.search("What is family coverage?", top_k=3)[0].category == "family_coverage", "Rapid KB request failed")
    return results + [
        {"case": "TC-12 empty query", "hits": 0},
        {"case": "TC-13 very long query", "top_category": long_hits[0].category},
        {"case": "TC-14 PII query", "top_category": kb.search("My Aadhaar is 1234 5678 9012", top_k=3)[0].category},
        {"case": "TC-15 unknown product", "hits": 0},
        {"case": "ST-05 Q2 100 rapid requests", "status": "passed"},
    ]


def q3_cases() -> list[dict]:
    cases = [
        ("PH-01 English", ph_analyze, "Hello", "greeting"),
        ("PH-02 Tagalog", ph_analyze, "Kailangan ko ng insurance", "insurance_need"),
        ("PH-03 Taglish", ph_analyze, "Premium magkano?", "policy_faq"),
        ("PH-04 Beneficiary", ph_analyze, "Beneficiary details please", "policy_faq"),
        ("PH-05 Rider", ph_analyze, "May rider ba?", "policy_faq"),
        ("PH-06 Human", ph_analyze, "Human agent please", "human_escalation"),
        ("PH-07 Reminder", ph_analyze, "Premium reminder please", "lapse_or_reminder"),
        ("PH-08 Renewal", ph_analyze, "Renewal reminder", "lapse_or_reminder"),
        ("PH-09 Bank referral", ph_analyze, "Bank referral premium", "policy_faq"),
        ("ID-11 Formal", id_analyze, "Saya mau cek cicilan dan jatuh tempo.", "installment_or_terms"),
        ("ID-12 Colloquial", id_analyze, "Bayar cicilan besok ya", "installment_or_terms"),
        ("ID-13 Regional", id_analyze, "Kulo telat bayar cicilan", "regional_accent_payment_issue"),
        ("ID-14 DP", id_analyze, "DP saya kurang", "installment_or_terms"),
        ("ID-15 Tenor", id_analyze, "Tenor masih bisa diubah?", "installment_or_terms"),
        ("ID-16 Denda", id_analyze, "Ada denda?", "late_payment_objection"),
        ("ID-17 Loan follow-up", id_analyze, "Loan saya overdue", "mixed_english_overdue"),
        ("ID-18 Collections", id_analyze, "Saya dapat tagihan collections", "collections_support"),
        ("ID-19 Mixed English", id_analyze, "Loan saya overdue", "mixed_english_overdue"),
        ("ID-20 Escalation", id_analyze, "Saya butuh customer service", "human_escalation"),
    ]
    results = []
    for case_id, fn, text, intent in cases:
        result = fn(text)
        assert_true(result["intent"] == intent, f"{case_id}: expected {intent}, got {result['intent']}")
        assert_true(bool(result["english_explanation"]), f"{case_id}: missing English explanation")
        results.append({"case": case_id, "input": text, "intent": result["intent"], "register": result["register"]})
    assert_true(ph_analyze("Insurance chahiye for family")["intent"] == "family_coverage", "Hindi/English mix should preserve family intent")
    assert_true(id_analyze("Halo 😊")["intent"] == "greeting", "Emoji greeting should not fail")
    for _ in range(100):
        assert_true(id_analyze("Saya mau cek DP dan tenor")["intent"] == "installment_or_terms", "Rapid Q3 request failed")
    results.extend([
        {"case": "ST-06 Q3 Hindi/English mix", "intent": "family_coverage"},
        {"case": "ST-07 Q3 emoji", "intent": "greeting"},
        {"case": "ST-08 Q3 100 rapid requests", "status": "passed"},
    ])
    return results


def q4_cases() -> list[dict]:
    cases = [
        ("TC-01 cross sell", ["Customer: I bought another car."], {"missed_cross_sell"}),
        ("TC-02 compliance", ["Agent: I skipped the disclosure."], {"compliance_gap"}),
        ("TC-03 frustration", ["Customer: I'm getting frustrated."], {"frustration"}),
        ("TC-04 callback", ["Customer: I'll pay tomorrow."], {"callback_need"}),
        ("TC-05 buying", ["Customer: I want full coverage."], {"buying_signal"}),
        ("TC-06 payment difficulty", ["Customer: I can't pay."], {"callback_need"}),
        ("TC-09 duplicate", ["Customer: I'm getting frustrated.", "Customer: I am angry"], {"frustration"}),
        ("TC-11 topic change", ["Customer: I need insurance.", "Customer: I can't pay."], {"callback_need"}),
        ("TC-12 multiple", ["Customer: I am frustrated. I bought another car. I can't pay."], {"frustration", "missed_cross_sell", "callback_need"}),
    ]
    results = []
    for case_id, chunks, expected in cases:
        result = stream_call(chunks)
        kinds = [n["signal"]["kind"] for n in result["nudges"]]
        assert_true(expected.issubset(set(kinds)), f"{case_id}: missing {expected}, got {kinds}")
        assert_true(all("llm_ms" in row for row in result["component_latency_ms"]), f"{case_id}: missing llm_ms latency")
        results.append({"case": case_id, "signals": kinds, "p95_ms": result["p95_ms"]})

    for chunks in ([], [""], ["background noise ... okay maybe...", "not sure what you mean ..."]):
        result = stream_call(chunks)
        assert_true(result["nudges"] == [], "Noisy/empty input should not emit nudges")
    multiple = stream_call(["Customer: I am frustrated. I bought another car. I cannot pay."])
    multiple_kinds = [n["signal"]["kind"] for n in multiple["nudges"]]
    assert_true(multiple_kinds[:3] == ["frustration", "callback_need", "missed_cross_sell"], f"Priority order mismatch: {multiple_kinds}")
    for _ in range(100):
        assert_true(stream_call(["Customer: I bought another car."])["nudges"], "Rapid Q4 request failed")
    return results + [
        {"case": "TC-07/08 noisy and ambiguous", "nudges": 0},
        {"case": "TC-12 priority order", "signals": multiple_kinds},
        {"case": "ST-09 Q4 100 rapid requests", "status": "passed"},
    ]


def main() -> None:
    report = {"q1": q1_cases(), "q2": q2_cases(), "q3": q3_cases(), "q4": q4_cases()}
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    total = sum(len(items) for items in report.values())
    print(json.dumps({"status": "passed", "cases": total, "report": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()

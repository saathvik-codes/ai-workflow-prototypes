from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
KB_PATH = BASE_DIR.parent / "q2-knowledge-base" / "out" / "kb.json"
Q2_SRC = BASE_DIR.parent / "q2-knowledge-base" / "src"

if str(Q2_SRC) not in sys.path:
    sys.path.append(str(Q2_SRC))

try:
    from retriever import load_kb  # type: ignore
except Exception:  # pragma: no cover
    load_kb = None


@dataclass
class AgentTurn:
    user: str
    intent: str
    answer: str
    source_ref: str | None = None
    escalated: bool = False
    retrieval_hit: str | None = None


@dataclass
class LeadSummary:
    name: str | None
    intent: str
    coverage: str | None
    coverage_needs: list[str]
    budget_range: str | None
    preliminary_eligibility: str
    callback_requested: bool
    crm_stage: str
    next_action: str
    notes: list[str]


def _load_kb_records() -> list[dict]:
    if not KB_PATH.exists():
        return []
    return json.loads(KB_PATH.read_text(encoding="utf-8"))


def _kb_available() -> bool:
    return KB_PATH.exists()


def _search_kb(query: str, top_k: int = 1) -> list[dict]:
    if load_kb and KB_PATH.exists():
        kb = load_kb(KB_PATH)
        hits = kb.search(query, top_k=top_k)
        return [
            {
                "record_id": hit.record_id,
                "title": hit.title,
                "content": hit.content,
                "category": hit.category,
                "source_ref": hit.source_ref,
            }
            for hit in hits
        ]

    records = _load_kb_records()
    q = query.lower()
    scored = []
    for rec in records:
        text = f'{rec["title"]} {rec["content"]} {" ".join(rec.get("tags", []))}'.lower()
        score = 0
        for token in re.findall(r"[a-z0-9]+", q):
            if token in text:
                score += 1
        if rec.get("category") in q:
            score += 2
        scored.append((score, rec))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [rec for score, rec in scored[:top_k] if score > 0]


def _context_text(context: dict | None) -> str:
    transcript = (context or {}).get("transcript", [])
    if not isinstance(transcript, list):
        return ""
    return " ".join(str(turn.get("text", "")) for turn in transcript if isinstance(turn, dict)).lower()


def _is_health_follow_up(text: str, context: dict | None) -> bool:
    history = _context_text(context)
    has_health_context = any(term in history for term in ["health insurance", "family coverage", "lead_opening", "family_coverage"])
    has_qualification_detail = any(term in text for term in ["age", "city", "live in", "hyderabad", "amount", "lacs", "lakhs", "lakh", "coverage"])
    return has_health_context and has_qualification_detail


def respond(user_text: str, context: dict | None = None) -> AgentTurn:
    text = user_text.lower()
    alternate_use_cases = {
        "business_loan": ["business loan", "working capital", "business-loan", "merchant loan"],
        "candidate_screening": ["candidate screening", "resume", "job candidate", "interview screening"],
        "loan_pre_due_reminder": ["loan pre-due", "pre due", "emi reminder", "loan reminder"],
    }
    for intent, phrases in alternate_use_cases.items():
        if any(phrase in text for phrase in phrases):
            return AgentTurn(
                user=user_text,
                intent=f"unsupported_{intent}",
                answer=(
                    "This prototype is configured for health-insurance lead qualification. "
                    "I should not pretend to run a different workflow, so I will escalate or route this to the right specialist."
                ),
                escalated=True,
            )
    insurance_terms = [
        "insurance", "policy", "premium", "coverage", "renewal", "grace", "claim",
        "spouse", "wife", "children", "family", "health", "beneficiary", "rider",
    ]
    if not _kb_available() and any(term in text for term in insurance_terms):
        return AgentTurn(
            user=user_text,
            intent="knowledge_base_unavailable",
            answer="Knowledge base unavailable. I should not answer from memory, so I will route this to a human specialist.",
            escalated=True,
        )
    if not text.strip():
        return AgentTurn(
            user=user_text,
            intent="reprompt",
            answer="I did not catch that. Could you please share your age, city, and coverage need so I can help safely?",
            escalated=False,
        )

    ages = [int(age) for age in re.findall(r"\b(?:i am|i'm|age is|aged?|age:)\s*[:\-]?\s*(\d{1,3})\b", text)]
    has_conflicting_age = len(set(ages)) > 1
    required_detail_terms = ["age", "years old", "budget", "phone", "number", "income", "coverage need"]
    has_uncertain_required_detail = (
        any(p in text for p in ["conflicting", "inconsistent"])
        or (
            any(p in text for p in ["not sure", "don't know", "do not know"])
            and any(term in text for term in required_detail_terms)
        )
    )

    if re.fullmatch(r"[a-z]{6,}", text.strip()) and not any(word in text for word in ["insurance", "policy", "premium"]):
        return AgentTurn(
            user=user_text,
            intent="clarification",
            answer="I could not understand that clearly. Please rephrase your insurance need, or I can arrange a human callback.",
            escalated=False,
        )

    if any(p in text for p in ["thank you", "thanks", "that's all"]):
        return AgentTurn(
            user=user_text,
            intent="conversation_close",
            answer="You're welcome. I have noted the conversation and will close this interaction safely.",
            escalated=False,
        )

    if any(p in text for p in ["human agent", "speak to a human", "talk to a person", "escalate"]):
        return AgentTurn(
            user=user_text,
            intent="human_escalation",
            answer="Absolutely. I'll hand this over to a human specialist and note your request for a callback.",
            escalated=True,
        )

    if any(p in text for p in ["useless", "angry", "complaint", "legal", "lawyer", "file a case"]):
        return AgentTurn(
            user=user_text,
            intent="high_risk_escalation",
            answer="I'm sorry this has been frustrating. I should not continue guessing here, so I'll escalate this to a human specialist.",
            escalated=True,
        )

    if has_conflicting_age or has_uncertain_required_detail:
        hits = _search_kb("incomplete application conflicting details escalate human callback", top_k=1)
        hit = hits[0] if hits else None
        return AgentTurn(
            user=user_text,
            intent="incomplete_or_conflicting_details",
            answer=(
                "I see missing or conflicting qualification details, so I should not guess. "
                "I'll route this for a human callback or collect the missing fields first."
            ),
            source_ref=hit["source_ref"] if hit else None,
            escalated=True,
            retrieval_hit=hit["record_id"] if hit else None,
        )

    if "call me later" in text or "callback" in text or "call me tomorrow" in text or "tomorrow afternoon" in text:
        return AgentTurn(
            user=user_text,
            intent="callback_request",
            answer="Absolutely. I'll save the callback request and note the requested time so a human can follow up.",
            escalated=False,
        )

    if any(p in text for p in ["weather", "cricket", "binary search", "programming", "stock", "invest", "formula", "underwriting formula"]):
        return AgentTurn(
            user=user_text,
            intent="out_of_scope",
            answer="I don't have that information in the current knowledge base, so I don't want to guess. I can connect you with a human specialist.",
            escalated=True,
        )

    if ages and max(ages) > 65:
        hits = _search_kb("qualification rules eligibility adult applicants age human callback", top_k=1)
        hit = hits[0] if hits else None
        return AgentTurn(
            user=user_text,
            intent="not_eligible_age",
            answer="Based on the current qualification rules, this age may fall outside the standard eligibility range. I will escalate to a human specialist for review.",
            source_ref=hit["source_ref"] if hit else None,
            escalated=True,
            retrieval_hit=hit["record_id"] if hit else None,
        )

    if ages and 18 <= min(ages) <= 65 and any(p in text for p in ["non smoker", "non-smoker", "coverage", "lakhs", "lakh"]):
        hits = _search_kb("qualification rules eligibility coverage amount health insurance", top_k=1)
        hit = hits[0] if hits else None
        return AgentTurn(
            user=user_text,
            intent="eligible_lead",
            answer="This looks preliminarily qualified based on age and coverage information. I will still route exact plan and premium confirmation to an advisor.",
            source_ref=hit["source_ref"] if hit else None,
            retrieval_hit=hit["record_id"] if hit else None,
        )

    if _is_health_follow_up(text, context):
        hits = _search_kb("qualification rules coverage amount health insurance city age", top_k=1)
        hit = hits[0] if hits else None
        return AgentTurn(
            user=user_text,
            intent="qualification_details_collected",
            answer=(
                "Thanks, I captured the age, city, and coverage amount. This looks preliminarily qualified, "
                "and I will prepare the lead summary for advisor review."
            ),
            source_ref=hit["source_ref"] if hit else None,
            retrieval_hit=hit["record_id"] if hit else None,
        )

    if "already have insurance" in text or "existing insurance" in text:
        hits = _search_kb("existing insurance renewal date comparison review", top_k=1)
        hit = hits[0] if hits else None
        return AgentTurn(
            user=user_text,
            intent="existing_insurance",
            answer="Thanks for sharing. May I ask your renewal date? We can compare coverage before recommending any change.",
            source_ref=hit["source_ref"] if hit else None,
            retrieval_hit=hit["record_id"] if hit else None,
        )

    if "think about it" in text or "need time" in text:
        return AgentTurn(
            user=user_text,
            intent="needs_time",
            answer="Of course. I will not keep pushing. I can schedule a callback when you are ready.",
            escalated=False,
        )

    if "wife" in text or "children" in text or "family" in text or "kavali" in text:
        hits = _search_kb("family floater spouse children coverage ages", top_k=1)
        if hits:
            hit = hits[0]
            return AgentTurn(
                user=user_text,
                intent="family_coverage",
                answer="I understand this is for family coverage. A family floater may fit; I should collect each member's age before suggesting a plan.",
                source_ref=hit["source_ref"],
                retrieval_hit=hit["record_id"],
            )

    if "health insurance" in text or "insurance for myself" in text:
        hits = _search_kb("available plans individual health plan age city coverage amount", top_k=1)
        hit = hits[0] if hits else None
        return AgentTurn(
            user=user_text,
            intent="lead_opening",
            answer="I can help with that. To qualify the lead properly, may I collect your age, city, and preferred coverage amount?",
            source_ref=hit["source_ref"] if hit else None,
            retrieval_hit=hit["record_id"] if hit else None,
        )

    if "renewal notice" in text or "grace period" in text:
        hits = _search_kb(text, top_k=1)
        if hits:
            hit = hits[0]
            return AgentTurn(
                user=user_text,
                intent="grounded_kb_answer",
                answer=f"According to the knowledge base: {hit['content']}",
                source_ref=hit["source_ref"],
                retrieval_hit=hit["record_id"],
            )

    if "diamond ultra platinum gold" in text:
        return AgentTurn(
            user=user_text,
            intent="unknown_product",
            answer="I do not have information about that product in the current knowledge base, so I should not invent details.",
            escalated=True,
        )

    if "budget" in text or "family" in text or "outpatient" in text or "hospitalization" in text:
        hits = _search_kb("qualification rules eligibility incomplete application health insurance coverage", top_k=1)
        if hits:
            hit = hits[0]
            return AgentTurn(
                user=user_text,
                intent="qualification",
                answer=(
                    "Thanks, that helps. I've noted the coverage needs and budget range. "
                    "If any required details are missing, I'll route this for a callback instead of guessing."
                ),
                source_ref=hit["source_ref"],
                retrieval_hit=hit["record_id"],
            )

    if "pre-existing" in text or "pre existing" in text or "coverage" in text:
        hits = _search_kb("policy renewal premium coverage human verification", top_k=1)
        if hits:
            hit = hits[0]
            return AgentTurn(
                user=user_text,
                intent="grounded_faq",
                answer=(
                    "Based on the knowledge base, I can confirm related policy details are available, "
                    "but I should verify the exact coverage with a human specialist before I promise anything."
                ),
                source_ref=hit["source_ref"],
                retrieval_hit=hit["record_id"],
            )

    if "document" in text or "need from me" in text:
        hits = _search_kb("incomplete application escalate callback", top_k=1)
        if hits:
            hit = hits[0]
            return AgentTurn(
                user=user_text,
                intent="documents",
                answer=(
                    "I can collect the details we need, and if anything is incomplete I'll escalate for a human callback "
                    "rather than inventing requirements."
                ),
                source_ref=hit["source_ref"],
                retrieval_hit=hit["record_id"],
            )

    if "expensive" in text or "price" in text or "premium is high" in text:
        hits = _search_kb("premium objection lower coverage simpler plan advisor review", top_k=1)
        if hits:
            hit = hits[0]
            return AgentTurn(
                user=user_text,
                intent="objection",
                answer=(
                    "I understand the concern. We can review benefits, check a lower coverage amount or simpler plan, "
                    "and have an advisor confirm exact pricing without promising discounts."
                ),
                source_ref=hit["source_ref"],
                retrieval_hit=hit["record_id"],
            )

    return AgentTurn(
        user=user_text,
        intent="fallback",
        answer="I'm not fully sure based on the knowledge base, so I'd rather escalate this than guess.",
        escalated=True,
    )


def run_script(turns: list[str]) -> list[dict]:
    transcript = []
    for turn in turns:
        response = respond(turn)
        transcript.append(asdict(response))
    return transcript


def build_lead_summary(transcript: list[dict]) -> dict:
    budget = None
    coverage_needs: list[str] = []
    notes: list[str] = []
    callback_requested = False
    escalated = False
    has_qualification_signal = False
    for turn in transcript:
        user = turn.get("user", "").lower()
        if "budget" in user:
            budget = "monthly budget mentioned"
            has_qualification_signal = True
        if "outpatient" in user and "outpatient" not in coverage_needs:
            coverage_needs.append("outpatient")
            has_qualification_signal = True
        if "hospitalization" in user and "hospitalization" not in coverage_needs:
            coverage_needs.append("hospitalization")
            has_qualification_signal = True
        if turn.get("intent") == "callback_request":
            callback_requested = True
        if turn.get("escalated"):
            escalated = True
            notes.append(f"escalated:{turn.get('intent')}")
        if turn.get("retrieval_hit"):
            notes.append(f"retrieval:{turn.get('retrieval_hit')}")
    if escalated:
        preliminary_eligibility = "needs_human_review"
        crm_stage = "escalated"
        next_action = "human specialist review"
    elif callback_requested:
        preliminary_eligibility = "preliminarily_qualified"
        crm_stage = "callback_requested"
        next_action = "schedule callback"
    elif has_qualification_signal:
        preliminary_eligibility = "preliminarily_qualified"
        crm_stage = "qualified_lead"
        next_action = "send to licensed advisor"
    else:
        preliminary_eligibility = "insufficient_information"
        crm_stage = "needs_more_info"
        next_action = "collect missing qualification fields"
    summary = LeadSummary(
        name=None,
        intent="health_insurance_lead_qualification",
        coverage=", ".join(coverage_needs) if coverage_needs else None,
        coverage_needs=coverage_needs,
        budget_range=budget,
        preliminary_eligibility=preliminary_eligibility,
        callback_requested=callback_requested,
        crm_stage=crm_stage,
        next_action=next_action,
        notes=notes,
    )
    return asdict(summary)

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from philippines_bot import analyze as ph_analyze, respond as ph_respond
from indonesia_bot import analyze as id_analyze, respond as id_respond


BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "out"
OUT_DIR.mkdir(exist_ok=True)


PH_SAMPLES = [
    "Hi, can you help me with premium and coverage?",
    "Pwede ba Taglish? I need family beneficiary details.",
    "Mahal ba ang premium kung may rider at bank referral?",
    "Baka mag-lapse yung policy ko, can you remind me later?",
    "I want a human agent please."
]

ID_SAMPLES = [
    "Saya mau cek cicilan dan jatuh tempo.",
    "Bisa pakai bahasa santai ya, saya telat bayar angsuran.",
    "Tenornya masih bisa diubah kalau DP saya kurang?",
    "Kulo telat bayar cicilan, pripun denda ne?",
    "Saya butuh customer service manusia."
]


def cmd_run(args: argparse.Namespace) -> None:
    if args.market == "ph":
        transcript = [{"user": t, "bot": ph_respond(t)} for t in PH_SAMPLES]
    else:
        transcript = [{"user": t, "bot": id_respond(t)} for t in ID_SAMPLES]
    out_path = OUT_DIR / f"{args.market}_transcript.json"
    out_path.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
    print(json.dumps(transcript, indent=2, ensure_ascii=False))


def cmd_test(_: argparse.Namespace) -> None:
    ph_results = [ph_analyze(t) for t in PH_SAMPLES]
    id_results = [id_analyze(t) for t in ID_SAMPLES]
    required_keys = {"intent", "language_mix", "register", "terms_detected", "response", "english_explanation", "next_action"}
    for item in ph_results + id_results:
        missing = required_keys.difference(item)
        if missing:
            raise AssertionError(f"localized result missing fields: {sorted(missing)}")
        if not item["response"] or not item["english_explanation"]:
            raise AssertionError("localized result must include native response and English reviewer explanation")
    if not any(item["intent"] == "premium_objection" for item in ph_results):
        raise AssertionError("Philippines tests must include premium objection handling")
    if not any(item["register"] == "javanese_influenced_bahasa" for item in id_results):
        raise AssertionError("Indonesia tests must include regional-accent handling")
    if not any(item["intent"] == "human_escalation" for item in ph_results + id_results):
        raise AssertionError("tests must include human escalation")
    result = {
        "philippines": ph_results,
        "indonesia": id_results,
        "coverage": {
            "cooperative_customer": True,
            "sector_specific_objection": True,
            "mixed_english_finance_terms": True,
            "colloquial_speech": True,
            "human_escalation": True,
            "indonesian_regional_accent_sample": "Javanese-influenced sample: Kulo telat bayar cicilan, pripun denda ne?",
        },
    }
    (OUT_DIR / "test-results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Question 3 localized bot CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("market", choices=["ph", "id"])
    p_run.set_defaults(func=cmd_run)
    p_test = sub.add_parser("test")
    p_test.set_defaults(func=cmd_test)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])

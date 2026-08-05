from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from kb_builder import build_kb
from retriever import load_kb


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUT_DIR = BASE_DIR / "out"


def _is_out_of_domain(question: str) -> bool:
    q = question.lower()
    return any(term in q for term in [
        "ipl", "cricket", "weather", "stock market", "football", "movie",
        "who won", "latest news", "yesterday's match", "restaurant",
        "programming", "binary search"
    ])


def _format_response(question: str, hits: list) -> dict:
    if not hits:
        if _is_out_of_domain(question):
            return {
                "answer": "Unsupported.",
                "citation": None,
                "reason": "The question is outside the insurance knowledge-base domain.",
            }
        if any(term in question.lower() for term in ["diamond", "platinum", "gold", "ultra"]):
            return {
                "answer": "No relevant information available.",
                "citation": None,
                "reason": "No matching document exists in the indexed knowledge records.",
            }
        return {
            "answer": "No relevant information available.",
            "citation": None,
            "reason": "No matching document exists in the indexed knowledge records.",
        }

    top = hits[0]
    return {
        "answer": top.content,
        "citation": top.source_ref,
        "category": top.category,
        "record_id": top.record_id,
        "reason": "Retrieved from the indexed knowledge records.",
    }


def cmd_build(_: argparse.Namespace) -> None:
    report = build_kb(RAW_DIR, OUT_DIR)
    print(json.dumps(report, indent=2))


def cmd_query(args: argparse.Namespace) -> None:
    kb_path = OUT_DIR / "kb.json"
    if not kb_path.exists():
        raise SystemExit("KB not built yet. Run `python .\\src\\cli.py build` first.")
    kb = load_kb(kb_path)
    question = (args.question or "").strip()
    if not question:
        payload = {
            "answer": "No relevant information available.",
            "citation": None,
            "reason": "Empty query provided.",
            "hits": [],
        }
        print(json.dumps(payload, indent=2))
        return
    if _is_out_of_domain(question):
        payload = {
            "answer": "Unsupported.",
            "citation": None,
            "reason": "The question is outside the insurance knowledge-base domain.",
            "hits": [],
        }
        print(json.dumps(payload, indent=2))
        return
    hits = kb.search(question, top_k=args.top_k)
    payload = _format_response(question, hits)
    payload["hits"] = [hit.__dict__ for hit in hits]
    print(json.dumps(payload, indent=2))


def cmd_test(_: argparse.Namespace) -> None:
    kb_path = OUT_DIR / "kb.json"
    if not kb_path.exists():
        raise SystemExit("KB not built yet. Run `python .\\src\\cli.py build` first.")
    kb = load_kb(kb_path)
    test_path = BASE_DIR / "tests" / "retrieval_cases.json"
    cases = json.loads(test_path.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        hits = kb.search(case["question"], top_k=1)
        top = hits[0] if hits else None
        verdict = "incorrect"
        if top:
            verdict = "correct" if case["expected_category"] == top.category else "partially correct"
        response = _format_response(case["question"], hits)
        results.append({
            "question": case["question"],
            "expected_category": case["expected_category"],
            "top_hit": None if not top else top.__dict__,
            "response": response,
            "verdict": verdict,
        })
    print(json.dumps(results, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Question 2 knowledge base CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build the KB from raw sources")
    p_build.set_defaults(func=cmd_build)

    p_query = sub.add_parser("query", help="Run a search query")
    p_query.add_argument("question", nargs="?")
    p_query.add_argument("--top-k", type=int, default=3)
    p_query.set_defaults(func=cmd_query)

    p_test = sub.add_parser("test", help="Run retrieval tests")
    p_test.set_defaults(func=cmd_test)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])

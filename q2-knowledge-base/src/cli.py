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


def cmd_build(_: argparse.Namespace) -> None:
    report = build_kb(RAW_DIR, OUT_DIR)
    print(json.dumps(report, indent=2))


def cmd_query(args: argparse.Namespace) -> None:
    kb_path = OUT_DIR / "kb.json"
    if not kb_path.exists():
        raise SystemExit("KB not built yet. Run `python .\\src\\cli.py build` first.")
    kb = load_kb(kb_path)
    hits = kb.search(args.question, top_k=args.top_k)
    print(json.dumps([hit.__dict__ for hit in hits], indent=2))


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
        results.append({
            "question": case["question"],
            "expected_category": case["expected_category"],
            "top_hit": None if not top else top.__dict__,
            "verdict": verdict,
        })
    print(json.dumps(results, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Question 2 knowledge base CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build the KB from raw sources")
    p_build.set_defaults(func=cmd_build)

    p_query = sub.add_parser("query", help="Run a search query")
    p_query.add_argument("question")
    p_query.add_argument("--top-k", type=int, default=3)
    p_query.set_defaults(func=cmd_query)

    p_test = sub.add_parser("test", help="Run retrieval tests")
    p_test.set_defaults(func=cmd_test)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])


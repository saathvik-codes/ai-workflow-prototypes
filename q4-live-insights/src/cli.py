from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from pipeline import stream_call


BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "out"
OUT_DIR.mkdir(exist_ok=True)


DEMO_CALL = [
    "Customer: Hello, I have one vehicle on my policy.",
    "Customer: Actually I bought a second car last week.",
    "Customer: Your agent skipped the disclosure and I am getting frustrated.",
    "Customer: I can't pay right now, call me later."
]


NOISY_CALL = [
    "background noise ... okay maybe...",
    "not sure what you mean ...",
    "just a normal update, nothing urgent",
    "okay thanks"
]


def cmd_demo(_: argparse.Namespace) -> None:
    result = stream_call(DEMO_CALL)
    (OUT_DIR / "demo.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def cmd_benchmark(_: argparse.Namespace) -> None:
    normal = stream_call(DEMO_CALL)
    noisy = stream_call(NOISY_CALL)
    result = {"normal": normal, "noisy": noisy}
    (OUT_DIR / "benchmark.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Question 4 live insights CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    p_demo = sub.add_parser("demo")
    p_demo.set_defaults(func=cmd_demo)
    p_bench = sub.add_parser("benchmark")
    p_bench.set_defaults(func=cmd_benchmark)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])

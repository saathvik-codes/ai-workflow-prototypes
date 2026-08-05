from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from agent import build_lead_summary, run_script


BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "out"
OUT_DIR.mkdir(exist_ok=True)


def cmd_run(args: argparse.Namespace) -> None:
    scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    transcript = run_script(scenario["turns"])
    out_path = OUT_DIR / f'{scenario["name"]}_transcript.json'
    out_path.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
    summary = build_lead_summary(transcript)
    (OUT_DIR / f'{scenario["name"]}_lead_summary.json').write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_crm_csv([{"scenario": scenario["name"], **summary}], OUT_DIR / f'{scenario["name"]}_crm_export.csv')
    print(json.dumps({"scenario": scenario["name"], "transcript_file": str(out_path), "lead_summary_file": str(OUT_DIR / f'{scenario["name"]}_lead_summary.json'), "turns": len(transcript)}, indent=2))


def cmd_test(_: argparse.Namespace) -> None:
    scenarios = sorted((BASE_DIR / "scenarios").glob("*.json"))
    results = []
    for scenario_path in scenarios:
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        transcript = run_script(scenario["turns"])
        summary = build_lead_summary(transcript)
        results.append({
            "scenario": scenario["name"],
            "turns": len(transcript),
            "escalated": any(t["escalated"] for t in transcript),
            "last_intent": transcript[-1]["intent"] if transcript else None,
            "crm_stage": summary["crm_stage"],
            "next_action": summary["next_action"],
            "retrieval_hits": [t["retrieval_hit"] for t in transcript if t.get("retrieval_hit")],
        })
    (OUT_DIR / "test-results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    write_crm_csv(results, OUT_DIR / "mock_crm_export.csv")
    print(json.dumps(results, indent=2))


def write_crm_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class CallHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/call":
            self._send_json(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8") or "{}")
        user_text = payload.get("text", "")
        response = __import__("agent").respond(user_text)
        self._send_json(200, {
            "input": user_text,
            "response": response.answer,
            "intent": response.intent,
            "escalated": response.escalated,
            "source_ref": response.source_ref,
            "retrieval_hit": response.retrieval_hit,
        })


def cmd_serve(args: argparse.Namespace) -> None:
    server = HTTPServer((args.host, args.port), CallHandler)
    print(json.dumps({"status": "listening", "host": args.host, "port": args.port, "endpoint": "/call"}, indent=2))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Question 1 voice agent CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("scenario")
    p_run.set_defaults(func=cmd_run)
    p_test = sub.add_parser("test")
    p_test.set_defaults(func=cmd_test)
    p_serve = sub.add_parser("serve", help="Start a local web calling interface")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8081)
    p_serve.set_defaults(func=cmd_serve)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])

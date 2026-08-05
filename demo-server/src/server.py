from __future__ import annotations

import argparse
import base64
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
EVIDENCE_DIR = BASE_DIR / "evidence" / "q1" / "recordings"

sys.path.extend([
    str(BASE_DIR / "q1-voice-agent" / "src"),
    str(BASE_DIR / "q2-knowledge-base" / "src"),
    str(BASE_DIR / "q3-localized-bots" / "src"),
    str(BASE_DIR / "q4-live-insights" / "src"),
])

from agent import build_lead_summary, respond, run_script  # type: ignore  # noqa: E402
from indonesia_bot import analyze as id_analyze, respond as id_respond  # type: ignore  # noqa: E402
from kb_builder import build_kb  # type: ignore  # noqa: E402
from philippines_bot import analyze as ph_analyze, respond as ph_respond  # type: ignore  # noqa: E402
from pipeline import stream_call  # type: ignore  # noqa: E402
from retriever import load_kb  # type: ignore  # noqa: E402


KB_DIR = BASE_DIR / "q2-knowledge-base"
KB_PATH = KB_DIR / "out" / "kb.json"


class DemoHandler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        if route == "/health":
            self._json(200, {"status": "ok"})
            return
        if route in {"/", "/q1", "/q2", "/q3", "/q4"}:
            self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        try:
            payload = self._payload()
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid_json", "message": "Request body must be valid JSON."})
            return
        if route == "/api/q1/call":
            self._json(200, respond(payload.get("text", ""), {"transcript": payload.get("transcript", [])}).__dict__)
            return
        if route == "/api/q1/scenario":
            turns = [
                "Hi, I'm interested in health insurance for my family.",
                "We want outpatient and hospitalization coverage.",
                "Our budget is around 2500 monthly.",
                "What documents do you need from me?",
            ]
            transcript = run_script(turns)
            self._json(200, {"transcript": transcript, "lead_summary": build_lead_summary(transcript)})
            return
        if route == "/api/q1/save-recording":
            saved = self._save_recording(payload)
            self._json(200, saved)
            return
        if route == "/api/q2/build":
            self._json(200, build_kb(KB_DIR / "data" / "raw", KB_DIR / "out"))
            return
        if route == "/api/q2/search":
            question = payload.get("question", "")
            if not str(question).strip():
                self._json(400, {"error": "empty_query", "hits": []})
                return
            if not KB_PATH.exists():
                build_kb(KB_DIR / "data" / "raw", KB_DIR / "out")
            kb = load_kb(KB_PATH)
            hits = [hit.__dict__ for hit in kb.search(question, top_k=3)]
            self._json(200, {"hits": hits})
            return
        if route == "/api/q3/respond":
            market = payload.get("market", "ph")
            text = payload.get("text", "")
            analysis = id_analyze(text) if market == "id" else ph_analyze(text)
            self._json(200, analysis)
            return
        if route == "/api/q4/stream":
            self._json(200, stream_call(payload.get("chunks", [])))
            return
        self._json(404, {"error": "not_found"})

    def _payload(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _save_recording(self, payload: dict) -> dict:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        name = payload.get("name", "web-call").replace(" ", "-")
        audio_data = payload.get("audio_base64", "")
        transcript = payload.get("transcript", [])
        if "," in audio_data:
            audio_data = audio_data.split(",", 1)[1]
        audio_path = EVIDENCE_DIR / f"{name}.webm"
        transcript_path = EVIDENCE_DIR / f"{name}.json"
        if audio_data:
            audio_path.write_bytes(base64.b64decode(audio_data))
        transcript_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "audio_file": str(audio_path),
            "transcript_file": str(transcript_path),
            "recording_saved": bool(audio_data),
            "turns": len(transcript),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified assessment demo server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8088)
    args = parser.parse_args()
    server = HTTPServer((args.host, args.port), DemoHandler)
    print(json.dumps({"status": "listening", "url": f"http://{args.host}:{args.port}/"}, indent=2))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

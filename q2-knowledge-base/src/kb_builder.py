from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "can", "for", "from",
    "how", "if", "in", "is", "it", "may", "of", "on", "or", "our", "that",
    "the", "their", "there", "this", "to", "what", "when", "where", "who",
    "with", "within", "you", "your"
}


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_boilerplate(text: str) -> str:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            lines.append("")
            continue
        lower = line.lower()
        if lower.startswith(("navigation:", "footer:")):
            continue
        if lower.startswith("duplicate section"):
            continue
        if lower in {"home | about | products | contact", "privacy policy | terms | careers"}:
            continue
        lines.append(line)
    return _normalize_text("\n".join(lines))


def _mask_pii(text: str) -> tuple[str, bool]:
    pii_found = False

    text, count = re.subn(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[REDACTED_EMAIL]", text)
    pii_found = pii_found or count > 0
    text, count = re.subn(r"\b(?:\+?\d{1,3}[- ]?)?(?:\d{3}[- ]?\d{3}[- ]?\d{4})\b", "[REDACTED_PHONE]", text)
    pii_found = pii_found or count > 0
    text, count = re.subn(r"\b0?\d{10,11}\b", "[REDACTED_PHONE]", text)
    pii_found = pii_found or count > 0

    # Mask obvious person-name label values in forms.
    text, count = re.subn(r"(?im)^(Name:\s*)(.+)$", r"\1[REDACTED_NAME]", text)
    pii_found = pii_found or count > 0

    return text, pii_found


def _split_chunks(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    return chunks


def _merge_heading_chunks(chunks: list[str]) -> list[str]:
    merged: list[str] = []
    i = 0
    while i < len(chunks):
        current = chunks[i]
        next_chunk = chunks[i + 1] if i + 1 < len(chunks) else ""
        is_heading = len(current.split()) <= 8 and not current.endswith(".") and "\n" not in current
        if is_heading and next_chunk and not next_chunk.startswith("#"):
            merged.append(f"{current}\n{next_chunk}")
            i += 2
            continue
        merged.append(current)
        i += 1
    return merged


def _dedupe_chunks(chunks: Iterable[str]) -> list[str]:
    unique: list[str] = []
    for chunk in chunks:
        if any(SequenceMatcher(None, chunk.lower(), seen.lower()).ratio() >= 0.9 for seen in unique):
            continue
        unique.append(chunk)
    return unique


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [tok for tok in tokens if tok not in STOPWORDS]


def _infer_category(source_name: str, chunk: str) -> str:
    text = f"{source_name} {chunk}".lower()
    if "do not retain" in text or "pii" in text or "redacted_phone" in text or "redacted_name" in text:
        return "pii_handling"
    if "family floater" in text or "spouse" in text or "children" in text:
        return "family_coverage"
    if "claims process" in text or "cashless" in text or "reimbursement" in text:
        return "claims"
    if "premium objection" in text or "premium is high" in text or "cheaper" in text:
        return "objection_handling"
    if "available plans" in text or "individual health plan" in text or "senior-support" in text:
        return "product_plans"
    if "partner" in text or "branch" in text:
        return "partnership_benefits"
    if "qualification" in text or "incomplete application" in text or "who can buy" in text:
        return "qualification_rules"
    if "renewal" in text or "lapse" in text or "grace period" in text:
        return "policy_renewal"
    if "pii" in text or "phone" in text or "name:" in text:
        return "pii_handling"
    return "general"


@dataclass
class KBRecord:
    record_id: str
    title: str
    content: str
    category: str
    source: str
    source_ref: str
    version: str
    pii_present: bool
    chunk_index: int
    tags: list[str]


def build_kb(raw_dir: str | Path, out_dir: str | Path) -> dict:
    raw_dir = Path(raw_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[KBRecord] = []
    report = {
        "sources": [],
        "raw_files": 0,
        "chunks_extracted": 0,
        "chunks_after_dedupe": 0,
        "pii_masked_chunks": 0,
        "source_errors": [],
    }

    for file_path in sorted(raw_dir.glob("*")):
        if not file_path.is_file():
            continue
        report["raw_files"] += 1
        try:
            original = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            report["source_errors"].append({
                "file": file_path.name,
                "error": f"encoding_error:{exc.__class__.__name__}",
            })
            continue
        if not original.strip():
            report["source_errors"].append({
                "file": file_path.name,
                "error": "empty_source",
            })
            continue
        cleaned = _clean_boilerplate(original)
        masked, pii_found = _mask_pii(cleaned)
        chunks = _merge_heading_chunks(_split_chunks(masked))
        chunks = _dedupe_chunks(chunks)
        report["chunks_extracted"] += len(_split_chunks(masked))
        report["chunks_after_dedupe"] += len(chunks)
        if pii_found:
            report["pii_masked_chunks"] += 1

        source_summary = {
            "file": file_path.name,
            "chunks": len(chunks),
            "pii_found": pii_found,
        }
        report["sources"].append(source_summary)

        for idx, chunk in enumerate(chunks):
            category = _infer_category(file_path.stem, chunk)
            lines = [line.lstrip("# ").strip() for line in chunk.splitlines() if line.strip()]
            title = lines[0][:80] if lines else file_path.stem
            content_hash = hashlib.sha1(f"{file_path.name}:{idx}:{chunk}".encode("utf-8")).hexdigest()[:10]
            tokens = _tokenize(chunk)
            tags = sorted(set(tokens[:6]))
            record = KBRecord(
                record_id=f"kb_{file_path.stem}_{idx:03d}_{content_hash}",
                title=title,
                content=chunk,
                category=category,
                source=file_path.name,
                source_ref=str(file_path.relative_to(raw_dir.parent).as_posix()),
                version="1.0",
                pii_present=pii_found,
                chunk_index=idx,
                tags=tags,
            )
            records.append(record)

    kb_path = out_dir / "kb.json"
    kb_path.write_text(json.dumps([asdict(r) for r in records], indent=2), encoding="utf-8")
    (out_dir / "build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1]
    build_kb(base / "data" / "raw", base / "out")

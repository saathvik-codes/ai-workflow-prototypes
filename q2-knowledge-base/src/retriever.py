from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "for", "from", "how", "if",
    "in", "is", "it", "may", "of", "on", "or", "that", "the", "to", "was",
    "what", "when", "where", "who", "with", "you", "your"
}


def tokenize(text: str) -> list[str]:
    tokens = []
    for t in re.findall(r"[a-z0-9]+", text.lower()):
        if t == "renwel":
            t = "renewal"
        if t == "renew":
            t = "renewal"
        if t in {"plans", "plan"}:
            t = "plan"
        if t in {"spouse", "wife", "children", "kids"}:
            t = "family"
        if t in {"claim", "claims"}:
            t = "claims"
        if t in STOPWORDS:
            continue
        if t.startswith("applic"):
            t = "apply"
        if t in {"phone", "number", "numbers"}:
            t = "phone"
        if t in {"name", "names"}:
            t = "name"
        tokens.append(t)
    return tokens


@dataclass
class SearchHit:
    record_id: str
    score: float
    title: str
    content: str
    category: str
    source_ref: str


class KnowledgeBase:
    def __init__(self, records: list[dict]):
        self.records = records
        self.doc_tokens = [tokenize(rec["title"] + " " + rec["content"] + " " + " ".join(rec.get("tags", []))) for rec in records]
        self.doc_len = [len(tokens) for tokens in self.doc_tokens]
        self.avgdl = sum(self.doc_len) / max(len(self.doc_len), 1)
        self.df = defaultdict(int)
        for tokens in self.doc_tokens:
            for token in set(tokens):
                self.df[token] += 1

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeBase":
        records = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(records)

    def search(self, query: str, top_k: int = 5) -> list[SearchHit]:
        q_tokens = tokenize(query)
        q_lower = query.lower()
        if not q_tokens:
            return []
        if any(term in q_lower for term in ["diamond", "platinum", "gold"]) and not any(term in q_lower for term in ["family", "individual", "senior"]):
            return []
        scores: list[tuple[int, float]] = []
        N = len(self.records)
        k1 = 1.5
        b = 0.75
        q_counts = Counter(q_tokens)

        for i, tokens in enumerate(self.doc_tokens):
            tf = Counter(tokens)
            score = 0.0
            for term, qf in q_counts.items():
                if term not in tf:
                    continue
                df = self.df.get(term, 0)
                idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
                denom = tf[term] + k1 * (1 - b + b * self.doc_len[i] / max(self.avgdl, 1e-9))
                score += idf * (tf[term] * (k1 + 1) / denom) * (1 + 0.1 * (qf - 1))

            rec = self.records[i]
            if rec.get("category") and rec["category"] in query.lower():
                score += 0.25
            if any(tag in query.lower() for tag in rec.get("tags", [])):
                score += 0.15
            if "incomplete" in q_lower and "apply" in q_tokens and rec.get("category") == "qualification_rules":
                score += 2.0
            if any(word in q_lower for word in ["phone", "name", "pii", "stored", "retain", "aadhaar", "aadhar"]) and rec.get("category") == "pii_handling":
                score += 2.5
            if "branch" in q_lower and rec.get("category") == "partnership_benefits":
                score += 1.0
            if "renewal" in q_lower and rec.get("category") == "policy_renewal":
                score += 1.0
            if any(word in q_lower for word in ["plans", "plan", "offer", "available"]) and rec.get("category") == "product_plans":
                score += 3.0
            if any(word in q_lower for word in ["family", "spouse", "wife", "children"]) and rec.get("category") == "family_coverage":
                score += 2.0
            if any(word in q_lower for word in ["claim", "claims"]) and rec.get("category") == "claims":
                score += 2.0
            if any(word in q_lower for word in ["expensive", "premium is high", "costly", "too high"]) and rec.get("category") == "objection_handling":
                score += 2.0
            if any(word in q_lower for word in ["eligible", "buy", "age"]) and rec.get("category") == "qualification_rules":
                score += 1.0
            if any(phrase in q_lower for phrase in ["who can buy", "who can apply", "eligible"]) and rec.get("category") == "qualification_rules":
                score += 3.0
            if "who can buy" in q_lower and rec.get("category") in {"family_coverage", "partnership_benefits"}:
                score -= 1.0
            scores.append((i, score))

        scores.sort(key=lambda item: item[1], reverse=True)
        hits = []
        for idx, score in scores:
            if len(hits) >= top_k:
                break
            if score < 0.5:
                continue
            rec = self.records[idx]
            hits.append(SearchHit(
                record_id=rec["record_id"],
                score=round(score, 4),
                title=rec["title"],
                content=rec["content"],
                category=rec["category"],
                source_ref=rec["source_ref"],
            ))
        return hits


def load_kb(path: str | Path) -> KnowledgeBase:
    return KnowledgeBase.load(path)

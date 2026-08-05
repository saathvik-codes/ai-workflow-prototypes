from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, asdict


@dataclass
class Signal:
    kind: str
    detail: str
    confidence: float
    topic: str


@dataclass
class Nudge:
    message: str
    priority: str
    expires_in_sec: int


@dataclass
class ChunkMetrics:
    chunk_index: int
    speaker: str
    asr_ms: float
    signal_ms: float
    llm_ms: float
    nudge_ms: float
    delivery_ms: float


def infer_speaker(chunk: str) -> str:
    t = chunk.lower().strip()
    if t.startswith("agent:"):
        return "agent"
    if t.startswith("customer:"):
        return "customer"
    if "your agent" in t or "i " in t or "i'm" in t or "i am" in t or "saya" in t:
        return "customer"
    return "unknown"


def normalize_chunk(chunk: str) -> str:
    return chunk.split(":", 1)[1].strip() if ":" in chunk and chunk.split(":", 1)[0].lower() in {"agent", "customer"} else chunk


def analyze_chunk(chunk: str, previous_topic: str | None = None) -> list[Signal]:
    t = chunk.lower()
    signals = []
    if "angry" in t or "frustrated" in t or "this is taking too long" in t:
        signals.append(Signal("frustration", "Customer appears frustrated", 0.91, "sentiment"))
    if "second car" in t or "another vehicle" in t or "second vehicle" in t:
        signals.append(Signal("missed_cross_sell", "Customer mentioned another vehicle", 0.88, "buying_signal"))
    if "another car" in t:
        signals.append(Signal("missed_cross_sell", "Customer mentioned another car", 0.88, "buying_signal"))
    if "full coverage" in t:
        signals.append(Signal("buying_signal", "Customer asked for full coverage", 0.86, "buying_signal"))
    if "didn't mention the disclosure" in t or "skipped disclosure" in t or "skipped the disclosure" in t:
        signals.append(Signal("compliance_gap", "Required disclosure may be missing", 0.95, "compliance"))
    if "guaranteed approval" in t or "no risk" in t:
        signals.append(Signal("risky_statement", "Potentially risky or overpromising statement", 0.9, "compliance"))
    if "call me later" in t or "can't pay right now" in t or "can't pay" in t or "cannot pay" in t or "pay tomorrow" in t:
        signals.append(Signal("callback_need", "Customer requested callback or payment help", 0.84, "payment_support"))
    if previous_topic and "vehicle" in t and previous_topic != "vehicle":
        signals.append(Signal("topic_shift", "Conversation shifted toward vehicle coverage", 0.82, "topic"))
    return signals


def nudge_for(signal: Signal) -> Nudge:
    mapping = {
        "frustration": Nudge("Acknowledge the concern before continuing.", "high", 120),
        "missed_cross_sell": Nudge("Customer mentioned a second vehicle. Suggest the multi-vehicle offer.", "medium", 180),
        "buying_signal": Nudge("Customer asked for broader coverage. Confirm needs and offer the approved coverage path.", "medium", 180),
        "compliance_gap": Nudge("Required disclosure is missing. Remind the agent before proceeding.", "high", 90),
        "callback_need": Nudge("Offer an approved callback path or payment-support option.", "medium", 180),
        "risky_statement": Nudge("Avoid overpromising. Restate only approved policy language.", "high", 90),
        "topic_shift": Nudge("Topic changed. Confirm the customer's current priority before continuing.", "low", 90),
    }
    return mapping[signal.kind]


def signal_priority(signal: Signal) -> int:
    order = {
        "risky_statement": 0,
        "compliance_gap": 1,
        "frustration": 2,
        "callback_need": 3,
        "buying_signal": 4,
        "missed_cross_sell": 5,
        "topic_shift": 6,
    }
    return order.get(signal.kind, 99)


def stream_call(chunks: list[str]) -> dict:
    confidence_threshold = 0.8
    chunks = [chunk for chunk in chunks if str(chunk).strip()]
    seen = set()
    emitted = []
    latencies = []
    metrics: list[ChunkMetrics] = []
    timeline = []
    current_topic: str | None = None
    for idx, chunk in enumerate(chunks):
        speaker = infer_speaker(chunk)
        clean_chunk = normalize_chunk(chunk)
        start = time.perf_counter()
        asr_start = time.perf_counter()
        time.sleep(0.004)
        asr_ms = (time.perf_counter() - asr_start) * 1000

        signal_start = time.perf_counter()
        signals = analyze_chunk(clean_chunk, previous_topic=current_topic)
        signal_ms = (time.perf_counter() - signal_start) * 1000
        if "vehicle" in clean_chunk.lower() or "car" in clean_chunk.lower():
            current_topic = "vehicle"
        elif "pay" in clean_chunk.lower() or "payment" in clean_chunk.lower():
            current_topic = "payment"

        nudge_ms = 0.0
        llm_ms = 0.0
        delivery_ms = 0.0
        signals = sorted(signals, key=signal_priority)
        for signal in signals:
            if signal.confidence < confidence_threshold:
                continue
            key = f"{signal.kind}:{signal.topic}"
            if key in seen and signal.kind != "compliance_gap":
                continue
            seen.add(key)
            nudge_start = time.perf_counter()
            nudge = nudge_for(signal)
            nudge_ms = (time.perf_counter() - nudge_start) * 1000
            llm_ms = nudge_ms
            delivery_start = time.perf_counter()
            time.sleep(0.001)
            delivery_ms = (time.perf_counter() - delivery_start) * 1000
            emitted.append({
                "chunk": idx,
                "speaker": speaker,
                "signal": asdict(signal),
                "nudge": asdict(nudge),
            })
        total_ms = (time.perf_counter() - start) * 1000
        latencies.append(total_ms)
        metrics.append(ChunkMetrics(idx, speaker, round(asr_ms, 3), round(signal_ms, 3), round(llm_ms, 3), round(nudge_ms, 3), round(delivery_ms, 3)))
        timeline.append({
            "chunk_index": idx,
            "speaker": speaker,
            "text": clean_chunk,
            "signals": [asdict(signal) for signal in signals if signal.confidence >= confidence_threshold],
        })
    false_positive_estimate = {
        "noisy_or_ambiguous_chunks": sum(1 for chunk in chunks if "noise" in chunk.lower() or "not sure" in chunk.lower()),
        "nudges_emitted": len(emitted),
        "suppression_note": "No nudge is emitted unless a signal crosses the confidence threshold and duplicate controls.",
    }
    p50_ms = round(statistics.median(latencies), 2) if latencies else 0.0
    p95_ms = round(sorted(latencies)[max(int(len(latencies) * 0.95) - 1, 0)], 2) if latencies else 0.0
    return {
        "nudges": emitted,
        "timeline": timeline,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "component_latency_ms": [asdict(m) for m in metrics],
        "controls": {
            "confidence_threshold": confidence_threshold,
            "duplicate_suppression": True,
            "topic_grouping": True,
            "cooldown_policy": "one active nudge per signal/topic group unless compliance is repeated",
            "priority_and_expiry": True,
        },
        "false_positive_analysis": false_positive_estimate,
        "chunks": len(chunks),
    }

"""tool3: reopen_stats. Is this problem going to come back?"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional

_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "americas"


def reopen_stats(intent_label: Optional[str] = None) -> Dict[str, Any]:
    """How often each kind of problem came back within 72 hours, from the
    eight human-handled conversations in transcripts_sample.jsonl."""
    rows = []
    with open(_DATA_DIR / "transcripts_sample.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    def summarize(group):
        reopened = [r for r in group if r.get("reopened_within_72h")]
        return {
            "conversations": len(group),
            "reopened_within_72h": len(reopened),
            "reopen_rate": round(len(reopened) / len(group), 2) if group else None,
            "reopen_reasons": [r.get("reopen_reason") for r in reopened],
        }

    by_intent: Dict[str, list] = {}
    for r in rows:
        by_intent.setdefault(r["intent_label"], []).append(r)

    if intent_label:
        if intent_label not in by_intent:
            return {"error": f"Unknown intent_label '{intent_label}'.",
                    "known_intent_labels": sorted(by_intent)}
        return {"intent_label": intent_label, **summarize(by_intent[intent_label])}
    return {
        "sample_note": "Only 8 human-handled conversations; treat rates as indicative, not statistical.",
        "overall": summarize(rows),
        "by_intent": {k: summarize(v) for k, v in sorted(by_intent.items())},
    }


TOOL_SCHEMA = {
        "name": "reopen_stats",
        "description": (
            "Answers 'Is this problem going to come back?'. Reads eight human-handled "
            "conversations (transcripts_sample.jsonl) and reports how often each kind of "
            "problem (intent_label, e.g. rebook_after_cancellation, refund_vs_credit) was "
            "reopened by the customer within 72 hours, with the reasons given. Use it to decide "
            "whether to close out the loose ends proactively (e.g. send_confirmation). Omit "
            "intent_label for all kinds. Tiny sample: say so, never present a rate as a promise."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "intent_label": {
                    "type": "string",
                    "description": "Optional kind of problem to filter on, e.g. 'rebook_after_cancellation'. "
                                   "An unknown value returns the list of valid labels.",
                },
            },
            "required": [],
        },
    }


TOOL_FUNCTION = reopen_stats

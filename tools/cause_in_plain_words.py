"""Tool: cause_in_plain_words. Larkspur's customer wording for a cause code,
from data/americas/disruption_policy.json. Moved here from agent.py unchanged."""
import json
from pathlib import Path
from typing import Any, Dict

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "americas"

SCHEMA = {
    "name": "cause_in_plain_words",
    "description": (
        "Use when a customer asks why their flight is delayed, cancelled or changed. "
        "Turns the raw cause code into the wording Larkspur lets you say to a customer. "
        "Call it after get_flight_status has given you the cause_code, and before you "
        "explain the situation or offer alternatives. You cannot invent the cause: you "
        "must already have the status data."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"],
                           "description": "The cause_code from get_flight_status."},
            "language": {"type": "string", "enum": ["en", "es"],
                         "description": "The customer's language, from the booking. Default en."},
        },
        "required": ["cause_code"],
    },
}


def run(cause_code: str, language: str = "en") -> Dict[str, Any]:
    """Larkspur's customer wording for a cause code, from disruption_policy.json."""
    policy = json.loads((DATA_DIR / "disruption_policy.json").read_text(encoding="utf-8"))
    labels = policy["cause_labels_customer"]
    code = str(cause_code).strip().upper()
    if code not in labels:
        return {"error": f"Unknown cause_code {cause_code!r}. Use one of: {', '.join(labels)}."}
    lang = str(language).strip().lower()
    if lang not in labels[code]:
        return {"cause_code": code, "language": "en", "customer_wording": labels[code]["en"],
                "note": f"No wording in {language!r}; only {', '.join(labels[code])} exist."}
    return {"cause_code": code, "language": lang, "customer_wording": labels[code][lang]}

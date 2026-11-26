"""Tool: fare_rules. Returns one section of Larkspur's written fare rules
(data/americas/fare_rules_excerpt.md). It states the rule and decides nothing."""
import re
from pathlib import Path

_FILE = Path(__file__).resolve().parent.parent / "data" / "americas" / "fare_rules_excerpt.md"
_SECTION = {
    "fare_families": "4",
    "disruption_rebooking": "5",
    "care_and_goodwill": "6",
    "chat_limits": "7",
}

SCHEMA = {
    "name": "fare_rules",
    "description": (
        "Returns the written Larkspur handbook text for one topic: fare families, "
        "disruption rebooking, care and goodwill (meals, hotel), or what chat won't do. "
        "Call it whenever the customer asks WHY they are not getting something, or "
        "questions or disputes a rule, so you can explain it from the handbook's own "
        "words instead of from memory. check_policy tells you what this customer gets; "
        "this tells you the rule behind it, so call both when the customer asks why. "
        "It doesn't cover baggage allowances or no-show rules."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "enum": list(_SECTION),
                "description": (
                    "fare_families = section 4 (Basic, Main, Main Plus, First); "
                    "disruption_rebooking = section 5 (delays, cancellations, diversions, refunds); "
                    "care_and_goodwill = section 6 (meals, hotel, goodwill credit); "
                    "chat_limits = section 7 (what chat automation will not do)."
                ),
            },
        },
        "required": ["topic"],
    },
}


def run(topic):
    """The section of the excerpt for this topic, verbatim, or a plain not-found result."""
    number = _SECTION.get(topic)
    if number is None:
        return {"error": "not in the fare rules excerpt: %s" % topic, "topics": list(_SECTION)}
    text = _FILE.read_text(encoding="utf-8")
    match = re.search(r"^### %s\..*?(?=^### \d+\.|\Z)" % number, text, re.S | re.M)
    if not match:
        return {"error": "not in the fare rules excerpt: %s" % topic}
    return {"topic": topic, "section": match.group(0).strip()}

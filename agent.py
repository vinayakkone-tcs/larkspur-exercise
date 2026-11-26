"""Larkspur disruption agent. This is the file you build.

It runs right now, and it is wrong in four places. The trace shows each one
before the code does, so read the trace first:

    python3 run.py K7PQ2M --trace

Where you edit:   grep -n '✏' agent.py   (six marks, one per place)
Steps and gates:  https://anthropicpartnerbasecamp.bts.com/
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any, Dict, List
from support import (MODEL, SYSTEM_PROMPT, call_local, execute_tool, mcp_client,
                     new_session, next_available_day, record_tool_result,
                     runtime_preamble)

MAX_TOOL_CALLS = 8  # Larkspur's own build capped the loop here; then a human takes over.

TONE_ADDENDUM = ""                       # ✏️ Build 4, step 4.1, intelligence goal
DATA_DIR = Path(__file__).resolve().parent / "data" / "americas"


def cause_in_plain_words(cause_code: str, language: str = "en") -> Dict[str, Any]:
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


def _minutes(hhmm: str) -> int:
    hours, mins = str(hhmm).strip().split(":")
    return int(hours) * 60 + int(mins)


def departures_in_window(origin: str, date: str, start_time: str, end_time: str,
                         dest: str = None) -> Dict[str, Any]:
    """Flights leaving one airport on one date inside a time window, from flights.csv.
    Cancelled flights are left out; delayed ones stay, placed by when they will leave."""
    try:
        start, end = _minutes(start_time), _minutes(end_time)
    except ValueError:
        return {"error": f"start_time and end_time must be HH:MM, got {start_time!r} and {end_time!r}"}
    origin = str(origin).strip().upper()
    dest = str(dest).strip().upper() if dest else None
    found = []
    with open(DATA_DIR / "flights.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["origin"] != origin or row["date"] != date:
                continue
            if dest and row["dest"] != dest:
                continue
            if row["status"] == "CANCELLED":
                continue
            est = _minutes(row["sched_dep_local"]) + int(row["delay_min"] or 0)
            if not start <= est <= end:
                continue
            found.append({
                "flight_no": row["flight_no"], "dest": row["dest"],
                "sched_dep_local": row["sched_dep_local"],
                "est_dep_local": f"{est // 60 % 24:02d}:{est % 60:02d}" + (" (+1 day)" if est >= 1440 else ""),
                "status": row["status"], "delay_min": int(row["delay_min"] or 0),
                "seats_left_Y": int(row["seats_left_Y"]), "seats_left_J": int(row["seats_left_J"]),
                "remarks": row["remarks"],
                "_sort": est,
            })
    found.sort(key=lambda r: r.pop("_sort"))
    return {"origin": origin, "date": date, "window": f"{start_time}-{end_time}",
            "dest": dest, "count": len(found), "departures": found}


EXTRA_TOOLS: List[Dict[str, Any]] = [    # ✏️ Build 2, step 2.1: schemas for the tools you add
    {
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
    },
    {
        "name": "departures_in_window",
        "description": (
            "Use when a customer needs other flights leaving an airport within a time range, "
            "such as 'what else leaves tonight between 6 and 10?' or 'what is the next flight "
            "this afternoon?', usually because their flight was cancelled or missed. Cancelled "
            "flights are not included. Delayed flights are, placed by when they will actually leave."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "IATA code of the departure airport, e.g. DEN."},
                "date": {"type": "string", "description": "Local departure date, YYYY-MM-DD."},
                "start_time": {"type": "string", "description": "Start of the window, local 24-hour HH:MM."},
                "end_time": {"type": "string", "description": "End of the window, local 24-hour HH:MM."},
                "dest": {"type": "string", "description": "Optional IATA code to keep only one destination."},
            },
            "required": ["origin", "date", "start_time", "end_time"],
        },
    },
]
LOCAL_TOOLS: Dict[str, Any] = {          # ✏️ Build 2, step 2.1: the functions behind them
    "cause_in_plain_words": cause_in_plain_words,
    "departures_in_window": departures_in_window,
}


def text_of(response) -> str:
    """Given. The last non-empty text block, never content[0]."""
    texts = [b.text for b in response.content if getattr(b, "type", None) == "text" and b.text]
    return texts[-1] if texts else ""


def tool_results(response) -> List[Dict[str, Any]]:
    """Given. Runs every tool_use block and packages the results the way the
    API expects them back. A tool can live in three places: the MCP server,
    LOCAL_TOOLS, or support/tools.py."""
    # three branches, no try/except in this file: mcp_client.call_remote() and
    # support.call_local() answer with an error dict instead of raising, and both
    # record what came back on the trace
    results = []
    for block in response.content:
        if getattr(block, "type", None) != "tool_use":
            continue
        if block.name in mcp_client.tool_names:
            output = mcp_client.call_remote(block.name, block.input)
        elif block.name in LOCAL_TOOLS:
            output = call_local(LOCAL_TOOLS[block.name], block.name, block.input)
        else:
            output = execute_tool(block.name, block.input)
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(output),
        })
    return results


def run_agent(pnr: str, last_name: str, message: str) -> str:            # ✏️ Build 1, step 1.2
    """Run the tool loop until Claude stops asking for tools. Return its final text."""
    client, tracer = new_session()
    tools = tool_list()
    messages = [
        {"role": "user", "content": f"PNR {pnr}, last name {last_name}. {message}"},
    ]

    response = client.messages.create(
        model=MODEL, max_tokens=4096, system=runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM,
        thinking={"type": "adaptive"}, tools=tools, messages=messages,
    )

    turns = 1
    while response.stop_reason == "tool_use" and turns < MAX_TOOL_CALLS:
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results(response)})
        response = client.messages.create(
            model=MODEL, max_tokens=4096, system=runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM,
            thinking={"type": "adaptive"}, tools=tools, messages=messages,
        )
        turns += 1

    answer = text_of(response)
    return answer


def tool_list() -> List[Dict[str, Any]]:                   # ✏️ Build 2, step 2.2
    """Given. Exactly what Claude is offered on every turn; run.py --show-tools
    prints this list."""
    return build_tools() + EXTRA_TOOLS


# ──────────────────────────────────────────────────────────────────────────────
# Below this line: what Claude is told about each tool. Step 1.3.
# The functions these describe are written and correct, in support/tools.py.
# ──────────────────────────────────────────────────────────────────────────────
def build_tools() -> List[Dict[str, Any]]:                 # ✏️ Build 1, step 1.3
    """Anthropic-shaped schemas: name, description, input_schema. What Claude is
    told about each of the nine tools, and all it is ever told."""
    return [
        {
            "name": "lookup_booking",
            "description": (
                "Retrieve a Larkspur reservation from Altura by confirmation code (PNR) "
                "and the passenger's last name. Both are required to prevent a lookup on "
                "a guessed PNR. Returns fare family, loyalty tier, the segment that needs "
                "attention, and any group/partner/minor/SSR flags relevant to scope."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "last_name": {"type": "string"}},
                "required": ["pnr", "last_name"],
            },
        },
        {
            "name": "get_flight_status",
            "description": (
                "Look up a Larkspur or Larkspur Link flight's current OpsFeed status for "
                "one local date: status, delay minutes, and cause. Use this before telling "
                "a customer anything about a flight's timing; never state it from memory."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "flight_no": {"type": "string"},
                    "date": {"type": "string", "description": "Local flight date in ISO format YYYY-MM-DD, e.g. 2025-05-08. Convert any other date format from the booking before calling."},
                },
                "required": ["flight_no", "date"],
            },
        },
        {
            "name": "search_alternatives",
            "description": "Find rebooking options for a customer whose flight was cancelled or badly delayed. Call it after lookup_booking and get_flight_status confirm the disruption. Returns ranked alternatives, each with an option_id, flights, date, and seats left. Pass a chosen option_id to hold_seat; do not invent one.",
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}},
                "required": ["pnr"],
            },
        },
        {
            "name": "check_policy",
            "description": (
                "Resolve what Larkspur owes this customer for the disruption: rebooking "
                "waiver, refund path, meal/hotel/ground care, goodwill eligibility and cap, "
                "and any escalation triggers. cause_code, delay_minutes and status describe "
                "what get_flight_status told you; fare_family, loyalty_tier and whether this "
                "is overnight are looked up from the booking, not asked of you. Every "
                "response carries a policy_row_id. Cite it if you reference this decision "
                "again."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"},
                    "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"]},
                    "delay_minutes": {"type": "integer"},
                    "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                    "wait_minutes_for_alternative": {"type": "integer"},
                    "chosen_option_id": {"type": "string"},
                },
                "required": ["pnr", "cause_code", "delay_minutes", "status"],
            },
        },
        {
            "name": "hold_seat",
            "description": "Place a 15-minute hold on one alternative. Reversible. It simply expires.",
            "input_schema": {
                "type": "object",
                "properties": {"option_id": {"type": "string"}, "pnr": {"type": "string"}},
                "required": ["option_id", "pnr"],
            },
        },
        {
            "name": "confirm_rebooking",
            "description": (
                "Finalize a held seat. Irreversible. Requires a confirmation_token that "
                "only the customer's own Confirm-click can produce. You cannot supply it "
                "yourself, and 'the customer said yes' in chat does not substitute for it."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"hold_id": {"type": "string"}, "confirmation_token": {"type": "string"}},
                "required": ["hold_id", "confirmation_token"],
            },
        },
        {
            "name": "issue_voucher",
            "description": (
                "Issue a meal, ground, hotel, or goodwill voucher. Auto-approves within the "
                "policy's threshold for that type; above it, returns a pending status for a "
                "human. It does not fail. Always pass the policy_row_id that made it eligible."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "voucher_type": {"type": "string", "enum": ["meal", "ground", "hotel", "goodwill"]},
                    "amount_usd": {"type": "number"},
                    "pnr": {"type": "string"},
                    "policy_row_id": {"type": "string"},
                },
                "required": ["voucher_type", "amount_usd", "pnr", "policy_row_id"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Hand this conversation to a human, with your reasoning attached. Use for "
                "groups, partner segments, unaccompanied minors, refunds, or anything else "
                "out of scope. This is the correct outcome for those cases, not a failure."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"}, "reason": {"type": "string"},
                    "summary_for_human": {"type": "string"}, "queue": {"type": "string"},
                },
                "required": ["pnr", "reason", "summary_for_human"],
            },
        },
        {
            "name": "send_confirmation",
            "description": "Send the customer a written confirmation of what was just done. Benign.",
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "message": {"type": "string"}},
                "required": ["pnr", "message"],
            },
        },
    ]

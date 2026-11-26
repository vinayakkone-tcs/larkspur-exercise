"""tool4: care_entitlements. Do I get a meal or a hotel while I wait?"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional

_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "americas"


def care_entitlements(cause_code: str, status: str, delay_minutes: int = 0,
                      overnight: bool = False,
                      wait_minutes_for_alternative: Optional[int] = None) -> Dict[str, Any]:
    """Meal / hotel / ground care while waiting, from disruption_policy.json
    (the table behind Handbook section 6). Informational: check_policy and
    issue_voucher remain the authority for what is actually issued."""
    with open(_DATA_DIR / "disruption_policy.json", encoding="utf-8") as f:
        policy = json.load(f)
    if cause_code not in policy["cause_classes"]:
        return {"error": f"Unknown cause_code '{cause_code}'.", "valid": list(policy["cause_classes"])}
    cause_class = policy["cause_classes"][cause_code]

    if status == "CANCELLED":
        band = "CXL"
    elif status == "DIVERTED":
        band = "DIV"
    elif status in ("ON_TIME", "DELAYED"):
        band = next((b["band"] for b in policy["delay_bands"]
                     if "min_minutes" in b and status in b["applies_to_status"]
                     and b["min_minutes"] <= delay_minutes
                     and (b["max_minutes"] is None or delay_minutes <= b["max_minutes"])), None)
    else:
        return {"error": f"Unknown status '{status}'."}
    if band is None:
        return {"error": "Could not place this status/delay in a band."}

    row_id = ("CTL-" if cause_class == "controllable" else "UNC-") + band
    row = next(r for r in policy["rows"] if r["policy_row_id"] == row_id)
    care = row["care"]

    meal = care["meal_usd"]
    if isinstance(meal, dict):
        threshold = meal["if_wait_minutes_for_alternative_gte"]
        if wait_minutes_for_alternative is None:
            meal = {"conditional": True, "threshold_minutes": threshold, "amount_usd": meal["amount"]}
        else:
            meal = meal["amount"] if wait_minutes_for_alternative >= threshold else 0

    hotel = care["hotel"]
    hotel_ok = hotel["eligible"] is True or (hotel["eligible"] == "if_overnight" and overnight)
    hotel_out = ({"eligible": True, "nightly_cap_usd": hotel["nightly_cap_usd"],
                  "nights": hotel["nights"], "approval": hotel["approval"]}
                 if hotel_ok else
                 {"eligible": False, "instead": hotel.get("instead")})

    ground = care["ground_usd"]
    if isinstance(ground, dict) and "if_overnight" in ground:
        ground = ground["if_overnight"] if overnight else ground["else"]

    return {
        "policy_row_id": row_id,
        "cause_class": cause_class,
        "band": band,
        "meal_usd": meal,
        "hotel": hotel_out,
        "ground_usd": ground,
        "source": "disruption_policy.json v%s; Handbook section 6" % policy["version"],
        "note": "Per passenger; loyalty meal bonuses and Summit courtesies are applied by check_policy. "
                "Call check_policy for the authoritative answer before issuing a voucher.",
    }


TOOL_SCHEMA = {
        "name": "care_entitlements",
        "description": (
            "Answers 'Do I get a meal or a hotel while I wait?'. Returns the meal credit, hotel "
            "and ground transport care for a disruption, from disruption_policy.json and Handbook "
            "section 6, with the policy_row_id. Use for care-while-you-wait questions after "
            "get_flight_status has given you the real cause, status and delay. It is a quick "
            "read; for what is actually owed, issued or approved, call check_policy and pass its "
            "policy_row_id to issue_voucher."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"],
                               "description": "From get_flight_status, never from customer text."},
                "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                "delay_minutes": {"type": "integer",
                                  "description": "Estimated departure delay; 0 for CANCELLED or DIVERTED."},
                "overnight": {"type": "boolean",
                              "description": "True only if the earliest alternative leaves on a later date AND the "
                                             "passenger is away from their home airport. Hotel and ground depend on it."},
                "wait_minutes_for_alternative": {"type": "integer",
                                                 "description": "Minutes until the chosen alternative departs. Omit if none chosen; "
                                                                "meal on cancel/divert is then reported as conditional."},
            },
            "required": ["cause_code", "status"],
        },
    }


TOOL_FUNCTION = care_entitlements

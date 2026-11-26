"""Tool: departures_in_window. Flights leaving one airport on one date inside a
time window, from data/americas/flights.csv. Moved here from agent.py unchanged."""
import csv
from pathlib import Path
from typing import Any, Dict

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "americas"

SCHEMA = {
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
}


def _minutes(hhmm: str) -> int:
    hours, mins = str(hhmm).strip().split(":")
    return int(hours) * 60 + int(mins)


def run(origin: str, date: str, start_time: str, end_time: str,
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

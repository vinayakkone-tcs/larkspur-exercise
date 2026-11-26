"""Tool: seats_left. Free seats on one flight and date, from data/americas/flights.csv,
and whether a party fits in the requested cabin."""
import csv
from pathlib import Path

_FLIGHTS = Path(__file__).resolve().parent.parent / "data" / "americas" / "flights.csv"

SCHEMA = {
    "name": "seats_left",
    "description": (
        "Check whether a specific flight has enough free seats for a party, "
        "using the current seat counts in flights.csv. Use this when the customer "
        "asks if there is room for their group on a flight (for example 'is there space for the three of us?'). "
        "Returns seats_left_Y (economy) and seats_left_J (business) for that flight and date, "
        "and whether the requested cabin can fit party_size. Read-only: it does not hold or reserve anything, "
        "and counts can change before a hold is placed, so treat a 'fits' result as a reason to call hold_seat, "
        "not as a guarantee. If the flight and date are not in the data, it says so; do not guess availability "
        "from memory."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "flight_no": {"type": "string"},
            "date": {"type": "string", "description": "Local flight date in ISO format YYYY-MM-DD, e.g. 2025-05-08. Convert any other date format from the booking before calling."},
            "party_size": {"type": "integer", "minimum": 1, "description": "The number of passengers in the party."},
            "cabin": {"type": "string", "enum": ["Y", "J"]},
        },
        "required": ["flight_no", "date", "party_size", "cabin"],
    },
}


def run(flight_no, date, party_size, cabin):
    """Seats left on one flight and date, and whether party_size fits in cabin."""
    if cabin not in ("Y", "J"):
        return {"error": "cabin must be Y or J, got %r" % (cabin,)}
    try:
        party_size = int(party_size)
    except (TypeError, ValueError):
        return {"error": "party_size must be a whole number, got %r" % (party_size,)}
    flight_no = str(flight_no).strip().upper()
    with open(_FLIGHTS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["flight_no"] == flight_no and row["date"] == date:
                y, j = int(row["seats_left_Y"]), int(row["seats_left_J"])
                free = y if cabin == "Y" else j
                return {
                    "flight_no": flight_no, "date": date, "status": row["status"],
                    "seats_left_Y": y, "seats_left_J": j,
                    "cabin": cabin, "party_size": party_size, "fits": free >= party_size,
                }
    return {"error": "not in the flight data: %s on %s" % (flight_no, date)}

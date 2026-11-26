"""Tool: next_available_day. The function already exists in support/tools.py;
this file is what tells Claude it is there."""
from support import next_available_day as run  # noqa: F401  (the function behind the schema)

SCHEMA = {
    "name": "next_available_day",
    "description": (
        "Finds the earliest date with an open seat on a route in a cabin. Use it when "
        "the customer's day is full or cancelled and they want the next day with seats "
        "on that route. Pass origin, dest and the segment's date (YYYY-MM-DD) from "
        "lookup_booking; cabin defaults to \"Y\". Unlike search_alternatives, it needs "
        "no PNR and returns only a date, not options you can hold. It checks for one "
        "passenger, so don't promise a family seats. It returns nothing if no date is found."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "IATA code of the departure airport, e.g. DEN."},
            "dest": {"type": "string", "description": "IATA code of the arrival airport, e.g. MCO."},
            "date": {"type": "string", "description": "Date of the full or cancelled segment, ISO format YYYY-MM-DD, e.g. 2025-05-08."},
            "cabin": {"type": "string", "description": "Cabin code, Y (main) or J (first). Optional; defaults to Y."},
        },
        "required": ["origin", "dest", "date"],
    },
}

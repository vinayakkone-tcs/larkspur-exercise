"""Tool: next_available_day. The function already exists in support/tools.py;
this file is what tells Claude it is there."""
from support import seats_left as run  # noqa: F401  (the function behind the schema)
SCHEMA = {
    "name": "seats_left",
    "description": (
                    "Check whether a specific flight has enough free seats for a party,"
		            "using the current seat counts in flights.csv. Use this when the customer "
		            "asks if there is room for their group on a flight (for example 'is there space for the three of us?')."
	                "Returns seats_left_Y (economy) and seats_left_J (business) for that flight and date,"
		            "and whether the requested cabin can fit party_size. Read-only: it does not hold or reserve anything, "
		            "and counts can change before a hold is placed, so treat a 'fits' result as a reason to call hold_seat,"
		            "not as a guarantee. If the flight and date are not in the data, it says so; do not guess availability " 
                    "from memory."
                    ),
                "input_schema": {
                     "type": "object",
                     "properties": {
                         "flight_no": {"type": "string"},
                         "date": {"type": "string", "description": "Local flight date in ISO format YYYY-MM-DD, e.g. 2025-05-08. Convert any other date format from the booking before calling."},
                         "party_size": {"type": "integer","minimum": 1, "description": "The number of passengers in the party."},
                         "cabin": {"type": "string", "enum": ["Y", "J"]},
                     }
                },     
                "required": ["flight_no", "date", "party_size", "cabin"],           
        }
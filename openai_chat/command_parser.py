# Handles natural language like "Add Ficus"
import re

def parse_command(message: str) -> dict:
    """Parses messages like 'Add Ficus' or 'Remove Aloe'"""
    match = re.match(r"(add|remove)\s+(?P<plant>[\w\s]+)", message, re.IGNORECASE)
    if match:
        return {
            "action": match.group(1).lower(),
            "plant_name": match.group("plant").strip()
        }
    return {}

# Extracts intent (e.g., “Water my Monstera”, “Diagnose this plant”) from user commands.


def parse_command(text):
    text = text.lower()
    if "diagnose" in text or "what's wrong" in text:
        return "diagnosis"
    # Add more commands as needed
    return "chat"

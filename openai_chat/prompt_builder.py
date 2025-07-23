# Reusable prompt templates and formatting
def build_plant_diagnosis_prompt(symptom: str, plant_type: str = "") -> str:
    return (
        f"I have a {plant_type or 'houseplant'} and its leaves are {symptom}. "
        "What could be the reason, and what should I do to fix it?"
    )

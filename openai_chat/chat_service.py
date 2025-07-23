# Main business logic for answering questions

from openai_chat.openai_client import ask_openai
from openai_chat.prompt_builder import build_plant_diagnosis_prompt

def handle_chat_query(user_message: str) -> str:
    # Optionally: classify or parse first
    prompt = f"You are a plant care assistant. Answer: {user_message}"
    return ask_openai(prompt)

def diagnose_plant_issue(symptom: str, plant: str = "") -> str:
    prompt = build_plant_diagnosis_prompt(symptom, plant)
    return ask_openai(prompt)

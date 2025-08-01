# Handles direct calls to the OpenAI API.
from openai import OpenAI
from settings import Setting

client = OpenAI(api_key=Setting.open_ai_key)

def ask_gpt4o(prompt: str, system_prompt: str = None) -> str:
    """
    Send a prompt to the GPT-4o-mini model and return the response.
    Optionally include a system prompt for context.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return response.choices[0].message.content
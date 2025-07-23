# Handles actual OpenAI API calls
import openai
from settings import Setting  # Make sure your API key is stored in settings.py

openai.api_key = Setting.open_api_key

def ask_openai(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message["content"]

# Handles direct calls to the OpenAI API.
import os
from openai import OpenAI
from settings import Setting


client = OpenAI(api_key=Setting.open_ai_key)

def chat_with_gpt(messages, model="gpt-4o-mini"):
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content
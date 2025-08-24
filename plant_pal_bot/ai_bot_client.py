# Handles direct calls to the OpenAI API.
from openai import OpenAI
from settings import Setting
from typing import List, Optional
import base64

client = OpenAI(api_key=Setting.open_ai_key)

def ask_gpt4o(
        user_prompt: str,
        system_prompt: Optional[str] = None,
        image_path: Optional[str] = None,
        max_tokens: int = 300,
) -> str:
    """
    Send a prompt to the GPT-4o-mini model and return the response.

    - If only user_prompt is given → behaves like normal text Q&A.
    - If image_path is provided → sends both text + image for multimodal Q&A.

    Args:
        user_prompt (str): The user’s text input
        system_prompt (Optional[str]): Optional system-level instruction
        image_path (Optional[str]): Path to an image file (JPEG/PNG)
        max_tokens (int): Max tokens for response
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # If image is provided → encode and attach
    if image_path:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        })
    else:
        # Text-only fallback
        messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=Setting.open_ai_model,
        messages=messages,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content.strip()


def embed_text(text: str) -> List[float]:
    """
    Create an embedding for plain text (user queries, diagnosis text).
    """
    try:
        resp = client.embeddings.create(
            model=Setting.embedding_model,
            input=text
        )
        return resp.data[0].embedding
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {str(e)}")
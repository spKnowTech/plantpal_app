# Builds reusable, context-aware prompt templates.

def build_prompt(user_message, context=None):
    system_prompt = {
        "role": "system",
        "content": ("You are a helpful and knowledgeable plant care assistant. "
                    "Answer user questions or provide plant care/diagnosis advice.")
    }
    user = {"role": "user", "content": user_message}
    messages = [system_prompt]
    if context:
        messages.extend(context)
    messages.append(user)
    return messages
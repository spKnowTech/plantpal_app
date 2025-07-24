# Orchestrates the user input, command parsing, prompt construction, OpenAI call, and logging of AI responses.

from openai_chat.command_parser import parse_command
from openai_chat.prompt_builder import build_prompt
from openai_chat.openai_client import chat_with_gpt
from models.ai_chat import AILog
from sqlalchemy.orm import Session


def answer_user_question(db: Session, user_id, user_message, plant_id=None):
    chat_type = parse_command(user_message)
    messages = build_prompt(user_message)
    response = chat_with_gpt(messages)

    ai_log = AILog(
        user_id=user_id,
        plant_id=plant_id,
        input_text=user_message,
        ai_response=response,
        type=chat_type
    )
    db.add(ai_log)
    db.commit()
    db.refresh(ai_log)
    return ai_log

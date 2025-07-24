from sqlalchemy.orm import Session
from models.ai_chat import AILog
from schemas.ai_chat import AIChatRequest


def log_ai_interaction(db: Session, user_id: int, request: AIChatRequest, response: str, type: str = "chat"):
    ai_log = AILog(
        user_id=user_id,
        plant_id=request.plant_id,
        input_text=request.input_text,
        ai_response=response,
        type=type
    )
    db.add(ai_log)
    db.commit()
    db.refresh(ai_log)
    return ai_log

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from services.user_service import get_current_user
from openai_chat.chat_service import answer_user_question
from schemas.ai_chat import AIChatRequest, AIChatResponse
from database import get_db


router = APIRouter(prefix="/ai-chat", tags=["AI Chat"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def ai_chat_page(request: Request):
    return templates.TemplateResponse("ai_chat.html", {"request": request})


@router.post("/", response_model=AIChatResponse)
def chat_with_ai(
    data: AIChatRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    ai_log = answer_user_question(
        db=db,
        user_id=user.id,
        user_message=data.input_text,
        plant_id=data.plant_id
    )
    return {"ai_response": ai_log.ai_response, "type": ai_log.type}

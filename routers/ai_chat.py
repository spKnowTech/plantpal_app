from fastapi import APIRouter
from openai_chat.chat_service import handle_chat_query
from schemas.openai_chat import ChatRequest


router = APIRouter()

@router.post("/chat/ask")
def chat_with_ai(payload: ChatRequest):
    reply = handle_chat_query(payload.message)
    return {"reply": reply}
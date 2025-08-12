from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from repositories.plant_repo import get_user_plants
from services.user_service import get_current_user
from database import get_db
from sqlalchemy.orm import Session
from services.ai_bot_service import (
    get_chat_history_service,
    handle_ai_chat,
    start_fresh_conversation
)
from utils.markdown_converter import markdown_to_html
from schemas.user import ResponseUser
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/ai_chat", response_class=HTMLResponse)
async def ai_chat_page(
        request: Request,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """Render the AI chat page with conversation history and user plants."""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    plants = get_user_plants(db, user.id)

    # Check if this is a fresh page load (not a redirect from POST)
    referer = request.headers.get("referer", "")
    is_fresh_load = not referer or "/ai_chat" not in referer

    if is_fresh_load:
        # Fresh page load - always start with a new conversation
        welcome_message = start_fresh_conversation(db, user.id, user.full_name)
        chat_history = [{
            "is_user": False,
            "text": welcome_message,
            "timestamp": datetime.now().strftime("%H:%M")
        }]
    else:
        # This is a redirect from POST - get current session conversation
        chat_history = get_chat_history_service(db, user.id)

        # Add timestamps to messages if not already present
        for message in chat_history:
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().strftime("%H:%M")

    # Convert markdown to HTML for bot messages
    for message in chat_history:
        if not message["is_user"]:
            message["text"] = markdown_to_html(message["text"])

    response = templates.TemplateResponse("ai_bot_chat.html", {
        "request": request,
        "chat_history": chat_history,
        "user_plants": plants,
        "user": user
    })

    return response


@router.post("/ai_chat", response_class=HTMLResponse)
async def ai_chat_post(
        request: Request,
        user_message: str = Form(...),
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """Handle AI chat message submission and generate bot response."""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        # Generate bot response (this will handle saving user message and AI response)
        bot_response = handle_ai_chat(db, user.id, user_message)

        return RedirectResponse(url="/ai_chat", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        # Log the error for debugging
        print(f"Error in ai_chat_post: {str(e)}")
        # Return to chat page with error message
        return RedirectResponse(url="/ai_chat", status_code=status.HTTP_303_SEE_OTHER)

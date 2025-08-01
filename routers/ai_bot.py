from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from repositories.plant_repo import get_user_plants
from repositories.ai_bot_repo import has_existing_conversation, get_latest_user_input
from services.user_service import get_current_user
from database import get_db
from sqlalchemy.orm import Session
from services.ai_bot_service import (
    get_chat_history_service,
    handle_ai_chat,
    create_welcome_message
)
from utils.markdown_converter import markdown_to_html
from schemas.user import ResponseUser

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/ai_chat", response_class=HTMLResponse)
def ai_chat_page(
    request: Request, 
    db: Session = Depends(get_db), 
    user: ResponseUser = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    plants = get_user_plants(db, user.id)
    chat_history = get_chat_history_service(db, user.id)

    # Check if user has any existing conversation history
    has_history = has_existing_conversation(db, user.id)
    
    # If no existing conversation, create a fresh one with welcome message
    if not has_history:
        # Create welcome message
        welcome_message = create_welcome_message(db, user.id, user.full_name, plants)
        
        # Save the welcome message as a bot message
        from services.ai_bot_service import save_bot_message_service
        save_bot_message_service(db, user.id, welcome_message)
        
        chat_history = [{
            "is_user": False,
            "text": welcome_message
        }]
    else:
        # Check if there's a pending user input without response
        pending_input = get_latest_user_input(db, user.id)
        if pending_input:
            # Add the pending user input to the chat history
            chat_history.append({
                "is_user": True,
                "text": pending_input
            })
    
    # Convert markdown to HTML for bot messages
    for message in chat_history:
        if not message["is_user"]:
            message["text"] = markdown_to_html(message["text"])
    
    return templates.TemplateResponse("ai_bot_chat.html", {
        "request": request,
        "chat_history": chat_history,
        "user_plants": plants,
        "user": user
    })

@router.post("/ai_chat", response_class=HTMLResponse)
def ai_chat_post(
    request: Request,
    user_message: str = Form(...),
    db: Session = Depends(get_db),
    plant_id: int = Form(None),
    user: ResponseUser = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    try:
        # Save user message first
        from services.ai_bot_service import save_user_message_service
        save_user_message_service(db, user.id, user_message)
        
        # Generate bot response
        bot_response = handle_ai_chat(db, user.id, user_message, plant_id)
        
        return RedirectResponse(url="/ai_chat", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        # Log the error for debugging
        print(f"Error in ai_chat_post: {str(e)}")
        # Return to chat page with error message
        return RedirectResponse(url="/ai_chat", status_code=status.HTTP_303_SEE_OTHER)

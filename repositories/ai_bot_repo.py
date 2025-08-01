from sqlalchemy.orm import Session
from models.ai_bot import AILog, AIResponse
from schemas.ai_bot import AIChatRequest

def log_ai_interaction(
    db: Session,
    user_id: int,
    request: AIChatRequest,
    response: str,
    log_type: str = "chat"
) -> AILog:
    """
    Log an AI interaction to the database.
    """
    try:
        # Create the user input log
        ai_log = AILog(
            user_id=user_id,
            plant_id=request.plant_id,
            input_text=request.input_text,
            type=log_type
        )
        db.add(ai_log)
        db.commit()
        db.refresh(ai_log)
        
        # Create the AI response
        ai_response = AIResponse(
            ai_log_id=ai_log.id,
            user_id=user_id,
            response_text=response
        )
        db.add(ai_response)
        db.commit()
        db.refresh(ai_response)
        
        return ai_log
    except Exception as e:
        db.rollback()
        print(f"Error in log_ai_interaction: {str(e)}")
        raise

def save_chat_message(db: Session, user_id: int, text: str, is_user: bool):
    """Save a chat message to the database."""
    try:
        if is_user:
            # Save user input
            ai_log = AILog(
                user_id=user_id,
                input_text=text,
                type="chat"
            )
            db.add(ai_log)
            db.commit()
            db.refresh(ai_log)
            return ai_log
        else:
            # Save AI response - find the most recent user input without response
            latest_user_input = db.query(AILog).filter(
                AILog.user_id == user_id,
                AILog.input_text.isnot(None),
                AILog.type == "chat"
            ).order_by(AILog.created_at.desc()).first()
            
            if latest_user_input:
                # Check if this user input already has a response
                existing_response = db.query(AIResponse).filter(
                    AIResponse.ai_log_id == latest_user_input.id
                ).first()
                
                if not existing_response:
                    # Create new AI response
                    ai_response = AIResponse(
                        ai_log_id=latest_user_input.id,
                        user_id=user_id,
                        response_text=text
                    )
                    db.add(ai_response)
                    db.commit()
                    db.refresh(ai_response)
                    return latest_user_input
            else:
                # If no user input found, create a standalone AI response
                # This handles the welcome message case
                ai_response = AIResponse(
                    ai_log_id=None,
                    user_id=user_id,
                    response_text=text
                )
                db.add(ai_response)
                db.commit()
                db.refresh(ai_response)
                return None
            
            return None
    except Exception as e:
        db.rollback()
        print(f"Error in save_chat_message: {str(e)}")
        raise

def get_chat_history(db: Session, user_id: int) -> list[dict]:
    """Get chat history for a user, ordered by time."""
    try:
        # Get all AI logs for the user that have both input and response
        logs = db.query(AILog).filter(
            AILog.user_id == user_id,
            AILog.type == "chat"
        ).order_by(AILog.created_at).all()
        
        history = []
        
        # Process each log entry
        for log in logs:
            # Only add user message if there's also an AI response
            ai_response = db.query(AIResponse).filter(
                AIResponse.ai_log_id == log.id
            ).first()
            
            if log.input_text and ai_response:
                # Add user message
                history.append({
                    "is_user": True, 
                    "text": log.input_text,
                    "created_at": log.created_at
                })
                
                # Add AI response
                history.append({
                    "is_user": False, 
                    "text": ai_response.response_text,
                    "created_at": ai_response.created_at
                })
        
        # Also get standalone AI responses (like welcome messages)
        standalone_responses = db.query(AIResponse).filter(
            AIResponse.user_id == user_id,
            AIResponse.ai_log_id.is_(None)
        ).order_by(AIResponse.created_at).all()
        
        for response in standalone_responses:
            history.append({
                "is_user": False, 
                "text": response.response_text,
                "created_at": response.created_at
            })
        
        # Sort by creation time
        history.sort(key=lambda x: x["created_at"])
        
        # Remove created_at from the final result
        for item in history:
            del item["created_at"]
        
        return history
    except Exception as e:
        print(f"Error in get_chat_history: {str(e)}")
        return []

def get_user_input_history(db: Session, user_id: int) -> list[str]:
    """Get only user input history for creating summary."""
    try:
        logs = db.query(AILog).filter(
            AILog.user_id == user_id,
            AILog.input_text.isnot(None),
            AILog.type == "chat"
        ).order_by(AILog.created_at).all()
        return [log.input_text for log in logs]
    except Exception as e:
        print(f"Error in get_user_input_history: {str(e)}")
        return []

def clear_ai_responses(db: Session, user_id: int):
    """Clear all AI responses for a user (called on logout)."""
    try:
        # Delete all AI responses for this user
        db.query(AIResponse).filter(AIResponse.user_id == user_id).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error in clear_ai_responses: {str(e)}")

def has_existing_conversation(db: Session, user_id: int) -> bool:
    """Check if user has any existing conversation history."""
    try:
        # Check if there are any AI responses for this user
        count = db.query(AIResponse).filter(
            AIResponse.user_id == user_id
        ).count()
        return count > 0
    except Exception as e:
        print(f"Error in has_existing_conversation: {str(e)}")
        return False

def get_latest_user_input(db: Session, user_id: int) -> str:
    """Get the most recent user input that doesn't have an AI response yet."""
    try:
        # Find the most recent user input without a response
        latest_input = db.query(AILog).filter(
            AILog.user_id == user_id,
            AILog.input_text.isnot(None),
            AILog.type == "chat"
        ).order_by(AILog.created_at.desc()).first()
        
        if latest_input:
            # Check if this input has a response
            has_response = db.query(AIResponse).filter(
                AIResponse.ai_log_id == latest_input.id
            ).first()
            
            if not has_response:
                return latest_input.input_text
        
        return None
    except Exception as e:
        print(f"Error in get_latest_user_input: {str(e)}")
        return None
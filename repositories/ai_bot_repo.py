import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from models.ai_bot import AILog, AIResponse, ConversationSession
from schemas.ai_bot import AIChatRequest


def log_ai_interaction(db: Session, user_id: int, request: AIChatRequest,
                       response: str, log_type: str = "chat") -> AILog:
    """
    Log an AI interaction to the database permanently.
    """
    try:
        # Create the user input log
        ai_log = AILog(user_id=user_id, plant_id=request.plant_id,
                       input_text=request.input_text, type=log_type, is_permanent=True)
        db.add(ai_log)
        db.commit()
        db.refresh(ai_log)

        # Create the AI response
        ai_response = AIResponse(ai_log_id=ai_log.id, user_id=user_id, response_text=response, is_permanent=True)
        db.add(ai_response)
        db.commit()
        db.refresh(ai_response)
        return ai_log
    except Exception as e:
        db.rollback()
        print(f"Error in log_ai_interaction: {str(e)}")
        raise


def create_new_session(db: Session, user_id: int) -> str:
    """Create a new conversation session and return session ID."""
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create new session record
        session = ConversationSession(user_id=user_id, session_id=session_id, is_active=True)
        db.add(session)
        db.commit()
        return session_id
    except Exception as e:
        db.rollback()
        print(f"Error in create_new_session: {str(e)}")
        raise


def get_current_session_id(db: Session, user_id: int) -> str:
    """Get the current active session ID for the user."""
    try:
        session = db.query(ConversationSession).filter(ConversationSession.user_id == user_id,
                                                       ConversationSession.is_active == True
                                                       ).order_by(ConversationSession.created_at.desc()).first()
        if session:
            return session.session_id
        else:
            # Create new session if none exists
            return create_new_session(db, user_id)
    except Exception as e:
        print(f"Error in get_current_session_id: {str(e)}")
        # Create new session as fallback
        return create_new_session(db, user_id)


def save_chat_message(db: Session, user_id: int, text: str, is_user: bool, session_id: str = None):
    """Save a chat message to the database with session ID."""
    try:
        # Get current session ID if not provided
        if not session_id:
            session_id = get_current_session_id(db, user_id)

        if is_user:
            # Save user input
            ai_log = AILog(user_id=user_id, input_text=text, type="chat", session_id=session_id, is_permanent=True)
            db.add(ai_log)
            db.commit()
            db.refresh(ai_log)
            return ai_log
        else:
            # Save AI response - find the most recent user input without response
            latest_user_input = db.query(AILog).filter(AILog.user_id == user_id,
                                                       AILog.input_text.isnot(None), AILog.type == "chat",
                                                       AILog.session_id == session_id, AILog.is_permanent == True
                                                       ).order_by(AILog.created_at.desc()).first()
            if latest_user_input:
                # Check if this user input already has a response
                existing_response = db.query(AIResponse).filter(AIResponse.ai_log_id == latest_user_input.id).first()

                if not existing_response:
                    # Create new AI response
                    ai_response = AIResponse(ai_log_id=latest_user_input.id, user_id=user_id,
                                             response_text=text, is_permanent=True)
                    db.add(ai_response)
                    db.commit()
                    db.refresh(ai_response)
                    return latest_user_input
            else:
                # If no user input found, create a standalone AI response. This handles the welcome message case
                ai_response = AIResponse(ai_log_id=None, user_id=user_id, response_text=text, is_permanent=True)
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
    """Get current session chat history for display."""
    try:
        # Get current session ID
        session_id = get_current_session_id(db, user_id)

        # Get all AI logs for the current session
        logs = db.query(AILog).filter(AILog.user_id == user_id, AILog.type == "chat",
                                      AILog.session_id == session_id, AILog.is_permanent == True
                                      ).order_by(AILog.created_at).all()
        history = []
        # Process each log entry
        for log in logs:
            # Only add user message if there's also an AI response
            ai_response = db.query(AIResponse).filter(AIResponse.ai_log_id == log.id).first()
            if log.input_text and ai_response:
                # Add user message
                history.append({"is_user": True, "text": log.input_text, "created_at": log.created_at})
                # Add AI response
                history.append({"is_user": False, "text": ai_response.response_text,
                                "created_at": ai_response.created_at })
        # Also get standalone AI responses for this session (like welcome messages)
        # We'll need to track welcome messages with session ID too. Get most recent welcome message
        standalone_responses = db.query(AIResponse).filter(AIResponse.user_id == user_id,
                                                           AIResponse.ai_log_id.is_(None),
                                                           AIResponse.is_permanent == True
                                                           ).order_by(AIResponse.created_at.desc()).limit(1).all()

        for response in standalone_responses:
            history.append({"is_user": False, "text": response.response_text, "created_at": response.created_at})

        # Sort by creation time
        history.sort(key=lambda x: x["created_at"])
        for item in history:
            item["timestamp"] = item["created_at"].strftime("%H:%M") # Add timestamps to the final result
            del item["created_at"]
        return history
    except Exception as e:
        print(f"Error in get_chat_history: {str(e)}")
        return []


def get_current_session_chat_history(db: Session, user_id: int, session_start_time=None) -> list[dict]:
    """Get only current session chat history for display (from session start time)."""
    try:
        # If no session start time provided, get the most recent conversation
        if not session_start_time:
            # Get the most recent AI response to determine session start
            latest_response = db.query(AIResponse).filter(AIResponse.user_id == user_id,
                                                          AIResponse.is_permanent == True
                                                          ).order_by(AIResponse.created_at.desc()).first()
            if latest_response:
                session_start_time = latest_response.created_at
            else:
                return []
        # Get AI logs from session start time onwards
        logs = db.query(AILog).filter(AILog.user_id == user_id, AILog.type == "chat",
                                      AILog.is_permanent == True, AILog.created_at >= session_start_time
                                      ).order_by(AILog.created_at).all()
        history = []
        # Process each log entry
        for log in logs:
            # Only add user message if there's also an AI response
            ai_response = db.query(AIResponse).filter(AIResponse.ai_log_id == log.id).first()
            if log.input_text and ai_response:
                # Add user message and AI response
                history.append({"is_user": True,"text": log.input_text,"created_at": log.created_at})
                history.append({"is_user": False,"text": ai_response.response_text,
                                "created_at": ai_response.created_at })
        # Also get standalone AI responses from session start time
        standalone_responses = db.query(AIResponse).filter(AIResponse.user_id == user_id,
                                                           AIResponse.ai_log_id.is_(None),
                                                           AIResponse.is_permanent == True,
                                                           AIResponse.created_at >= session_start_time
                                                           ).order_by(AIResponse.created_at).all()
        for response in standalone_responses:
            history.append({"is_user": False, "text": response.response_text, "created_at": response.created_at})

        history.sort(key=lambda x: x["created_at"]) # Sort by creation time
        # Add timestamps to the final result
        for item in history:
            item["timestamp"] = item["created_at"].strftime("%H:%M")
            del item["created_at"]
        return history
    except Exception as e:
        print(f"Error in get_current_session_chat_history: {str(e)}")
        return []


def get_session_start_time(db: Session, user_id: int) -> datetime:
    """Get the start time of the current session (when user first accessed chat)."""
    try:
        # Get the most recent AI response to determine session start
        latest_response = db.query(AIResponse).filter(AIResponse.user_id == user_id,
                                                      AIResponse.is_permanent == True
                                                      ).order_by(AIResponse.created_at.desc()).first()
        if latest_response:
            return latest_response.created_at
        else:
            return datetime.now()
    except Exception as e:
        print(f"Error in get_session_start_time: {str(e)}")
        return datetime.now()


def get_complete_conversation_history(db: Session, user_id: int) -> str:
    """Get complete conversation history for AI context (all past conversations)."""
    try:
        # Get all permanent conversations for the user (all sessions)
        logs = db.query(AILog).filter(AILog.user_id == user_id, AILog.type == "chat",
                                      AILog.is_permanent == True).order_by(AILog.created_at).all()
        conversation_lines = []
        for log in logs:
            conversation_lines.append(f"User: {log.input_text}")  # Add user message
            ai_response = db.query(AIResponse).filter(AIResponse.ai_log_id == log.id).first()  # Add AI response
            if ai_response:
                conversation_lines.append(f"PlantPal: {ai_response.response_text}")
        # Also get standalone AI responses
        standalone_responses = db.query(AIResponse).filter(AIResponse.user_id == user_id,
                                                           AIResponse.ai_log_id.is_(None),
                                                           AIResponse.is_permanent == True
                                                           ).order_by(AIResponse.created_at).all()
        for response in standalone_responses:
            conversation_lines.append(f"PlantPal: {response.response_text}")
        return "\n".join(conversation_lines)
    except Exception as e:
        print(f"Error in get_complete_conversation_history: {str(e)}")
        return ""


def get_user_input_history(db: Session, user_id: int) -> list[str]:
    """Get only user input history for creating summary."""
    try:
        logs = db.query(AILog).filter(AILog.user_id == user_id, AILog.input_text.isnot(None),
                                      AILog.type == "chat", AILog.is_permanent == True
                                      ).order_by(AILog.created_at).all()
        return [log.input_text for log in logs]
    except Exception as e:
        print(f"Error in get_user_input_history: {str(e)}")
        return []


def has_existing_conversation(db: Session, user_id: int) -> bool:
    """Check if user has any existing conversation history."""
    try:
        # Check if there are any AI responses for this user
        count = db.query(AIResponse).filter(AIResponse.user_id == user_id,
                                            AIResponse.is_permanent == True).count()
        return count > 0
    except Exception as e:
        print(f"Error in has_existing_conversation: {str(e)}")
        return False


def get_latest_user_input(db: Session, user_id: int):
    """Get the most recent user input that doesn't have an AI response yet."""
    try:
        # Find the most recent user input without a response
        latest_input = db.query(AILog).filter(AILog.user_id == user_id, AILog.input_text.isnot(None),
                                              AILog.type == "chat", AILog.is_permanent == True
                                              ).order_by(AILog.created_at.desc()).first()
        if latest_input:
            # Check if this input has a response
            has_response = db.query(AIResponse).filter(AIResponse.ai_log_id == latest_input.id).first()
            if not has_response:
                return latest_input.input_text
        return None
    except Exception as e:
        print(f"Error in get_latest_user_input: {str(e)}")
        return None


def clear_session(db: Session, user_id: int):
    """Clear current session when user logs out."""
    try:
        # Mark current session as inactive
        session = db.query(ConversationSession).filter(ConversationSession.user_id == user_id,
                                                       ConversationSession.is_active == True).first()
        if session:
            session.is_active = False
            session.ended_at = datetime.now()
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error in clear_session: {str(e)}")


def check_duplicate_question(db: Session, user_id: int, user_message: str):
    """Check if user has asked this question before and return duplicate info if found."""
    try:
        # Normalize the user message for comparison (remove extra spaces, convert to lowercase)
        normalized_message = ' '.join(user_message.lower().split())
        # Get all previous user inputs for this user
        previous_inputs = db.query(AILog).filter(AILog.user_id == user_id, AILog.input_text.isnot(None),
                                                 AILog.type == "chat", AILog.is_permanent == True
                                                 ).order_by(AILog.created_at.desc()).all()
        for prev_input in previous_inputs:
            # Normalize previous message for comparison
            normalized_prev = ' '.join(prev_input.input_text.lower().split())
            # Check for exact match or very similar questions (90% similarity threshold)
            if normalized_message == normalized_prev:
                # Exact match found
                return {'ai_log_id': prev_input.id, 'original_question': prev_input.input_text, 'match_type': 'exact'}
            elif len(normalized_message) > 10 and len(normalized_prev) > 10:
                # Check for similarity (simple word overlap for now)
                message_words = set(normalized_message.split())
                prev_words = set(normalized_prev.split())
                if len(message_words) > 0 and len(prev_words) > 0:
                    overlap = len(message_words.intersection(prev_words))
                    total_words = len(message_words.union(prev_words))
                    similarity = overlap / total_words if total_words > 0 else 0
                    if similarity >= 0.8:  # 80% similarity threshold
                        return {'ai_log_id': prev_input.id, 'original_question': prev_input.input_text,
                            'match_type': 'similar', 'similarity': similarity
                        }
        return None  # No duplicate found
    except Exception as e:
        print(f"Error in check_duplicate_question: {str(e)}")
        return None


def update_existing_response(db: Session, ai_log_id: int, new_response: str):
    """Update an existing AI response with a new response."""
    try:
        # Find the existing AI response for this log
        existing_response = db.query(AIResponse).filter(AIResponse.ai_log_id == ai_log_id).first()
        if existing_response:
            # Update the response text
            existing_response.response_text = new_response
            existing_response.created_at = datetime.now()
            db.commit()
            return existing_response
        else:
            print(f"No existing response found for ai_log_id: {ai_log_id}")
            return None
    except Exception as e:
        db.rollback()
        print(f"Error in update_existing_response: {str(e)}")
        return None


def get_last_user_question(db: Session, user_id: int):
    """Get the user's most recent question."""
    try:
        # Get the most recent user input that has an AI response
        latest_input = db.query(AILog).filter(AILog.user_id == user_id, AILog.input_text.isnot(None),
                                              AILog.type == "chat", AILog.is_permanent == True
                                              ).order_by(AILog.created_at.desc()).first()
        if latest_input:
            # Check if this input has a response
            has_response = db.query(AIResponse).filter(AIResponse.ai_log_id == latest_input.id).first()
            if has_response:
                return latest_input.input_text
        return None
    except Exception as e:
        print(f"Error in get_last_user_question: {str(e)}")
        return None

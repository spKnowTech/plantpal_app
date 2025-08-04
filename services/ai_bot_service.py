from repositories.plant_repo import get_user_plants
from repositories.ai_bot_repo import (
    save_chat_message, 
    get_chat_history, 
    get_user_input_history,
    create_new_session,
    get_current_session_id,
    clear_session,
    check_duplicate_question,
    update_existing_response,
    get_last_user_question
)
from plant_pal_bot.ai_bot_chat import answer_user_question, extract_and_update_plant_info, generate_history_summary
from datetime import datetime


def get_chat_history_service(db, user_id):
    """Get the chat history for the specified user."""
    return get_chat_history(db, user_id)

def save_user_message_service(db, user_id, message):
    """Save a user message to the chat history."""
    return save_chat_message(db, user_id, message, is_user=True)

def save_bot_message_service(db, user_id, message):
    """Save a bot message to the chat history."""
    return save_chat_message(db, user_id, message, is_user=False)


def create_welcome_message(db, user_id, user_full_name, plants):
    """Create a personalized welcome message for fresh conversation."""
    welcome_msg = f"🌱 Hello {user_full_name}! Welcome to **PlantPal!** 🌱\n\n"
    welcome_msg +="""I'm your AI gardening assistant! I can help you with:"
    • Plant care advice and tips"
    • Watering and fertilizing schedules"
    • Disease and pest identification"
    • General gardening questions"
    
    💡 Tip: Add some plants to your dashboard first for personalized care advice!"
    
    How can I help you today? 🌿"""
    
    return welcome_msg

def match_user_input_with_plants(db, user_id, user_message):
    """Match user input with their plants in the database."""
    plants = get_user_plants(db, user_id)
    if not plants:
        return None
    
    user_message_lower = user_message.lower()
    matched_plants = []
    
    for plant in plants:
        # Check if plant name, species, or nickname is mentioned
        plant_name_lower = plant.name.lower()
        if plant.species:
            species_lower = plant.species.lower()
        else:
            species_lower = ""
        if plant.nickname:
            nickname_lower = plant.nickname.lower()
        else:
            nickname_lower = ""
        
        # Check for exact matches or partial matches
        if (plant_name_lower in user_message_lower or 
            user_message_lower in plant_name_lower or
            (species_lower and species_lower in user_message_lower) or
            (nickname_lower and nickname_lower in user_message_lower)):
            matched_plants.append(plant)
    
    return matched_plants[0] if matched_plants else None

def is_summary_request(user_message: str) -> bool:
    """Check if user is asking for a summary of previous chat history."""
    user_message_lower = user_message.lower()
    
    summary_keywords = [
        "summary", "summarize", "recap", "recapitulate", "overview",
        "what have we talked about", "what did we discuss", "our conversation",
        "previous chat", "chat history", "what we discussed", "our talks",
        "conversation summary", "chat summary", "what we covered",
        "remind me what", "what was our conversation", "history of our chat"
    ]
    
    return any(keyword in user_message_lower for keyword in summary_keywords)

def is_last_question_request(user_message: str) -> bool:
    """Check if user is asking for their last question."""
    user_message_lower = user_message.lower()
    
    last_question_keywords = [
        "what was my last question", "my last question", "last question",
        "what did i ask last", "what was the last thing i asked",
        "what question did i ask last", "my previous question",
        "what was my previous question", "last thing i asked",
        "what did i ask before", "my earlier question"
    ]
    
    return any(keyword in user_message_lower for keyword in last_question_keywords)

def get_last_question_response(db, user_id: int) -> str:
    """Get the user's last question and provide a response."""
    try:
        last_question = get_last_user_question(db, user_id)
        
        if not last_question:
            return "🌱 You haven't asked any questions yet! This is our first conversation. Feel free to ask me anything about your plants and gardening! 🌿"
        
        return f"🌱 Your last question was: **\"{last_question}\"** 🌿\n\nWould you like me to answer it again or do you have a new question?"
    except Exception as e:
        print(f"Error getting last question: {str(e)}")
        return "🌱 I'm having trouble retrieving your last question right now. Please ask me something new! 🌿"

def generate_chat_summary(db, user_id: int) -> str:
    """Generate a summary of the user's previous chat history."""
    try:
        # Get user's input history
        user_history = get_user_input_history(db, user_id)
        
        if not user_history:
            return "🌱 We haven't had any previous conversations yet! This is our first chat. Feel free to ask me anything about your plants and gardening! 🌿"
        
        # Use the existing generate_history_summary function
        from plant_pal_bot.ai_bot_chat import generate_history_summary
        summary = generate_history_summary(user_history)
        
        if not summary:
            # Fallback summary
            summary = f"🌱 Based on our previous conversations, I remember you've been asking about plant care topics including {', '.join(user_history[-3:])}. How can I help you today? 🌿"
        
        return summary
    except Exception as e:
        print(f"Error generating chat summary: {str(e)}")
        return "🌱 I remember we've had some great conversations about your plants! How can I help you today? 🌿"

def handle_ai_chat(db, user_id, user_message, plant_id=None):
    """Handle AI chat interaction, including message saving and response generation."""
    try:
        # Check if user is asking for their last question
        if is_last_question_request(user_message):
            # Generate last question response
            last_question_response = get_last_question_response(db, user_id)
            
            # Save user message
            save_user_message_service(db, user_id, user_message)
            
            # Save bot response
            save_bot_message_service(db, user_id, last_question_response)
            
            return last_question_response
        
        # Check if user is asking for a summary
        if is_summary_request(user_message):
            # Generate summary response
            summary_response = generate_chat_summary(db, user_id)
            
            # Save user message
            save_user_message_service(db, user_id, user_message)
            
            # Save bot summary response
            save_bot_message_service(db, user_id, summary_response)
            
            return summary_response
        
        # Check if this is a duplicate question
        duplicate_info = check_duplicate_question(db, user_id, user_message)
        
        if duplicate_info:
            # This is a duplicate question - update the existing response
            ai_log = answer_user_question(db, user_id, user_message, plant_id)
            new_response = ai_log.ai_response
            
            # Update the existing response in the database
            update_existing_response(db, duplicate_info['ai_log_id'], new_response)
            
            # Save user message (for current session display)
            save_user_message_service(db, user_id, user_message)
            
            # Save updated bot response (for current session display)
            save_bot_message_service(db, user_id, new_response)
            
            # Optionally update plant info from chat
            if plant_id:
                extract_and_update_plant_info(db, user_id, plant_id, user_message, new_response)
            
            return new_response
        
        # This is a new question - proceed normally
        # Save user message first
        save_user_message_service(db, user_id, user_message)
        
        # If no plant_id provided, try to match user input with plants
        if not plant_id:
            matched_plant = match_user_input_with_plants(db, user_id, user_message)
            if matched_plant:
                plant_id = matched_plant.id
        
        # Generate bot response (plant/gardening only)
        ai_log = answer_user_question(db, user_id, user_message, plant_id)
        
        # Save bot message
        save_bot_message_service(db, user_id, ai_log.ai_response)
        
        # Optionally update plant info from chat
        if plant_id:
            extract_and_update_plant_info(db, user_id, plant_id, user_message, ai_log.ai_response)
        
        return ai_log.ai_response
    except Exception as e:
        print(f"Error in handle_ai_chat: {str(e)}")
        # Return a fallback response
        return "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment."

def start_fresh_conversation(db, user_id, user_full_name, plants):
    """Start a fresh conversation with welcome message."""
    # Create new session
    session_id = create_new_session(db, user_id)
    
    welcome_msg = create_welcome_message(db, user_id, user_full_name, plants)
    
    # Save the welcome message as a bot message with session ID
    save_bot_message_service(db, user_id, welcome_msg)
    
    return welcome_msg

def clear_user_session(db, user_id):
    """Clear user session when logging out."""
    clear_session(db, user_id)

def get_current_session_chat_history_service(db, user_id):
    """Get only current session chat history for display."""
    from repositories.ai_bot_repo import get_current_session_chat_history, get_session_start_time
    
    session_start_time = get_session_start_time(db, user_id)
    return get_current_session_chat_history(db, user_id, session_start_time)
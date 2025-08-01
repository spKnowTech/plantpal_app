from repositories.plant_repo import get_user_plants
from repositories.ai_bot_repo import save_chat_message, get_chat_history, get_user_input_history, clear_ai_responses
from plant_pal_bot.ai_bot_chat import answer_user_question, extract_and_update_plant_info, generate_history_summary


def get_chat_history_service(db, user_id):
    return get_chat_history(db, user_id)

def save_user_message_service(db, user_id, message):
    return save_chat_message(db, user_id, message, is_user=True)

def save_bot_message_service(db, user_id, message):
    return save_chat_message(db, user_id, message, is_user=False)



def create_welcome_message(db, user_id, user_full_name, plants):
    """Create a personalized welcome message with user history."""
    welcome_msg = f"🌱 Hello {user_full_name}! Welcome to PlantPal! 🌱\n\n"
    
    # Get user's previous conversation history (only input text, not AI responses)
    user_history = get_user_input_history(db, user_id)
    
    if user_history:
        # Generate a proper history paragraph using AI
        history_summary = generate_history_summary(user_history)
        welcome_msg += f"{history_summary}\n\n"
    
    welcome_msg += "How may I help you? Type your question to start a conversation! 🌿"
    
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

def handle_ai_chat(db, user_id, user_message, plant_id=None):
    try:
        # User message is already saved in the router, so we don't save it again here
        
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

def clear_user_conversation(db, user_id):
    """Clear all AI responses for a user (called on logout)."""
    clear_ai_responses(db, user_id)
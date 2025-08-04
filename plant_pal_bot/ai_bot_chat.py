# Orchestrates the user input, command parsing, prompt construction, OpenAI call, and logging of AI responses.

from plant_pal_bot.ai_bot_client import ask_gpt4o
from repositories.ai_bot_repo import get_complete_conversation_history
from repositories.plant_repo import find_plant_by_name, update_plant, create_default_care_tasks
from models.ai_bot import AILog
from schemas.ai_bot import AIChatRequest
from schemas.plant import PlantUpdate
from sqlalchemy.orm import Session
import re
from datetime import date, timedelta

PLANT_KEYWORDS = [
    "plant", "watering", "fertilizer", "soil", "leaves", "sunlight", "photosynthesis",
    "pruning", "repotting", "disease", "pests", "growth", "root", "stem", "flower",
    "garden", "gardening", "care", "maintenance", "health", "growth", "bloom", "seeds",
    "pot", "container", "indoor", "outdoor", "climate", "temperature", "humidity",
    "nutrients", "organic", "natural", "green", "foliage", "bud", "sprout", "seedling",
    "water", "fertilize", "prune", "repot", "transplant", "propagate", "grow", "nurture",
    "cactus", "succulent", "monstera", "ficus", "pothos", "philodendron", "orchid",
    "rose", "tulip", "daffodil", "lily", "daisy", "sunflower", "marigold", "petunia",
    "herb", "basil", "mint", "rosemary", "thyme", "sage", "oregano", "parsley",
    "vegetable", "tomato", "pepper", "lettuce", "spinach", "carrot", "onion", "garlic",
    "fruit", "apple", "orange", "lemon", "lime", "grape", "strawberry", "blueberry"
]

WELCOME_TEXT = (
    " **Welcome to PlantPal AI!**\n\n"
    "I'm your smart plant care assistant, here to help you grow, nurture, and understand your plants like never before! "
    "Ask me anything about your green friends, and let's make your plant journey amazing together.\n\n"
    "To get started, please tell me about a new plant you'd like to add to your collection. "
    "I'll also show you your existing plant history below."
)

RESTRICTED_TEXT = (
    "🌿 I'm sorry, but I can only help with plant and gardening related questions! "
    "I'm your PlantPal AI assistant, specialized in:\n\n"
    "• Plant care and maintenance\n"
    "• Watering and fertilizing schedules\n"
    "• Disease and pest identification\n"
    "• Gardening tips and advice\n"
    "• Plant identification and recommendations\n\n"
    "Please ask me something about your plants or gardening! 🌱"
)

def is_plant_related(text: str) -> bool:
    """Enhanced plant-related detection with more comprehensive keyword matching."""
    text_lower = text.lower()
    
    # Check for plant-related keywords
    if any(keyword in text_lower for keyword in PLANT_KEYWORDS):
        return True
    
    # Check for common plant care phrases
    plant_phrases = [
        "how to", "care for", "take care", "look after", "maintain",
        "water", "fertilize", "prune", "repot", "transplant",
        "growing", "planting", "seeding", "sowing",
        "leaves", "flowers", "roots", "stems",
        "indoor", "outdoor", "garden", "yard", "balcony",
        "sunlight", "shade", "temperature", "humidity",
        "soil", "pot", "container", "planter"
    ]
    
    if any(phrase in text_lower for phrase in plant_phrases):
        return True
    
    # Check for question words that might be about plants
    question_words = ["what", "when", "where", "why", "how", "which"]
    if any(word in text_lower for word in question_words):
        # If it's a question, be more lenient but still check for plant context
        return any(keyword in text_lower for keyword in PLANT_KEYWORDS[:20])  # Use core keywords
    
    return False

def extract_plant_info_from_text(text: str) -> dict:
    """Extract plant information from user text using AI."""
    prompt = f"""
    Extract plant information from the following text. Return only a JSON object with the following fields if found:
    - name: plant name
    - species: plant species/scientific name
    - nickname: any nickname mentioned
    - location: where the plant is located (indoor/outdoor, room, etc.)
    - sunlight: sunlight requirements mentioned
    - watering_interval: watering frequency mentioned (in days)
    - notes: any other relevant information

    Text: "{text}"

    Return only valid JSON or "null" if no plant information is found.
    """

    try:
        response = ask_gpt4o(
            prompt=prompt,
            system_prompt="You are a plant information extractor. Extract only plant-related information and return it as JSON. If no plant information is found, return 'null'."
        )
        
        # Try to parse JSON response
        import json
        try:
            plant_info = json.loads(response.strip())
            if plant_info and plant_info != "null":
                return plant_info
        except json.JSONDecodeError:
            pass
        
        return {}
    except Exception as e:
        print(f"Error extracting plant info: {str(e)}")
        return {}

def should_create_care_tasks(text: str) -> bool:
    """Check if user wants care tasks created for their plant."""
    text_lower = text.lower()
    
    care_task_indicators = [
        "care task", "care schedule", "reminder", "schedule", "routine",
        "when to water", "when to fertilize", "watering schedule", "fertilizing schedule",
        "care plan", "maintenance schedule", "care routine", "watering reminder",
        "yes", "sure", "okay", "ok", "please", "that would be great", "that sounds good",
        "create", "set up", "establish", "start", "begin"
    ]
    
    return any(indicator in text_lower for indicator in care_task_indicators)

def generate_history_summary(user_history: list[str]) -> str:
    """Generate a natural paragraph summary of user's conversation history using AI."""
    if not user_history:
        return ""
    
    # Create a prompt for the AI to generate a natural history summary
    history_text = "\n".join([f"- {text}" for text in user_history])
    
    prompt = f"""Based on the following user conversation history, create a natural, friendly paragraph that summarizes what the user has been asking about. Make it conversational and engaging, not a bullet point list.

User's previous questions:
{history_text}

Please create a 2-3 sentence paragraph that naturally flows and summarizes their plant care interests and concerns. Include specific topics they've asked about and any patterns in their questions."""

    try:
        summary = ask_gpt4o(
            prompt=prompt,
            system_prompt="You are PlantPal, a friendly plant care assistant. Create natural, conversational summaries of user's plant care history. Keep it warm and engaging. Focus on their specific plant care interests and any recurring themes in their questions."
        )
        return summary
    except Exception as e:
        print(f"Error generating history summary: {str(e)}")
        # Fallback to a simple summary
        if len(user_history) >= 3:
            return f"🌱 Based on our previous conversations, I remember you've been asking about plant care topics including {', '.join(user_history[-3:])}. You seem very interested in taking good care of your plants! 🌿"
        else:
            return f"🌱 We've had some great conversations about {', '.join(user_history)}. How can I help you today? 🌿"

def fix_numbered_lists(text: str) -> str:
    """Fix numbered lists to ensure proper sequential numbering (1, 2, 3, 4, 5...)."""
    lines = text.split('\n')
    fixed_lines = []
    list_counter = 1
    in_list = False
    
    for line in lines:
        stripped_line = line.strip()
        
        # Check if line starts with a number followed by a period and space
        if re.match(r'^\d+\.\s', stripped_line):
            # Extract content after the number and period
            content = re.sub(r'^\d+\.\s*', '', stripped_line)
            # Replace with correct sequential number
            fixed_line = f'{list_counter}. {content}'
            fixed_lines.append(fixed_line)
            list_counter += 1
            in_list = True
        else:
            # If we were in a list and now we're not, reset counter
            if in_list and stripped_line and not stripped_line.startswith('•') and not stripped_line.startswith('-'):
                list_counter = 1
                in_list = False
            fixed_lines.append(line)
    
    result = '\n'.join(fixed_lines)
    return result

def check_similar_past_questions(db: Session, user_id: int, current_question: str) -> str:
    """Check if user has asked similar questions before and return relevant past responses."""
    try:
        # Get complete conversation history
        complete_history = get_complete_conversation_history(db, user_id)
        
        if not complete_history:
            return ""
        
        # Create a prompt to find similar past questions
        prompt = f"""
        Analyze the following conversation history and the current user question to find if they've asked something similar before.

        COMPLETE CONVERSATION HISTORY:
        {complete_history}

        CURRENT USER QUESTION:
        {current_question}

        If the user has asked a similar question before, provide a brief reference to that past conversation and what was discussed. 
        If this is a completely new topic, return "NEW_TOPIC".

        Format your response as:
        - If similar: "PAST_REFERENCE: [brief mention of past conversation]"
        - If new: "NEW_TOPIC"
        """
        
        try:
            response = ask_gpt4o(
                prompt=prompt,
                system_prompt="You are analyzing conversation history to find similar past questions. Be concise and accurate."
            )
            return response.strip()
        except Exception as e:
            print(f"Error checking similar questions: {str(e)}")
            return ""
            
    except Exception as e:
        print(f"Error in check_similar_past_questions: {str(e)}")
        return ""

def answer_user_question(db: Session, user_id: int, user_message: str, plant_id: int = None) -> AILog:
    """Enhanced AI response function with complete conversation history and memory."""
    if not is_plant_related(user_message):
        ai_response = RESTRICTED_TEXT
        # Don't log the interaction here since user message is already saved
        # Just return a mock log object with the response
        class MockAILog:
            def __init__(self, response):
                self.ai_response = response
        
        return MockAILog(ai_response)

    # Get complete conversation history for context
    complete_history = get_complete_conversation_history(db, user_id)
    
    # Check for similar past questions
    past_reference = check_similar_past_questions(db, user_id, user_message)
    
    # Extract plant information from user message
    plant_info = extract_plant_info_from_text(user_message)
    
    # If plant information is found, try to find or update the plant
    if plant_info and plant_info.get('name'):
        plant_name = plant_info['name']
        existing_plant = find_plant_by_name(db, plant_name, user_id)
        
        if existing_plant:
            # Update existing plant with new information
            update_data = {}
            for key, value in plant_info.items():
                if key == 'name':
                    continue  # Don't update the name
                if key == 'watering_interval' and value:
                    update_data['watering_interval_days'] = int(value)
                elif key in ['species', 'nickname', 'location', 'sunlight', 'notes'] and value:
                    update_data[key] = value
            
            if update_data:
                update_plant(db, existing_plant.id, PlantUpdate(**update_data), user_id)
                plant_id = existing_plant.id
        else:
            # Create new plant if not found
            from repositories.plant_repo import create_plant
            from schemas.plant import PlantCreate
            
            plant_data = {
                'name': plant_name,
                'location': plant_info.get('location', 'Indoor'),
                'species': plant_info.get('species'),
                'nickname': plant_info.get('nickname'),
                'sunlight': plant_info.get('sunlight'),
                'watering_interval_days': int(plant_info.get('watering_interval', 7)),
                'notes': plant_info.get('notes')
            }
            
            new_plant = create_plant(db, PlantCreate(**plant_data), user_id)
            plant_id = new_plant.id

    # Check if user wants care tasks
    wants_care_tasks = should_create_care_tasks(user_message)
    
    # Build intelligent system prompt with complete history
    history_context = ""
    if complete_history:
        history_context = f"""
COMPLETE CONVERSATION HISTORY:
{complete_history}

"""
    
    past_reference_context = ""
    if past_reference and past_reference != "NEW_TOPIC":
        past_reference_context = f"""
PAST REFERENCE: {past_reference}
"""
    
    # Create intelligent system prompt
    system_prompt = f"""You are PlantPal, an expert plant care assistant with complete memory of all past conversations.

{history_context}{past_reference_context}
INSTRUCTIONS:
1. Be engaging and conversational. Use emojis occasionally.
2. You have access to ALL past conversations with this user - use this knowledge to provide personalized responses.
3. If the user asks something similar to what they've asked before, acknowledge this and reference the past conversation briefly.
4. If they mentioned their plant type, watering schedule, light conditions, or issues in past conversations, remember and use this information.
5. Provide specific, actionable advice based on their complete history.
6. If they want care tasks, create them immediately if you have enough information from past conversations.
7. Be helpful and avoid repetitive questions they've already answered.
8. Use numbered lists when providing multiple points, but make them sequential (1, 2, 3, 4, 5...).
9. Make the conversation feel continuous and personal - like you remember everything about their plant journey.

Current user message: {user_message}"""

    ai_response = ask_gpt4o(
        prompt=user_message,
        system_prompt=system_prompt
    )
    
    # Fix any numbered lists in the response to ensure proper sequential numbering
    ai_response = fix_numbered_lists(ai_response)
    
    # If user wants care tasks and we have a plant, create them
    if wants_care_tasks and plant_id:
        try:
            plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user_id).first()
            if plant:
                care_tasks = create_default_care_tasks(db, plant_id, plant)
                ai_response += f"\n\n✅ I've created care tasks for your {plant.name}! You'll now get reminders for watering, fertilizing, and health checks."
        except Exception as e:
            print(f"Error creating care tasks: {str(e)}")
    
    # Don't log the interaction here since user message is already saved
    # Just return a mock log object with the response
    class MockAILog:
        def __init__(self, response):
            self.ai_response = response
    
    return MockAILog(ai_response)

def extract_and_update_plant_info(db: Session, user_id: int, plant_id: int, user_message: str, ai_response: str):
    """Extract plant details from conversation and update the plant in DB if new info is found."""
    # Simple regex/keyword extraction (expand as needed)
    species = None
    nickname = None
    
    # Example: "My plant's species is Ficus lyrata and I call it Figgy."
    species_match = re.search(r"species is ([\w\s]+)[\.,]?", user_message, re.IGNORECASE)
    if not species_match:
        species_match = re.search(r"species is ([\w\s]+)[\.,]?", ai_response, re.IGNORECASE)
    if species_match:
        species = species_match.group(1).strip()
    
    nickname_match = re.search(r"call (it|him|her|my plant) ([\w\s]+)[\.,]?", user_message, re.IGNORECASE)
    if not nickname_match:
        nickname_match = re.search(r"nickname is ([\w\s]+)[\.,]?", user_message, re.IGNORECASE)
    if not nickname_match:
        nickname_match = re.search(r"nickname is ([\w\s]+)[\.,]?", ai_response, re.IGNORECASE)
    if nickname_match:
        nickname = nickname_match.group(2).strip() if nickname_match.lastindex == 2 else nickname_match.group(1).strip()
    
    # Only update if new info is found
    if species or nickname:
        update_data = {}
        if species:
            update_data["species"] = species
        if nickname:
            update_data["nickname"] = nickname
        update_plant(db, plant_id, PlantUpdate(**update_data), user_id)

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

def generate_chat_summary(db, user_id: int) -> str:
    """Generate a summary of the user's previous chat history."""
    try:
        # Use the detailed conversation summary function
        from plant_pal_bot.ai_bot_chat import generate_detailed_conversation_summary
        summary = generate_detailed_conversation_summary(db, user_id)
        
        return summary
    except Exception as e:
        print(f"Error generating chat summary: {str(e)}")
        return "🌱 I remember we've had some great conversations about your plants! How can I help you today? 🌿"

def generate_detailed_conversation_summary(db: Session, user_id: int) -> str:
    """Generate a detailed summary of the complete conversation including both user questions and bot responses."""
    try:
        # Get complete conversation history
        complete_history = get_complete_conversation_history(db, user_id)
        
        if not complete_history:
            return "🌿 We haven't had any previous conversations yet! This is our first chat. Feel free to ask me anything about your plants and gardening! 🌿"
        
        prompt = f"""Based on the following complete conversation history between a user and PlantPal (an AI plant care assistant), create a comprehensive but concise summary of what we've discussed.

COMPLETE CONVERSATION HISTORY:
{complete_history}

Please create a friendly, natural summary that includes:
1. The main topics and questions the user has asked about
2. Any specific plants they've mentioned
3. Key advice or solutions I've provided
4. Any patterns or recurring themes in their plant care journey

Make it conversational and engaging, as if I'm reminiscing about our conversations together."""

        try:
            summary = ask_gpt4o(
                prompt=prompt,
                system_prompt="You are PlantPal, a friendly plant care assistant. Create natural, conversational summaries of complete conversations. Keep it warm and personal, as if you're reminiscing about your time helping the user with their plants."
            )
            return summary
        except Exception as e:
            print(f"Error generating detailed conversation summary: {str(e)}")
            # Fallback to user input history summary
            user_history = get_user_input_history(db, user_id)
            return generate_history_summary(user_history)
            
    except Exception as e:
        print(f"Error in generate_detailed_conversation_summary: {str(e)}")
        return "🌱 I remember we've had some great conversations about your plants! How can I help you today? 🌿"

def handle_ai_chat(db, user_id, user_message, plant_id=None):
    """Handle AI chat interaction, including message saving and response generation."""
    try:
        # Check if user is asking for a summary
        if is_summary_request(user_message):
            # Generate summary response
            summary_response = generate_chat_summary(db, user_id)
            
            # Save user message
            save_user_message_service(db, user_id, user_message)
            
            # Save bot summary response
            save_bot_message_service(db, user_id, summary_response)
            
            return summary_response
        
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
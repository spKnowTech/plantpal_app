# Orchestrates the user input, command parsing, prompt construction, OpenAI call, and logging of AI responses.

from plant_pal_bot.ai_bot_client import ask_gpt4o
from repositories.ai_bot_repo import log_ai_interaction
from models.ai_bot import AILog
from schemas.ai_bot import AIChatRequest
from sqlalchemy.orm import Session
import re
from repositories.plant_repo import update_plant
from schemas.plant import PlantUpdate

PLANT_KEYWORDS = [
    "plant", "watering", "fertilizer", "soil", "leaves", "sunlight", "photosynthesis",
    "pruning", "repotting", "disease", "pests", "growth", "root", "stem", "flower",
    "garden", "gardening", "care", "maintenance", "health", "growth", "bloom", "seeds",
    "pot", "container", "indoor", "outdoor", "climate", "temperature", "humidity",
    "nutrients", "organic", "natural", "green", "foliage", "bud", "sprout", "seedling"
]

WELCOME_TEXT = (
    "🌱 **Welcome to PlantPal AI!** 🌱\n\n"
    "I'm your smart plant care assistant, here to help you grow, nurture, and understand your plants like never before! "
    "Ask me anything about your green friends, and let's make your plant journey amazing together.\n\n"
    "To get started, please tell me about a new plant you'd like to add to your collection. "
    "I'll also show you your existing plant history below."
)

RESTRICTED_TEXT = (
    "I'm sorry, but I can only answer questions related to plants, gardening, and plant care. "
    "Please ask me something about your plants! 🌿"
)

def is_plant_related(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in PLANT_KEYWORDS)

def generate_history_summary(user_history: list[str]) -> str:
    """Generate a natural paragraph summary of user's conversation history using AI."""
    if not user_history:
        return ""
    
    # Create a prompt for the AI to generate a natural history summary
    history_text = "\n".join([f"- {text}" for text in user_history])
    
    prompt = f"""Based on the following user conversation history, create a natural, friendly paragraph that summarizes what the user has been asking about. Make it conversational and engaging, not a bullet point list.

User's previous questions:
{history_text}

Please create a 2-3 sentence paragraph that naturally flows and summarizes their plant care interests and concerns."""

    try:
        summary = ask_gpt4o(
            prompt=prompt,
            system_prompt="You are PlantPal, a friendly plant care assistant. Create natural, conversational summaries of user's plant care history. Keep it warm and engaging."
        )
        return summary
    except Exception as e:
        print(f"Error generating history summary: {str(e)}")
        # Fallback to a simple summary
        return f"Based on our previous conversations, I remember you've been asking about plant care topics including {', '.join(user_history[:3])}."

def answer_user_question(db: Session, user_id: int, user_message: str, plant_id: int = None) -> AILog:
    if not is_plant_related(user_message):
        ai_response = RESTRICTED_TEXT
        log = log_ai_interaction(
            db=db,
            user_id=user_id,
            request=AIChatRequest(input_text=user_message, plant_id=plant_id, type="chat"),
            response=ai_response,
            log_type="chat"
        )
        return log

    # Create a more specific prompt based on whether a plant is identified
    if plant_id:
        system_prompt = (
            "You are PlantPal, an expert plant care assistant. Focus on providing specific advice "
            "for the user's plant. Ask follow-up questions to gather more information about their plant "
            "if needed. Only answer plant-related questions. If asked about anything else, politely refuse."
        )
    else:
        system_prompt = (
            "You are PlantPal, an expert plant care assistant. Provide helpful gardening and plant care advice. "
            "Ask follow-up questions to gather more information about their plants if needed. "
            "Only answer plant-related questions. If asked about anything else, politely refuse."
        )

    ai_response = ask_gpt4o(
        prompt=user_message,
        system_prompt=system_prompt
    )
    
    log = log_ai_interaction(
        db=db,
        user_id=user_id,
        request=AIChatRequest(input_text=user_message, plant_id=plant_id, type="chat"),
        response=ai_response,
        log_type="chat"
    )
    return log

def extract_and_update_plant_info(db: Session, user_id: int, plant_id: int, user_message: str, ai_response: str):
    """
    Extract plant details from conversation and update the plant in DB if new info is found.
    """
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
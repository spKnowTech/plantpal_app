# Orchestrates the user input, command parsing, prompt construction, OpenAI call, and logging of AI responses.
from plant_pal_bot.ai_bot_client import ask_gpt4o, embed_text
from repositories.ai_bot_repo import (
    get_complete_conversation_history, get_user_input_history
)
from repositories.plant_repo import find_plant_by_name, update_plant, get_user_plants
from models.ai_bot import AILog
from schemas.plant import PlantUpdate
from sqlalchemy.orm import Session
import re
from repositories.care_task_repo import get_user_care_tasks_for_plant
from datetime import date, timedelta
import json
from repositories.plant_repo import create_plant
from schemas.plant import PlantCreate
import base64
from typing import List, Optional, Dict
from services.photo_service import (
    get_photo_context_for_chat, validate_photo_for_chat, create_photo_diagnosis
)
from plant_pal_bot.vision_analyzer import (
    analyze_plant_image_with_gpt4_vision, generate_diagnosis_summary,
    validate_image_for_analysis
)
from rag.context_builder import build_rag_context_for_diagnosis, format_rag_context_for_ai
from rag.embeddings_generator import generate_and_store_embedding

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

TASK_MANAGEMENT_KEYWORDS = [
    "task", "tasks", "schedule", "reminder", "due", "complete", "completed",
    "mark as done", "finished", "check off", "tick", "done", "todo",
    "create task", "add task", "new task", "update task", "modify task",
    "delete task", "remove task", "task history", "completed tasks",
    "pending tasks", "upcoming tasks", "today's tasks", "weekly tasks",
    "monthly tasks", "care routine", "maintenance schedule"
]

# Photo-related keywords for detection
PHOTO_ANALYSIS_KEYWORDS = [
    "photo", "image", "picture", "pic", "analyze", "diagnosis", "diagnose",
    "what's wrong", "identify", "issue", "problem", "disease", "pest",
    "looks like", "appears to be", "seems", "spots", "discoloration",
    "yellowing", "browning", "wilting", "drooping", "unhealthy"
]

# NEW: Helper function to create mock AILog
def create_mock_ai_log(response_text: str) -> AILog:
    """Create a mock AILog object for responses."""

    class MockAILog:
        def __init__(self, response):
            self.ai_response = response

    return MockAILog(response_text)

# Function to detect photo analysis requests
def is_photo_analysis_request(text: str) -> bool:
    """Detect if user is requesting photo analysis."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in PHOTO_ANALYSIS_KEYWORDS)


# NEW: Function to extract photo ID from text
def extract_photo_id_from_text(text: str) -> int | None:
    """Extract photo ID from user message."""
    # Look for patterns like "photo 123", "image 456", "pic 789"
    import re
    patterns = [
        r'photo\s+(\d+)',
        r'image\s+(\d+)',
        r'picture\s+(\d+)',
        r'pic\s+(\d+)',
        r'#(\d+)'  # hashtag notation
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    return None


def analyze_plant_photo_with_rag(db: Session, user_id: int, user_message: str,
                                 photo_id: int) -> AILog:
    """
    Analyze plant photo using GPT-4 Vision with RAG enhancement.

    Args:
        db: Database session
        user_id: User ID
        user_message: User's message/question about the photo
        photo_id: ID of the photo to analyze

    Returns:
        AILog object with analysis response
    """
    try:
        # Validate photo exists and belongs to user
        is_valid, error_msg, photo = validate_photo_for_chat(db, photo_id, user_id)
        if not is_valid:
            return create_mock_ai_log(f"❌ Photo Error: {error_msg}")

        # Validate image file exists
        is_image_valid, image_error = validate_image_for_analysis(photo.image_path)
        if not is_image_valid:
            return create_mock_ai_log(f"❌ Image Error: {image_error}")

        # Get photo context for analysis
        photo_context = get_photo_context_for_chat(photo, db)

        # Extract plant context if available
        plant_context = photo_context.get('plant')

        # Build RAG context using similar historical cases
        rag_context = build_rag_context_for_diagnosis(
            db=db,
            query_text=f"{user_message} {photo_context.get('upload_context', '')}",
            user_id=user_id,
            plant_context=plant_context,
            user_history=get_user_input_history(db, user_id, limit=10),
            max_similar_cases=5
        )

        # Analyze image with vision AI
        analysis_result = analyze_plant_image_with_gpt4_vision(
            image_path=photo.image_path,
            user_context=f"{user_message} {photo_context.get('upload_context', '')}",
            plant_context=plant_context
        )

        # Generate and store embedding for RAG learning
        try:
            diagnosis_data_for_embedding = {
                'diagnosis_id': None,  # Will be updated after diagnosis creation
                'diagnosis_text': analysis_result['analysis_text'],
                'identified_issues': analysis_result.get('identified_issues'),
                'recommended_actions': analysis_result.get('recommended_actions'),
                'confidence_score': analysis_result.get('confidence_score'),
                'upload_context': photo_context.get('upload_context'),
                'created_at': date.today().isoformat()
            }

            generate_and_store_embedding(
                db, photo_id, user_id, diagnosis_data_for_embedding, plant_context
            )
        except Exception as e:
            print(f"Failed to generate embedding for photo {photo_id}: {str(e)}")

        # generate diagnosis summary
        diagnosis_summary = generate_diagnosis_summary(analysis_result, user_message)

        # Format RAG context for AI enhancement
        rag_context_text = format_rag_context_for_ai(rag_context)

        # Create enhanced response with RAG context
        enhanced_prompt = f"""
        Based on the photo analysis and historical similar cases, provide an enhanced response.

        ORIGINAL DIAGNOSIS:
        {diagnosis_summary}

        HISTORICAL CONTEXT:
        {rag_context_text}

        USER'S QUESTION: {user_message}

        Enhance the diagnosis with insights from similar historical cases. Mention if any patterns 
        from successful treatments apply. Keep the response practical and actionable.
        """

        # Get enhanced response using RAG context
        enhanced_response = ask_gpt4o(
            prompt=enhanced_prompt,
            system_prompt="""You are PlantPal, an expert plant care assistant with access to historical 
            diagnosis data. Use the historical context to enhance your diagnosis with proven patterns 
            and successful treatments. Be specific about which insights come from historical data."""
        )

        # Combine diagnosis summary with enhanced insights
        final_response = f"{diagnosis_summary}\n\n🔍 **Enhanced Analysis with Historical Data:**\n{enhanced_response}"

        return create_mock_ai_log(final_response)

    except Exception as e:
        error_msg = f"❌ **Photo Analysis Failed**\n\nSorry, I encountered an error analyzing your photo: {str(e)}\n\nPlease try uploading the photo again or contact support if the issue persists."
        return create_mock_ai_log(error_msg)


# Function to handle photo-related queries in text
def handle_photo_reference_in_text(db: Session, user_id: int, user_message: str) -> AILog | None:
    """
    Handle when user references a photo in their text message.

    Args:
        db: Database session
        user_id: User ID
        user_message: User's message

    Returns:
        AILog if photo reference founded and processed, None otherwise
    """
    # Extract photo ID from message
    photo_id = extract_photo_id_from_text(user_message)

    if photo_id:
        # User is referencing a specific photo
        return analyze_plant_photo_with_rag(db, user_id, user_message, photo_id)

    # Check if user is asking about recent photos
    if any(phrase in user_message.lower() for phrase in [
        "my photo", "the photo", "recent photo", "uploaded photo", "last photo"
    ]):
        # Get user's most recent photo
        from services.photo_service import get_user_photos_list
        recent_photos = get_user_photos_list(db, user_id, limit=1)

        if recent_photos:
            most_recent_photo = recent_photos[0]
            return analyze_plant_photo_with_rag(db, user_id, user_message, most_recent_photo.id)
        else:
            return create_mock_ai_log(
                "📸 I don't see any photos uploaded yet. Please upload a photo of your plant first, then I can help analyze it!")

    return None


# Add task command detection functions
def is_task_creation_request(text: str) -> bool:
    """Detect if user wants to create a new task."""
    text_lower = text.lower()
    creation_indicators = [
        "create task", "add task", "new task", "set up task", "make task",
        "schedule task", "remind me to", "i need to", "set reminder for",
        "create reminder", "add reminder", "new reminder"
    ]
    return any(indicator in text_lower for indicator in creation_indicators)


def is_task_update_request(text: str) -> bool:
    """Detect if user wants to update an existing task."""
    text_lower = text.lower()
    update_indicators = [
        "update task", "modify task", "change task", "edit task",
        "reschedule", "move task", "change due date", "update schedule",
        "modify reminder", "change reminder"
    ]
    return any(indicator in text_lower for indicator in update_indicators)


def is_task_completion_request(text: str) -> bool:
    """Detect if user wants to mark a task as complete."""
    text_lower = text.lower()
    completion_indicators = [
        "complete task", "mark as done", "finished", "done", "completed",
        "check off", "tick off", "mark complete", "task done", "finished task",
        "completed task", "i did it", "i finished", "i'm done"
    ]
    return any(indicator in text_lower for indicator in completion_indicators)


def extract_task_info_from_text(text: str) -> dict:
    """Extract task information from user text using AI."""
    user_prompt = f"""
    Extract task information from the following text. Return only a JSON object with the following fields if found:
    - task_type: type of task (water, fertilize, prune, repot, check_health, custom)
    - title: task title/name
    - description: task description
    - frequency_days: how often to perform (in days)
    - due_date: specific due date mentioned
    - plant_name: which plant this task is for
    - priority: high/medium/low if mentioned

    Text: "{text}"

    Return only valid JSON or "null" if no task information is found.
    """
    try:
        response = ask_gpt4o(
            user_prompt=user_prompt,
            system_prompt="You are a task information extractor. Extract only task-related information and return it as JSON."
        )
        task_info = json.loads(response.strip())
        if task_info and task_info != "null":
            return task_info
    except Exception as e:
        print(f"Error extracting task info: {str(e)}")
    return {}


def extract_plant_name_from_task_request(text: str, user_plants: list) -> str | None:
    """Extract plant name from task request by matching with user's plants."""
    text_lower = text.lower()
    for plant in user_plants:
        if plant.name.lower() in text_lower:
            return plant.name
    return None


def is_plant_related(text: str) -> bool:
    """Enhanced plant-related detection with more comprehensive keywords matching."""
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
    user_prompt = f"""
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
            user_prompt=user_prompt,
            system_prompt=(f"You are a plant information extractor. Extract only plant-related information "
                           f"and return it as JSON. If no plant information is found, return 'null'."
                           ))
        # Try to parse JSON response
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
    user_prompt = f"""Based on the following user conversation history, create a natural, friendly paragraph that summarizes what the user has been asking about. Make it conversational and engaging, not a bullet point list.

User's previous questions:
{history_text}

Please create a 2-3 sentence paragraph that naturally flows and summarizes their plant care interests and concerns. Include specific topics they've asked about and any patterns in their questions."""
    try:
        summary = ask_gpt4o(
            user_prompt=user_prompt,
            system_prompt=(f"You are PlantPal, a friendly plant care assistant. Create natural, conversational "
                           f"summaries of user's plant care history. Keep it warm and engaging. Focus on their "
                           f"specific plant care interests and any recurring themes in their questions.")
        )
        return summary
    except Exception as e:
        print(f"Error generating history summary: {str(e)}")
        # Fallback to a simple summary
        if len(user_history) >= 3:
            return (f"🌱 Based on our previous conversations, I remember you've been asking about plant care "
                    f"topics including {', '.join(user_history[-3:])}. You seem very interested in taking "
                    f"good care of your plants! 🌿")
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
            # If we were in a list, and now we're not, reset counter
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
        user_prompt = f"""
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
                user_prompt=user_prompt,
                system_prompt="You are analyzing conversation history to find similar past questions. Be concise and accurate."
            )
            return response.strip()
        except Exception as e:
            print(f"Error checking similar questions: {str(e)}")
            return ""

    except Exception as e:
        print(f"Error in check_similar_past_questions: {str(e)}")
        return ""


def get_user_plant_context(db: Session, user_id: int) -> dict:
    """Get comprehensive plant context for the user including all plants, care tasks, and care history."""
    try:

        # Get all user plants
        plants = get_user_plants(db, user_id)

        plant_contexts = []
        for plant in plants:
            # Get care tasks for this plant
            care_tasks = get_user_care_tasks_for_plant(db, plant.id, user_id)

            # Calculate next due dates for tasks
            upcoming_tasks = []
            overdue_tasks = []

            for task in care_tasks:
                if task.due_date:
                    if task.due_date < date.today():
                        overdue_tasks.append({
                            'type': task.task_type,
                            'title': task.title,
                            'due_date': task.due_date.strftime('%Y-%m-%d'),
                            'days_overdue': (date.today() - task.due_date).days
                        })
                    elif task.due_date <= date.today() + timedelta(days=7):
                        upcoming_tasks.append({
                            'type': task.task_type,
                            'title': task.title,
                            'due_date': task.due_date.strftime('%Y-%m-%d'),
                            'days_until_due': (task.due_date - date.today()).days
                        })

            plant_context = {
                'id': plant.id,
                'name': plant.name,
                'species': plant.species,
                'nickname': plant.nickname,
                'location': plant.location,
                'sunlight': plant.sunlight,
                'watering_interval_days': plant.watering_interval_days,
                'fertilizing_interval_days': plant.fertilizing_interval_days,
                'last_watered': plant.last_watered.strftime('%Y-%m-%d') if plant.last_watered else None,
                'last_fertilized': plant.last_fertilized.strftime('%Y-%m-%d') if plant.last_fertilized else None,
                'notes': plant.notes,
                'total_care_tasks': len(care_tasks),
                'active_care_tasks': len([t for t in care_tasks if t.is_active]),
                'upcoming_tasks': upcoming_tasks,
                'overdue_tasks': overdue_tasks
            }
            plant_contexts.append(plant_context)

        return {
            'total_plants': len(plants),
            'plants': plant_contexts,
            'total_overdue_tasks': sum(len(p['overdue_tasks']) for p in plant_contexts),
            'total_upcoming_tasks': sum(len(p['upcoming_tasks']) for p in plant_contexts)
        }

    except Exception as e:
        print(f"Error getting user plant context: {str(e)}")
        return {'total_plants': 0, 'plants': [], 'total_overdue_tasks': 0, 'total_upcoming_tasks': 0}


def extract_task_management_intent(user_message: str) -> dict:
    """Extract task management intent from user message."""
    text_lower = user_message.lower()

    intent = {
        'action': '',
        'plant_name': None,
        'task_type': None,
        'specific_task': None,
        'due_date': None,
        'frequency': None,
        'priority': None
    }

    # Detect action types
    if any(word in text_lower for word in ['create', 'add', 'set up', 'establish', 'make']):
        intent['action'] = 'create'
    elif any(word in text_lower for word in ['update', 'change', 'modify', 'edit']):
        intent['action'] = 'update'
    elif any(word in text_lower for word in ['complete', 'done', 'finished', 'mark as done']):
        intent['action'] = 'complete'
    elif any(word in text_lower for word in ['delete', 'remove', 'cancel']):
        intent['action'] = 'delete'
    elif any(word in text_lower for word in ['show', 'list', 'view', 'see', 'what']):
        intent['action'] = 'view'

    # Detect task types
    task_keywords = {
        'water': ['water', 'watering', 'hydrate'],
        'fertilize': ['fertilize', 'fertilizer', 'feed', 'nutrients'],
        'prune': ['prune', 'trim', 'cut', 'trimming'],
        'repot': ['repot', 'transplant', 'pot', 'container'],
        'check_health': ['check', 'inspect', 'examine', 'health', 'condition'],
        'rotate': ['rotate', 'turn', 'move'],
        'custom': ['custom', 'special', 'specific']
    }

    for task_type, keywords in task_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            intent['task_type'] = task_type
            break

    # Detect frequency
    frequency_patterns = {
        'daily': ['daily', 'every day', 'each day'],
        'weekly': ['weekly', 'every week', 'once a week'],
        'biweekly': ['biweekly', 'every two weeks', 'twice a month'],
        'monthly': ['monthly', 'every month', 'once a month'],
        'custom': ['every', 'times a', 'times per']
    }

    for freq, patterns in frequency_patterns.items():
        if any(pattern in text_lower for pattern in patterns):
            intent['frequency'] = freq
            break

    # Detect priority
    if any(word in text_lower for word in ['urgent', 'important', 'high priority', 'asap']):
        intent['priority'] = 'high'
    elif any(word in text_lower for word in ['medium', 'normal']):
        intent['priority'] = 'medium'
    elif any(word in text_lower for word in ['low', 'when convenient']):
        intent['priority'] = 'low'

    return intent


def generate_intelligent_task_response(user_message: str, plant_context: dict) -> str:
    """Generate intelligent response for task management based on user's plant context."""
    try:
        intent = extract_task_management_intent(user_message)

        # Create context-aware prompt
        user_prompt = f"""
You are PlantPal, an intelligent plant care assistant. The user is asking about task management for their plants.

USER'S PLANT CONTEXT:
{json.dumps(plant_context, indent=2)}

TASK MANAGEMENT INTENT:
{json.dumps(intent, indent=2)}

USER MESSAGE: {user_message}

Based on the user's plant context and their task management intent, provide a helpful, personalized response that:

1. Acknowledges their specific plants and current care situation
2. Addresses their task management needs intelligently
3. Provides specific, actionable advice based on their plant data
4. Mentions any overdue or upcoming tasks that need attention
5. Suggests appropriate care schedules based on their plants' specific needs
6. Uses the plant context to make personalized recommendations
7. Be conversational and engaging, using emojis appropriately

If they have overdue tasks, gently remind them. If they have upcoming tasks, mention them proactively.
If they're asking about creating tasks, suggest appropriate frequencies based on their plants' care requirements.
"""

        response = ask_gpt4o(
            user_prompt=user_prompt,
            system_prompt="You are PlantPal, an expert plant care assistant. Provide intelligent, context-aware responses for task management based on the user's specific plant data and care history."
        )

        return response

    except Exception as e:
        print(f"Error generating intelligent task response: {str(e)}")
        return "I'd be happy to help you with your plant care tasks! Could you tell me more about what you'd like to do?"


def answer_user_question(db: Session, user_id: int, user_message: str, photo_id: int = None) -> AILog:
    """Enhanced AI response function with intelligent plant context and task management."""

    # Handle direct photo analysis request
    if photo_id:
        return analyze_plant_photo_with_rag(db, user_id, user_message, photo_id)

    # Check if user is referencing a photo in their message
    if is_photo_analysis_request(user_message):
        photo_response = handle_photo_reference_in_text(db, user_id, user_message)
        if photo_response:
            return photo_response

    # Check if plant-related
    if not is_plant_related(user_message):
        ai_response = RESTRICTED_TEXT
        return create_mock_ai_log(ai_response)

    # Get comprehensive plant context
    plant_context = get_user_plant_context(db, user_id)

    # Check if this is a task management request
    task_intent = extract_task_management_intent(user_message)
    is_task_management = task_intent['action'] is not None

    complete_history = get_complete_conversation_history(db, user_id)
    past_reference = check_similar_past_questions(db, user_id, user_message)

    # Extract plant information from user message
    plant_info = extract_plant_info_from_text(user_message)

    # Handle plant creation/update logic
    if plant_info and plant_info.get('name'):
        plant_name = plant_info['name']
        existing_plant = find_plant_by_name(db, plant_name, user_id)
        if existing_plant:
            update_data = {}
            for key, value in plant_info.items():
                if key == 'name':
                    continue
                if key == 'watering_interval' and value:
                    update_data['watering_interval_days'] = int(value)
                elif key in ['species', 'nickname', 'location', 'sunlight', 'notes'] and value:
                    update_data[key] = value

            if update_data:
                update_plant(db, existing_plant.id, PlantUpdate(**update_data), user_id)
                plant_id = existing_plant.id
        else:
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

    # Generate intelligent response based on context
    if is_task_management:
        ai_response = generate_intelligent_task_response(user_message, plant_context)
    else:
        # Build enhanced system prompt with plant context
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

        plant_context_summary = ""
        if plant_context['total_plants'] > 0:
            plant_context_summary = f"""
USER'S PLANT CONTEXT:
- Total plants: {plant_context['total_plants']}
- Overdue tasks: {plant_context['total_overdue_tasks']}
- Upcoming tasks: {plant_context['total_upcoming_tasks']}

PLANT DETAILS:
"""
            for plant in plant_context['plants']:
                plant_context_summary += f"""
• {plant['name']} ({plant['species'] or 'Unknown species'})
  - Location: {plant['location']}
  - Sunlight: {plant['sunlight'] or 'Not specified'}
  - Watering: Every {plant['watering_interval_days'] or 'Not set'} days
  - Last watered: {plant['last_watered'] or 'Never'}
  - Active tasks: {plant['active_care_tasks']}
  - Overdue: {len(plant['overdue_tasks'])} tasks
  - Upcoming: {len(plant['upcoming_tasks'])} tasks
"""
        # Add photo analysis capability mention
        system_prompt = f"""You are PlantPal, an expert plant care assistant with complete memory and plant context awareness. 
        
📸 You can now analyze plant photos! Users can upload photos and ask for diagnosis by mentioning photo IDs or saying "analyze my photo".

{history_context}{past_reference_context}{plant_context_summary}

INSTRUCTIONS:
1. Be engaging and conversational. Use emojis occasionally.
2. You have access to ALL past conversations and complete plant context - use this knowledge for personalized responses.
3. If the user has overdue tasks, gently remind them proactively.
4. If they have upcoming tasks, mention them helpfully.
5. Reference their specific plants by name when giving advice.
6. Use their plant care history to provide tailored recommendations.
7. If they mentioned plant issues in past conversations, remember and follow up.
8. Provide specific, actionable advice based on their complete context.
9. Use numbered lists when providing multiple points, but make them sequential (1, 2, 3, 4, 5...).
10. Make the conversation feel continuous and personal - like you remember everything about their plant journey.
11. If users mention plant problems, suggest they can upload a photo for detailed analysis.

Current user message: {user_message}"""

        ai_response = ask_gpt4o(
            user_prompt=user_message,
            system_prompt=system_prompt
        )

    # Fix any numbered lists in the response
    ai_response = fix_numbered_lists(ai_response)
    return create_mock_ai_log(ai_response)

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

        user_prompt = f"""Based on the following complete conversation history between a user and PlantPal (an AI plant care assistant), create a comprehensive but concise summary of what we've discussed.

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
                user_prompt=user_prompt,
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
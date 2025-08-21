# Orchestrates the user input, command parsing, prompt construction, OpenAI call, and logging of AI responses.

from plant_pal_bot.ai_bot_client import ask_gpt4o
from repositories.ai_bot_repo import (
    get_complete_conversation_history, get_user_input_history
)
from repositories.plant_repo import find_plant_by_name, update_plant
from models.ai_bot import AILog
from schemas.plant import PlantUpdate
from sqlalchemy.orm import Session
import re
import json

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
    prompt = f"""Based on the following user conversation history, create a natural, friendly paragraph that summarizes what the user has been asking about. Make it conversational and engaging, not a bullet point list.

User's previous questions:
{history_text}

Please create a 2-3 sentence paragraph that naturally flows and summarizes their plant care interests and concerns. Include specific topics they've asked about and any patterns in their questions."""
    try:
        summary = ask_gpt4o(
            prompt=prompt,
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

def get_user_plant_context(db: Session, user_id: int) -> dict:
    """Get comprehensive plant context for the user including all plants, care tasks, and care history."""
    try:
        from repositories.plant_repo import get_user_plants, get_plant_care_tasks
        from datetime import date, timedelta
        
        # Get all user plants
        plants = get_user_plants(db, user_id)
        
        plant_contexts = []
        for plant in plants:
            # Get care tasks for this plant
            care_tasks = get_plant_care_tasks(db, plant.id, user_id)
            
            # Calculate next due dates for tasks
            upcoming_tasks = []
            overdue_tasks = []
            
            for task in care_tasks:
                if task.next_due_date:
                    if task.next_due_date < date.today():
                        overdue_tasks.append({
                            'type': task.task_type,
                            'title': task.title,
                            'due_date': task.due_date.strftime('%Y-%m-%d'),
                            'days_overdue': (date.today() - task.next_due_date).days
                        })
                    elif task.next_due_date <= date.today() + timedelta(days=7):
                        upcoming_tasks.append({
                            'type': task.task_type,
                            'title': task.title,
                            'due_date': task.next_due_date.strftime('%Y-%m-%d'),
                            'days_until_due': (task.next_due_date - date.today()).days
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





def answer_user_question(db: Session, user_id: int, user_message: str, plant_id: int = None) -> AILog:
    """Enhanced AI response function with intelligent plant context and task management."""
    if not is_plant_related(user_message):
        ai_response = RESTRICTED_TEXT
        class MockAILog:
            def __init__(self, response):
                self.ai_response = response
        return MockAILog(ai_response)

    # Get comprehensive plant context
    plant_context = get_user_plant_context(db, user_id)
    complete_history = get_complete_conversation_history(db, user_id)
    past_reference = check_similar_past_questions(db, user_id, user_message)
    
    # Extract plant information from user message
    plant_info = extract_plant_info_from_text(user_message)
    
    # Handle plant creation/update logic (existing code)
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
        
        system_prompt = f"""You are PlantPal, an expert plant care assistant with complete memory and plant context awareness.

{past_reference_context}{plant_context_summary}

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

Current user message: {user_message}"""

        ai_response = ask_gpt4o(
            prompt=user_message,
            system_prompt=system_prompt
        )
    
    # Fix any numbered lists in the response
    ai_response = fix_numbered_lists(ai_response)
    
    class MockAILog:
        def __init__(self, response):
            self.ai_response = response
    
    return MockAILog(ai_response)

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

def handle_task_creation_request(user_message: str, plant_context: dict) -> str:
    """Handle intelligent task creation based on user's plant context."""
    try:
        
        # Find the specific plant they're referring to
        target_plant = None
        plant_name_mentioned = None
        
        # Extract plant name from message
        for plant in plant_context['plants']:
            if plant['name'].lower() in user_message.lower():
                target_plant = plant
                plant_name_mentioned = plant['name']
                break
        
        if not target_plant:
            if len(plant_context['plants']) == 1:
                target_plant = plant_context['plants'][0]
                plant_name_mentioned = target_plant['name']
            else:
                return "I'd love to help you create care tasks! Which plant would you like to set up tasks for? I can see you have: " + ", ".join([p['name'] for p in plant_context['plants']])
        
        # Generate intelligent task suggestions based on plant type and current care
        task_suggestions = generate_plant_specific_tasks(target_plant)
        
        response = f"🌱 Great! I'll help you set up care tasks for your {plant_name_mentioned}. "
        response += f"Based on your {plant_name_mentioned}'s care needs, here are my recommendations:\n\n"
        
        for i, task in enumerate(task_suggestions, 1):
            response += f"{i}. **{task['title']}** - {task['description']}\n"
            response += f"   Frequency: {task['frequency']}\n"
            if task.get('notes'):
                response += f"   Note: {task['notes']}\n"
            response += "\n"
        
        response += "Would you like me to create these tasks for you? Just say 'yes' or let me know if you'd like to modify any of them!"
        
        return response
        
    except Exception as e:
        print(f"Error handling task creation: {str(e)}")
        return "I'd be happy to help you create care tasks! Could you tell me which plant you'd like to set up tasks for?"

def generate_plant_specific_tasks(plant: dict) -> list:
    """Generate plant-specific task recommendations based on plant data."""
    tasks = []
    
    # Watering task
    watering_freq = plant.get('watering_interval_days', 7)
    tasks.append({
        'title': 'Water Plant',
        'description': f'Water your {plant["name"]} thoroughly',
        'frequency': f'Every {watering_freq} days',
        'task_type': 'water',
        'notes': f'Based on your current {watering_freq}-day watering schedule'
    })
    
    # Fertilizing task
    fertilizing_freq = plant.get('fertilizing_interval_days', 30)
    tasks.append({
        'title': 'Fertilize Plant',
        'description': f'Apply appropriate fertilizer to {plant["name"]}',
        'frequency': f'Every {fertilizing_freq} days',
        'task_type': 'fertilize',
        'notes': f'Based on your current {fertilizing_freq}-day fertilizing schedule'
    })
    
    # Health check task
    tasks.append({
        'title': 'Health Check',
        'description': f'Inspect {plant["name"]} for pests, diseases, or issues',
        'frequency': 'Weekly',
        'task_type': 'check_health',
        'notes': 'Regular health checks help catch problems early'
    })
    
    # Rotation task (for indoor plants)
    if plant.get('location', '').lower() in ['indoor', 'inside', 'home']:
        tasks.append({
            'title': 'Rotate Plant',
            'description': f'Rotate {plant["name"]} for even growth',
            'frequency': 'Every 2 weeks',
            'task_type': 'rotate',
            'notes': 'Helps ensure even sunlight exposure'
        })
    
    # Pruning task (for plants that need it)
    if plant.get('species', '').lower() in ['monstera', 'ficus', 'pothos', 'philodendron']:
        tasks.append({
            'title': 'Prune Plant',
            'description': f'Trim dead or overgrown parts of {plant["name"]}',
            'frequency': 'Monthly',
            'task_type': 'prune',
            'notes': 'Keeps your plant healthy and well-shaped'
        })
    
    return tasks

def handle_task_update_request(user_message: str, plant_context: dict) -> str:
    """Handle intelligent task updates based on user's plant context."""
    try:
        # Find relevant tasks to update
        target_plant = None
        for plant in plant_context['plants']:
            if plant['name'].lower() in user_message.lower():
                target_plant = plant
                break
        
        if not target_plant:
            return "I'd be happy to help you update your care tasks! Which plant's tasks would you like to modify?"
        
        # Analyze what needs updating
        update_suggestions = []
        if target_plant['overdue_tasks']:
            update_suggestions.append(f"Address {len(target_plant['overdue_tasks'])} overdue tasks")
        
        response = f"🌱 I can help you update the care tasks for your {target_plant['name']}! "
        if update_suggestions:
            response += "Here's what I can help you with:\n\n"
            for i, suggestion in enumerate(update_suggestions, 1):
                response += f"{i}. {suggestion}\n"
            response += "\nWhat specific changes would you like to make?"
        else:
            response += "What would you like to update about your care tasks?"
        
        return response
        
    except Exception as e:
        print(f"Error handling task update: {str(e)}")
        return "I'd be happy to help you update your care tasks! What changes would you like to make?"

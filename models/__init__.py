# Import all models
from .user import User
from .plant import Plant, PlantPhoto
from .care_task import PlantCareTask, TaskCompletionHistory
from .ai_bot import AILog, AIResponse, ConversationSession
from sqlalchemy.orm import relationship

# Now that all models are imported, we can set up the relationships
# This prevents circular import issues

# Add the PlantCareTask relationship to User after both classes are defined
User.care_tasks = relationship("PlantCareTask", back_populates="user", cascade="all, delete")

# Make sure all models are available for import
__all__ = [
    'User',
    'Plant',
    'PlantPhoto',
    'PlantCareTask',
    'TaskCompletionHistory',
    'AILog',
    'AIResponse',
    'ConversationSession'
]

from sqlalchemy.orm import Session
from models.care_task import PlantCareTask
from schemas.care_task import PlantCareTaskCreate
from repositories.care_task_repository import create_default_care_tasks
from repositories.plant_repository import get_plant

def create_default_care_tasks_service(db: Session, plant_id: int, user_id: int):
    """Create default care tasks for a plant."""
    plant = get_plant(db, plant_id, user_id)
    if plant:
        return create_default_care_tasks(db, plant_id, plant)
    return []
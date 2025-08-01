from sqlalchemy.orm import Session
from schemas.plant import PlantCreate, PlantUpdate
import repositories.plant_repo as plant_repo

def create_plant_service(db: Session, user_id: int, data: PlantCreate):
    """Create a new plant for the user."""
    return plant_repo.create_plant(db, data, user_id)

def get_plant_service(db: Session, user_id: int, plant_id: int):
    """Retrieve a specific plant for the user."""
    return plant_repo.get_plant(db, plant_id, user_id)

def get_user_plants_service(db: Session, user_id: int):
    """Retrieve all plants for the user."""
    return plant_repo.get_user_plants(db, user_id)

def update_plant_service(db: Session, user_id: int, plant_id: int, data: PlantUpdate):
    """Update a plant's details for the user."""
    return plant_repo.update_plant(db, plant_id, data, user_id)

def delete_plant_service(db: Session, user_id: int, plant_id: int):
    """Delete a plant for the user."""
    return plant_repo.delete_plant(db, plant_id, user_id)
from repositories.plant_repo import (
    create_plant, get_user_plants, get_plant, update_plant, delete_plant
)
from schemas.plant import PlantCreate, PlantUpdate
from sqlalchemy.orm import Session


def create_user_plant(db: Session, plant: PlantCreate, user_id: int):
    """Create a new plant for the specified user."""
    return create_plant(db, plant, user_id)


def get_user_plants_service(db: Session, user_id: int):
    """Get all plants belonging to the specified user."""
    return get_user_plants(db, user_id)


def get_plant_service(db: Session, plant_id: int, user_id: int):
    """Get a specific plant by ID for the specified user."""
    return get_plant(db, plant_id, user_id)


def update_plant_service(db: Session, plant_id: int, plant_update: PlantUpdate, user_id: int):
    """Update a plant's details for the specified user."""
    return update_plant(db, plant_id, plant_update, user_id)


def delete_plant_service(db: Session, plant_id: int, user_id: int):
    """Delete a plant for the specified user."""
    return delete_plant(db, plant_id, user_id)

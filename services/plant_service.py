from repositories.plant_repo import (
    create_plant, get_user_plants, get_plant, update_plant, delete_plant,
    create_care_task, get_plant_care_tasks, update_care_task, delete_care_task,
    create_default_care_tasks
)
from schemas.plant import PlantCreate, PlantUpdate, PlantCareTaskCreate, PlantCareTaskUpdate
from sqlalchemy.orm import Session
from typing import List, Optional


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


def create_care_task_service(db: Session, care_task: PlantCareTaskCreate):
    """Create a new care task for a plant."""
    return create_care_task(db, care_task)


def get_plant_care_tasks_service(db: Session, plant_id: int, user_id: int):
    """Get all care tasks for a specific plant belonging to the user."""
    return get_plant_care_tasks(db, plant_id, user_id)


def update_care_task_service(db: Session, task_id: int, task_update: PlantCareTaskUpdate, user_id: int):
    """Update a care task for the specified user."""
    return update_care_task(db, task_id, task_update, user_id)


def delete_care_task_service(db: Session, task_id: int, user_id: int):
    """Delete a care task for the specified user."""
    return delete_care_task(db, task_id, user_id)


def create_default_care_tasks_service(db: Session, plant_id: int, user_id: int):
    """Create default care tasks for a plant."""
    plant = get_plant(db, plant_id, user_id)
    if plant:
        return create_default_care_tasks(db, plant_id, plant)
    return []
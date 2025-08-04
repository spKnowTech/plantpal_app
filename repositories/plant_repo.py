from sqlalchemy.orm import Session
from models.plant import Plant, PlantCareTask
from schemas.plant import PlantCreate, PlantUpdate, PlantCareTaskCreate, PlantCareTaskUpdate
from datetime import date, datetime, timedelta
from typing import List, Optional


def create_plant(db: Session, plant: PlantCreate, user_id: int) -> Plant:
    """Create a new plant in the database for the specified user."""
    db_plant = Plant(**plant.dict(), user_id=user_id)
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    return db_plant


def get_user_plants(db: Session, user_id: int) -> List[Plant]:
    """Get all plants belonging to the specified user."""
    return db.query(Plant).filter(Plant.user_id == user_id).all()


def get_plant(db: Session, plant_id: int, user_id: int) -> Optional[Plant]:
    """Get a specific plant by ID for the specified user."""
    return db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user_id).first()


def update_plant(db: Session, plant_id: int, plant_update: PlantUpdate, user_id: int) -> Optional[Plant]:
    """Update a plant's details for the specified user."""
    db_plant = get_plant(db, plant_id, user_id)
    if db_plant:
        update_data = plant_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_plant, field, value)
        db.commit()
        db.refresh(db_plant)
    return db_plant


def delete_plant(db: Session, plant_id: int, user_id: int) -> bool:
    """Delete a plant for the specified user."""
    db_plant = get_plant(db, plant_id, user_id)
    if db_plant:
        db.delete(db_plant)
        db.commit()
        return True
    return False


def find_plant_by_name(db: Session, name: str, user_id: int) -> Optional[Plant]:
    """Find a plant by name (case-insensitive)."""
    return db.query(Plant).filter(
        Plant.user_id == user_id,
        Plant.name.ilike(f"%{name}%")
    ).first()


def create_care_task(db: Session, care_task: PlantCareTaskCreate) -> PlantCareTask:
    """Create a new care task in the database."""
    db_care_task = PlantCareTask(**care_task.dict())
    db.add(db_care_task)
    db.commit()
    db.refresh(db_care_task)
    return db_care_task


def get_plant_care_tasks(db: Session, plant_id: int, user_id: int) -> List[PlantCareTask]:
    """Get all care tasks for a specific plant."""
    return db.query(PlantCareTask).join(Plant).filter(
        PlantCareTask.plant_id == plant_id,
        Plant.user_id == user_id
    ).all()


def update_care_task(db: Session, task_id: int, task_update: PlantCareTaskUpdate, user_id: int) -> Optional[PlantCareTask]:
    """Update a care task."""
    db_task = db.query(PlantCareTask).join(Plant).filter(
        PlantCareTask.id == task_id,
        Plant.user_id == user_id
    ).first()
    
    if db_task:
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)
        db.commit()
        db.refresh(db_task)
    return db_task


def delete_care_task(db: Session, task_id: int, user_id: int) -> bool:
    """Delete a care task."""
    db_task = db.query(PlantCareTask).join(Plant).filter(
        PlantCareTask.id == task_id,
        Plant.user_id == user_id
    ).first()
    
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False


def create_default_care_tasks(db: Session, plant_id: int, plant: Plant) -> List[PlantCareTask]:
    """Create default care tasks for a plant based on its species and characteristics."""
    care_tasks = []
    
    # Default watering task
    watering_interval = plant.watering_interval_days or 7  # Default to weekly
    watering_task = PlantCareTask(
        plant_id=plant_id,
        task_type="water",
        title=f"Water {plant.name}",
        description=f"Water your {plant.name} thoroughly. Check soil moisture before watering.",
        frequency_days=watering_interval,
        next_due_date=date.today() + timedelta(days=watering_interval),
        is_active=True
    )
    care_tasks.append(watering_task)
    
    # Default fertilizing task (monthly)
    fertilizing_task = PlantCareTask(
        plant_id=plant_id,
        task_type="fertilize",
        title=f"Fertilize {plant.name}",
        description=f"Apply appropriate fertilizer to your {plant.name}.",
        frequency_days=30,
        next_due_date=date.today() + timedelta(days=30),
        is_active=True
    )
    care_tasks.append(fertilizing_task)
    
    # Health check task (weekly)
    health_task = PlantCareTask(
        plant_id=plant_id,
        task_type="check_health",
        title=f"Check {plant.name}'s health",
        description=f"Inspect {plant.name} for pests, diseases, or any issues.",
        frequency_days=7,
        next_due_date=date.today() + timedelta(days=7),
        is_active=True
    )
    care_tasks.append(health_task)
    
    # Add all tasks to database
    for task in care_tasks:
        db.add(task)
    
    db.commit()
    
    # Refresh all tasks to get their IDs
    for task in care_tasks:
        db.refresh(task)
    
    return care_tasks
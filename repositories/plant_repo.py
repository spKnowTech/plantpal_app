from sqlalchemy.orm import Session
from models.plant import Plant
from schemas.plant import PlantCreate, PlantUpdate
from typing import List, Optional


def create_plant(db: Session, plant: PlantCreate, user_id: int) -> Plant:
    """Create a new plant in the database for the specified user."""
    db_plant = Plant(**plant.model_dump(), user_id=user_id)
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
        update_data = plant_update.model_dump(exclude_unset=True)
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

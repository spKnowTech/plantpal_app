from sqlalchemy.orm import Session
from models.plant import Plant
from schemas.plant import PlantCreate, PlantUpdate

def create_plant(db: Session, plant_data: PlantCreate, user_id: int) -> Plant:
    """Create a new plant for the user."""
    plant = Plant(**plant_data.model_dump(), user_id=user_id)
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant

def get_plant(db: Session, plant_id: int, user_id: int) -> Plant | None:
    """Retrieve a specific plant for the user."""
    return db.query(Plant).filter_by(id=plant_id, user_id=user_id).first()

def get_user_plants(db: Session, user_id: int) -> list[Plant]:
    """Retrieve all plants for a user."""
    return db.query(Plant).filter(Plant.user_id == user_id).all()

def add_plant_for_user(db: Session, user_id: int, name: str, location: str) -> Plant:
    """Add a new plant for a user."""
    plant = Plant(name=name, location=location, user_id=user_id)
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant

def update_plant(db: Session, plant_id: int, plant_data: PlantUpdate, user_id: int) -> Plant | None:
    """Update a plant's details for the user."""
    plant = get_plant(db, plant_id, user_id)
    if plant:
        for key, value in plant_data.model_dump(exclude_unset=True).items():
            setattr(plant, key, value)
        db.commit()
        db.refresh(plant)
    return plant

def delete_plant(db: Session, plant_id: int, user_id: int) -> bool:
    """Delete a plant for the user. Returns True if deleted, False otherwise."""
    plant = get_plant(db, plant_id, user_id)
    if plant:
        db.delete(plant)
        db.commit()
        return True
    return False
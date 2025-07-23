from sqlalchemy.orm import Session
from models.plant import Plant
from schemas.plant import PlantCreate, PlantUpdate


def create_plant(db: Session, plant_data: PlantCreate, user_id: int):
    plant = Plant(**plant_data.model_dump(), user_id=user_id)
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


def get_plant(db: Session, plant_id: int, user_id: int):
    return db.query(Plant).filter_by(id=plant_id, user_id=user_id).first()


def get_user_plants(db: Session, user_id: int):
    return db.query(Plant).filter_by(user_id=user_id).all()


def update_plant(db: Session, plant_id: int, plant_data: PlantUpdate, user_id: int):
    plant = get_plant(db, plant_id, user_id)
    if plant:
        for key, value in plant_data.dict(exclude_unset=True).items():
            setattr(plant, key, value)
        db.commit()
        db.refresh(plant)
    return plant


def delete_plant(db: Session, plant_id: int, user_id: int):
    plant = get_plant(db, plant_id, user_id)
    if plant:
        db.delete(plant)
        db.commit()
    return plant

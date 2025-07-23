from datetime import date
from pydantic import BaseModel
from typing import Optional


class PlantBase(BaseModel):
    name: str
    species: Optional[str]
    nickname: Optional[str]
    location: Optional[str]
    sunlight: Optional[str]
    watering_interval_days: Optional[int]
    fertilizing_interval_days: Optional[int]
    last_watered: Optional[date]
    last_fertilized: Optional[date]
    notes: Optional[str]


class PlantCreate(PlantBase):
    pass


class PlantUpdate(PlantBase):
    pass


class PlantResponse(PlantBase):
    id: int
    user_id: int
    created_at: date

    class Config:
        orm_mode = True

from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional


class PlantBase(BaseModel):
    """Base model for plant data."""
    name: str
    species: Optional[str] = None
    nickname: Optional[str] = None
    location: Optional[str] = None
    sunlight: Optional[str] = None
    watering_interval_days: Optional[int] = None
    fertilizing_interval_days: Optional[int] = None
    last_watered: Optional[date] = None
    last_fertilized: Optional[date] = None
    notes: Optional[str] = None


class PlantCreate(PlantBase):
    """Model for creating a new plant."""
    pass


class PlantUpdate(BaseModel):
    """Model for updating plant details - all fields are optional."""
    name: Optional[str] = None
    species: Optional[str] = None
    nickname: Optional[str] = None
    location: Optional[str] = None
    sunlight: Optional[str] = None
    watering_interval_days: Optional[int] = None
    fertilizing_interval_days: Optional[int] = None
    last_watered: Optional[date] = None
    last_fertilized: Optional[date] = None
    notes: Optional[str] = None


class PlantResponse(PlantBase):
    """Response model for plant data."""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PlantCareTaskBase(BaseModel):
    task_type: str
    title: str
    description: Optional[str] = None
    frequency_days: Optional[int] = None
    next_due_date: Optional[date] = None
    is_active: bool = True


class PlantCareTaskCreate(PlantCareTaskBase):
    plant_id: int


class PlantCareTaskUpdate(BaseModel):
    task_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    frequency_days: Optional[int] = None
    next_due_date: Optional[date] = None
    is_active: Optional[bool] = None


class PlantCareTaskResponse(PlantCareTaskBase):
    id: int
    plant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
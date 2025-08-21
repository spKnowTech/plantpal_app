from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional
from models.care_task import TaskType, RecurrenceType


class PlantCareTaskBase(BaseModel):
    """Base model for plant care task data."""
    task_type: TaskType = Field(..., description="Type of care task")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    recurrence_type: RecurrenceType = Field(None, description="Recurrence type")
    due_date: date = Field(None, description="Due date")
    frequency_days: Optional[int] = Field(None, description="How often to perform task (in days)")
    user_id: int = Field(..., description="ID of the user who owns this task")

class PlantCareTaskCreate(PlantCareTaskBase):
    """Model for creating a new plant care task."""
    plant_id: int = Field(..., description="ID of the plant this task belongs to")


class PlantCareTaskUpdate(PlantCareTaskBase):
    """Model for updating plant care task - all fields are optional."""
    plant_id: int = Field(..., description="ID of the plant this task belongs to")


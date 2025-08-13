from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional, List

class PlantCareTaskBase(BaseModel):
    """Base model for plant care task data."""
    task_type: str = Field(..., description="Type of care task")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    frequency_days: Optional[int] = Field(None, description="How often to perform task (in days)")
    next_due_date: Optional[date] = Field(None, description="Next due date for the task")
    is_active: bool = Field(True, description="Whether the task is active")


class PlantCareTaskCreate(PlantCareTaskBase):
    """Model for creating a new plant care task."""
    plant_id: int = Field(..., description="ID of the plant this task belongs to")


class PlantCareTaskUpdate(BaseModel):
    """Model for updating plant care task - all fields are optional."""
    task_type: Optional[str] = Field(None, description="Type of care task")
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    frequency_days: Optional[int] = Field(None, description="How often to perform task (in days)")
    next_due_date: Optional[date] = Field(None, description="Next due date for the task")
    is_active: Optional[bool] = Field(None, description="Whether the task is active")


class PlantCareTaskResponse(PlantCareTaskBase):
    """Response model for plant care task data."""
    id: int
    plant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# TaskCompletionHistory Schemas
class TaskCompletionHistoryBase(BaseModel):
    """Base model for task completion history data."""
    completed_date: date = Field(..., description="Date when task was completed")


class TaskCompletionHistoryCreate(TaskCompletionHistoryBase):
    """Model for creating a new task completion record."""
    plant_care_task_id: int = Field(..., description="ID of the completed task")
    completed_by_user_id: int = Field(..., description="ID of user who completed the task")


class TaskCompletionHistoryUpdate(BaseModel):
    """Model for updating task completion record - all fields are optional."""
    completed_date: Optional[date] = Field(None, description="Date when task was completed")


class TaskCompletionHistoryResponse(TaskCompletionHistoryBase):
    """Response model for task completion history data."""
    id: int
    plant_care_task_id: int
    completed_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Combined Response Schemas for API endpoints
class PlantCareTaskWithHistoryResponse(PlantCareTaskResponse):
    """Response model for plant care task with completion history."""
    completion_history: List[TaskCompletionHistoryResponse] = []

    class Config:
        from_attributes = True


class TaskCompletionSummary(BaseModel):
    """Summary model for task completion statistics."""
    total_tasks: int
    completed_today: int
    overdue_tasks: int
    upcoming_tasks: int
    completion_rate: float = Field(..., description="Percentage of tasks completed on time")


class DailyTaskSummary(BaseModel):
    """Summary model for daily task overview."""
    date: date
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    is_all_completed: bool = Field(..., description="Whether all tasks for the day are completed")
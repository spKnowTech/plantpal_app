from sqlalchemy.orm import Session
from models.care_task import PlantCareTask
from schemas.care_task import PlantCareTaskCreate, PlantCareTaskUpdate
from repositories.care_task_repo import (
create_care_task, update_care_task, delete_care_task, get_delayed_tasks,
get_upcoming_tasks, get_tasks_by_date, get_tasks_by_type, get_plant_care_tasks,
complete_task, get_task_completion_history, get_completed_tasks_by_date,
get_daily_task_summary, get_plant_task_statistics, update_task_next_due_date
)
from typing import List, Optional, Dict
from datetime import date

# Task CRUD operations
def create_care_task_service(db: Session, care_task: PlantCareTaskCreate, user_id: int) -> Optional[PlantCareTask]:
    """Service layer for creating a new care task."""
    return create_care_task(db, care_task, user_id)

def update_care_task_service(db: Session, task_id: int, task_update: PlantCareTaskUpdate, user_id: int) -> Optional[PlantCareTask]:
    """Service layer for updating a care task."""
    return update_care_task(db, task_id, task_update, user_id)

def delete_care_task_service(db: Session, task_id: int, user_id: int) -> bool:
    """Service layer for deleting a care task."""
    return delete_care_task(db, task_id, user_id)

# Task retrieval services
def get_plant_care_tasks_service(db: Session, plant_id: int, user_id: int) -> List[PlantCareTask]:
    """Service layer for getting all tasks for a specific plant."""
    return get_plant_care_tasks(db, plant_id, user_id)

def get_tasks_by_date_service(db: Session, user_id: int, target_date: date) -> List[PlantCareTask]:
    """Service layer for getting tasks for a specific date."""
    return get_tasks_by_date(db, user_id, target_date)

def get_delayed_tasks_service(db: Session, user_id: int) -> List[PlantCareTask]:
    """Service layer for getting delayed tasks."""
    return get_delayed_tasks(db, user_id)

def get_upcoming_tasks_service(db: Session, user_id: int, days_ahead: int = 7) -> List[PlantCareTask]:
    """Service layer for getting upcoming tasks."""
    return get_upcoming_tasks(db, user_id, days_ahead)

def get_tasks_by_type_service(db: Session, user_id: int, task_type: str) -> List[PlantCareTask]:
    """Service layer for getting tasks by type."""
    return get_tasks_by_type(db, user_id, task_type)

# Task Completion services
def complete_task_service(db: Session, task_id: int, user_id: int) -> Optional[PlantCareTask]:
    """Service layer for completing a task."""
    return complete_task(db, task_id, user_id)

def get_completed_tasks_by_date_service(db: Session, user_id: int, target_date: date) -> List[PlantCareTask]:
    """Service layer for getting completed tasks by date."""
    return get_completed_tasks_by_date(db, user_id, target_date)

def get_task_completion_history_service(db: Session, plant_id: int, user_id: int) -> List[Dict]:
    """Service layer for getting task completion history."""
    return get_task_completion_history(db, plant_id, user_id)

# Task Analytics and Summary Services
def get_daily_task_summary_service(db: Session, user_id: int, target_date: date) -> Dict:
    """Service layer for getting daily task summary."""
    return get_daily_task_summary(db, user_id, target_date)

def get_plant_task_statistics_service(db: Session, plant_id: int, user_id: int) -> Dict:
    """Service layer for getting plant task statistics."""
    return get_plant_task_statistics(db, plant_id, user_id)

# Task Management Services
def update_task_next_due_date_service(db: Session, task_id: int, user_id: int, new_due_date: date) -> Optional[PlantCareTask]:
    """Service layer for updating task due date."""
    return update_task_next_due_date(db, task_id, user_id, new_due_date)

def get_todays_tasks_service(db: Session, user_id: int) -> List[PlantCareTask]:
    """Service layer for getting today's tasks."""
    return get_tasks_by_date(db, user_id, date.today())


def get_user_task_overview_service(db: Session, user_id: int) -> Dict:
    """Service layer for getting user's task overview."""
    today = date.today()

    todays_tasks = get_tasks_by_date(db, user_id, today)
    delayed_tasks = get_delayed_tasks(db, user_id)
    upcoming_tasks = get_upcoming_tasks(db, user_id, 7)
    daily_summary = get_daily_task_summary(db, user_id, today)

    return {
        "todays_tasks": todays_tasks,
        "delayed_tasks": delayed_tasks,
        "upcoming_tasks": upcoming_tasks,
        "daily_summary": daily_summary
    }

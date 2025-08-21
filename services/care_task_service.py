from sqlalchemy.orm import Session
from models.care_task import PlantCareTask
from schemas.care_task import (
    PlantCareTaskCreate, PlantCareTaskUpdate
)
from repositories.care_task_repo import (
    create_care_task, update_care_task, delete_care_task, get_all_tasks_by_date,
    get_all_delayed_tasks, get_all_completed_tasks, get_all_completed_tasks_of_plant,
    get_all_delayed_tasks_for_plant, get_all_completed_tasks_by_date, complete_task
)
from datetime import date, timedelta

# Task CRUD operations with enhanced responses
def create_care_task_service(db: Session,
                             care_task: PlantCareTaskCreate,
                             user_id: int) -> PlantCareTask | None:
    """Service layer for creating a new care task with enhanced response."""
    return create_care_task(db, care_task, user_id)

def update_care_task_service(db: Session,
                             task_id: int,
                             task_update: PlantCareTaskUpdate,
                             user_id: int) -> PlantCareTask | None:
    """Service layer for updating a care task with enhanced response."""
    return update_care_task(db, task_id, task_update, user_id)

def delete_care_task_service(db: Session, task_id: int, user_id: int) -> bool:
    """Service layer for deleting a care task."""
    return delete_care_task(db, task_id, user_id)

# Task Completion Service for Frontend
def complete_task_service(db: Session, task_id: int, user_id: int, is_completed: bool) -> bool:
    """
    Service layer for completing a task from frontend. Creates task completion history if is_completed is True.
    """
    if is_completed:
        return complete_task(db, task_id, user_id)
    return False

def completed_tasks_by_date_service(db: Session, user_id: int, target_date: date) -> list:
    """Service layer for getting all completed tasks by date."""
    return get_all_completed_tasks_by_date(db, user_id, target_date)

# upcoming tasks
def get_all_upcoming_tasks(db: Session, user_id: int) -> list:
    """Service layer for getting all upcoming tasks."""
    todays_tasks = get_all_tasks_by_date(db, user_id, date.today())
    if todays_tasks:
        for task in todays_tasks:
            if task.frequency_days > 0 and task.due_date == date.today():
                task.due_date = task.due_date + timedelta(days=task.frequency_days)
    return todays_tasks

def get_all_upcoming_tasks_for_plant(db: Session, plant_id: int, user_id: int) -> list:
    """Service layer for getting all upcoming tasks."""
    todays_tasks = get_all_delayed_tasks_for_plant(db, plant_id, user_id)
    if todays_tasks:
        for task in todays_tasks:
            if task.frequency_days > 0 and task.due_date == date.today():
                task.due_date = task.due_date + timedelta(days=task.frequency_days)
    return todays_tasks

# Task statistics
def get_tasks_statistics_service(db: Session, user_id: int) -> dict:
    """Service layer for getting all care tasks status."""
    todays_task = get_all_tasks_by_date(db, user_id, date.today())
    upcoming_tasks = get_all_upcoming_tasks(db, user_id)
    delayed_tasks = get_all_delayed_tasks(db, user_id)
    completed_tasks = get_all_completed_tasks(db, user_id)
    return {
        "todays_tasks": todays_task,
        "completed_tasks": completed_tasks,
        "delayed_tasks": delayed_tasks,
        "upcoming_tasks": upcoming_tasks
    }

def get_tasks_statistics_for_plant_service(db: Session, user_id: int, plant_id: int) -> dict:
    """Service layer for getting all care tasks status of a specific plant."""
    todays_task = get_all_delayed_tasks_for_plant(db, plant_id, user_id)
    upcoming_tasks = get_all_upcoming_tasks_for_plant(db, plant_id, user_id)
    delayed_tasks = get_all_delayed_tasks_for_plant(db, plant_id, user_id)
    completed_tasks = get_all_completed_tasks_of_plant(db, plant_id, user_id)
    return {
        "todays_task": todays_task,
        "completed_tasks": completed_tasks,
        "delayed_tasks": delayed_tasks,
        "upcoming_tasks": upcoming_tasks
    }
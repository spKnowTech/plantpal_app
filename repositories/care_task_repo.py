from sqlalchemy.orm import Session
from datetime import date, timedelta
from models.care_task import PlantCareTask
from schemas.care_task import PlantCareTaskCreate, PlantCareTaskUpdate
from models.care_task import TaskCompletionHistory
from models.plant import Plant
from typing import List, Optional, Dict


def create_care_task(db: Session, care_task: PlantCareTaskCreate, user_id: int) -> Optional[PlantCareTask]:
    """Create a new care task in the database with user ownership validation."""
    # Verify plant ownership
    plant = db.query(Plant).filter(Plant.id == care_task.plant_id, Plant.user_id == user_id).first()
    if not plant:
        return None

    db_care_task = PlantCareTask(**care_task.dict())
    db.add(db_care_task)
    db.commit()
    db.refresh(db_care_task)
    return db_care_task


def update_care_task(db: Session, task_id: int, task_update: PlantCareTaskUpdate, user_id: int) -> Optional[
    PlantCareTask]:
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


def get_plant_care_tasks(db: Session, plant_id: int, user_id: int) -> List[PlantCareTask]:
    """Get all care tasks for a specific plant with user ownership validation."""
    return db.query(PlantCareTask).join(Plant).filter(
        PlantCareTask.plant_id == plant_id,
        Plant.user_id == user_id
    ).order_by(PlantCareTask.next_due_date).all()


def get_tasks_by_date(db: Session, user_id: int, target_date: date) -> List[PlantCareTask]:
    """Get all tasks for a specific date for a user across all their plants."""
    return db.query(PlantCareTask).join(Plant).filter(
        Plant.user_id == user_id,
        PlantCareTask.next_due_date == target_date,
        PlantCareTask.is_active == True
    ).all()


def get_delayed_tasks(db: Session, user_id: int) -> List[PlantCareTask]:
    """Get all delayed tasks for a user."""
    return db.query(PlantCareTask).join(Plant).filter(
        Plant.user_id == user_id,
        PlantCareTask.next_due_date < date.today(),
        PlantCareTask.is_active == True
    ).all()


def get_upcoming_tasks(db: Session, user_id: int, days_ahead: int = 7) -> List[PlantCareTask]:
    """Get upcoming tasks for the next N days."""
    future_date = date.today() + timedelta(days=days_ahead)
    return db.query(PlantCareTask).join(Plant).filter(
        Plant.user_id == user_id,
        PlantCareTask.next_due_date >= date.today(),
        PlantCareTask.next_due_date <= future_date,
        PlantCareTask.is_active == True
    ).order_by(PlantCareTask.next_due_date).all()


def complete_task(db: Session, task_id: int, user_id: int) -> None:
    """Mark a task as completed and create completion history record."""
    # Get the task and verify ownership
    db_task = db.query(PlantCareTask).join(Plant).filter(
        PlantCareTask.id == task_id,
        Plant.user_id == user_id
    ).first()

    if not db_task:
        return None

    # Create completion history record
    completion_record = TaskCompletionHistory(
        plant_care_task_id=task_id,
        completed_by_user_id=user_id,
        completed_date=date.today()
    )
    db.add(completion_record)

    # Update next due date if task is recurring
    if db_task.frequency_days:
        db_task.next_due_date = date.today() + timedelta(days=db_task.frequency_days)


    db.commit()
    db.refresh(db_task)
    return None


def get_task_completion_history(db: Session, plant_id: int, user_id: int) -> List[Dict]:
    """Get completion history for all tasks of a specific plant."""
    from models.care_task import TaskCompletionHistory

    return db.query(
        PlantCareTask,
        TaskCompletionHistory.completed_date,
        TaskCompletionHistory.created_at
    ).join(Plant).outerjoin(TaskCompletionHistory).filter(
        PlantCareTask.plant_id == plant_id,
        Plant.user_id == user_id
    ).order_by(TaskCompletionHistory.completed_date.desc()).all()


def get_completed_tasks_by_date(db: Session, user_id: int, target_date: date) -> List[PlantCareTask]:
    """Get all tasks completed on a specific date."""
    from models.care_task import TaskCompletionHistory

    return db.query(PlantCareTask).join(Plant).join(TaskCompletionHistory).filter(
        Plant.user_id == user_id,
        TaskCompletionHistory.completed_date == target_date
    ).all()


def get_daily_task_summary(db: Session, user_id: int, target_date: date) -> Dict:
    """Get summary of tasks for a specific date."""
    total_tasks = db.query(PlantCareTask).join(Plant).filter(
        Plant.user_id == user_id,
        PlantCareTask.next_due_date == target_date,
        PlantCareTask.is_active == True
    ).count()

    from models.care_task import TaskCompletionHistory
    completed_tasks = db.query(PlantCareTask).join(Plant).join(TaskCompletionHistory).filter(
        Plant.user_id == user_id,
        TaskCompletionHistory.completed_date == target_date
    ).count()

    return {
        "date": target_date,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": total_tasks - completed_tasks,
        "is_all_completed": total_tasks > 0 and total_tasks == completed_tasks
    }


def get_plant_task_statistics(db: Session, plant_id: int, user_id: int) -> Dict:
    """Get task statistics for a specific plant."""
    from models.care_task import TaskCompletionHistory

    # Verify plant ownership
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user_id).first()
    if not plant:
        return {}

    total_tasks = db.query(PlantCareTask).filter(PlantCareTask.plant_id == plant_id).count()

    completed_tasks = db.query(PlantCareTask).join(TaskCompletionHistory).filter(
        PlantCareTask.plant_id == plant_id
    ).count()

    overdue_tasks = db.query(PlantCareTask).filter(
        PlantCareTask.plant_id == plant_id,
        PlantCareTask.next_due_date < date.today(),
        PlantCareTask.is_active == True
    ).count()

    upcoming_tasks = db.query(PlantCareTask).filter(
        PlantCareTask.plant_id == plant_id,
        PlantCareTask.next_due_date >= date.today(),
        PlantCareTask.is_active == True
    ).count()

    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "upcoming_tasks": upcoming_tasks,
        "completion_rate": round(completion_rate, 2)
    }


def update_task_next_due_date(db: Session, task_id: int, user_id: int, new_due_date: date) -> Optional[PlantCareTask]:
    """Update the next due date for a task."""
    db_task = db.query(PlantCareTask).join(Plant).filter(
        PlantCareTask.id == task_id,
        Plant.user_id == user_id
    ).first()

    if db_task:
        db_task.next_due_date = new_due_date
        db.commit()
        db.refresh(db_task)

    return db_task


def get_tasks_by_type(db: Session, user_id: int, task_type: str) -> List[PlantCareTask]:
    """Get all tasks of a specific type for a user."""
    return db.query(PlantCareTask).join(Plant).filter(
        Plant.user_id == user_id,
        PlantCareTask.task_type == task_type,
        PlantCareTask.is_active == True
    ).all()
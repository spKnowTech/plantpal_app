from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Enum as SQLEnum, TIMESTAMP, text, Boolean
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import date

class RecurrenceType(enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    WEEKEND = "weekend"
    CUSTOM = "custom"

class TaskType(enum.Enum):
    """Enum for task types to ensure validation."""
    NONE = "none"
    WATER = "water"
    FERTILIZE = "fertilize"
    PRUNE = "prune"
    ROTATE = "rotate"
    REPOT = "repot"
    CHECK_HEALTH = "check_health"
    OTHER = "other"

class PlantCareTask(Base):
    """Scheduled care tasks for plants."""
    __tablename__ = 'plant_care_tasks'

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))  # owner
    task_type = Column(SQLEnum(TaskType), nullable=False, default=TaskType.NONE)
    title = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    recurrence_type = Column(SQLEnum(RecurrenceType), nullable=False, default=RecurrenceType.NONE)
    frequency_days = Column(Integer, nullable=False, default=0)
    due_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)  # Whether the task is still active
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))
    updated_at = Column(Date, nullable=True)
    # Relationships
    plant = relationship("Plant", back_populates="care_tasks")
    user = relationship("User", back_populates="care_tasks")  # who owns this task
    completion_history = relationship("TaskCompletionHistory", back_populates="tasks", cascade="all, delete")


class TaskCompletionHistory(Base):
    """Historical record of completed tasks."""
    __tablename__ = 'task_completion_history'
    id = Column(Integer, primary_key=True)
    plant_care_task_id = Column(Integer, ForeignKey('plant_care_tasks.id', ondelete='CASCADE'))
    completed_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))
    # Relationships
    tasks = relationship("PlantCareTask", back_populates="completion_history")
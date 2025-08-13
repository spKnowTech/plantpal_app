from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, CheckConstraint, TIMESTAMP, text, Boolean
from sqlalchemy.orm import relationship
from database import Base


class PlantCareTask(Base):
    """Scheduled care tasks for plants."""
    __tablename__ = 'plant_care_tasks'

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'))
    task_type = Column(String(50), CheckConstraint(
        "task_type IN ('water', 'fertilize', 'prune', 'rotate', 'repot', 'check_health')"))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    frequency_days = Column(Integer, nullable=True)  # How often to perform the task
    next_due_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)  # Whether the task is still active
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'), onupdate=text('now()'))
    completed_by_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))

    plant = relationship("Plant", back_populates="care_tasks")
    completion_history = relationship("TaskCompletionHistory", back_populates="task", cascade="all, delete")


class TaskCompletionHistory(Base):
    """Historical record of completed tasks."""
    __tablename__ = 'task_completion_history'
    id = Column(Integer, primary_key=True)
    plant_care_task_id = Column(Integer, ForeignKey('plant_care_tasks.id', ondelete='CASCADE'))
    completed_by_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    completed_date = Column(Date, nullable=False) # When the task was completed
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))
    # Relationships
    task = relationship("PlantCareTask", back_populates="completion_history")
    user = relationship("User", back_populates="task_completions")
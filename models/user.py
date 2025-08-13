from sqlalchemy import Column, Integer, String, TIMESTAMP, text
from database import Base
from sqlalchemy.orm import relationship


class User(Base):
    """Represents an application user."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    location = Column(String(200), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))

    plant = relationship("Plant", back_populates="user", cascade="all, delete")
    ai_logs = relationship("AILog", back_populates="user", cascade="all, delete")
    ai_responses = relationship("AIResponse", back_populates="user", cascade="all, delete")
    conversation_sessions = relationship("ConversationSession", back_populates="user", cascade="all, delete")
    task_completions = relationship("TaskCompletionHistory", back_populates="user", cascade="all, delete")
from sqlalchemy import Column, Integer, String, Text, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from database import Base


class AILog(Base):
    """
    Stores logs of AI interactions, including user input and context.
    """
    __tablename__ = 'ai_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='SET NULL'), nullable=True)
    input_text = Column(Text, nullable=False)
    type = Column(String(50), CheckConstraint("type IN ('chat', 'diagnosis')"))
    session_id = Column(String(100), nullable=True)  # To identify different sessions
    is_permanent = Column(Boolean, default=True)  # Whether to keep this conversation permanently
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))

    user = relationship("User", back_populates="ai_logs")
    plant = relationship("Plant", back_populates="ai_logs")
    ai_responses = relationship("AIResponse", back_populates="ai_log", cascade="all, delete")


class AIResponse(Base):
    """
    Stores AI responses permanently for conversation history.
    """
    __tablename__ = 'ai_responses'

    id = Column(Integer, primary_key=True)
    ai_log_id = Column(Integer, ForeignKey('ai_logs.id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    response_text = Column(Text, nullable=False)
    is_permanent = Column(Boolean, default=True)  # Whether to keep this response permanently
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))

    ai_log = relationship("AILog", back_populates="ai_responses")
    user = relationship("User", back_populates="ai_responses")


class ConversationSession(Base):
    """
    Tracks conversation sessions for users.
    """
    __tablename__ = 'conversation_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    session_id = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))
    ended_at = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="conversation_sessions")


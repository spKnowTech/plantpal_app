from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, CheckConstraint, TIMESTAMP, text
from sqlalchemy.orm import relationship
from database import Base


class Plant(Base):
    """Represents a user's plant and its care details."""
    __tablename__ = 'plants'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    name = Column(String(100), nullable=False, unique=True)
    species = Column(String(100), nullable=True)
    location = Column(String(100), nullable=False)
    sunlight = Column(String(50), nullable=True)
    watering_interval_days = Column(Integer, nullable=True)
    fertilizing_interval_days = Column(Integer, nullable=True)
    last_watered = Column(Date, nullable=True)
    last_fertilized = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))
    # Relationships
    user = relationship("User", back_populates="plant")
    photos = relationship("PlantPhoto", back_populates="plant", cascade="all, delete")
    ai_logs = relationship("AILog", back_populates="plant", cascade="all, delete")
    care_tasks = relationship("PlantCareTask", back_populates="plant", cascade="all, delete")




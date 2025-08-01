from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, CheckConstraint, TIMESTAMP, text
from sqlalchemy.orm import relationship
from database import Base


class Plant(Base):
    """Represents a user's plant and its care details."""
    __tablename__ = 'plants'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    name = Column(String(100), nullable=False)
    species = Column(String(100), nullable=True)
    nickname = Column(String(100), nullable=True)
    location = Column(String(100), nullable=False)
    sunlight = Column(String(50), nullable=True)
    watering_interval_days = Column(Integer, nullable=True)
    fertilizing_interval_days = Column(Integer, nullable=True)
    last_watered = Column(Date, nullable=True)
    last_fertilized = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))

    user = relationship("User", back_populates="plant")
    photos = relationship("PlantPhoto", back_populates="plant", cascade="all, delete")
    care_logs = relationship("CareLog", back_populates="plant", cascade="all, delete")
    ai_logs = relationship("AILog", back_populates="plant", cascade="all, delete")


class PlantPhoto(Base):
    """Stores photos of plants for diagnosis and history."""
    __tablename__ = 'plant_photos'

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'))
    image_path = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=True)
    uploaded_at = Column(TIMESTAMP(timezone=True), nullable=False,
                         server_default=text('now()'))

    plant = relationship("Plant", back_populates="photos")


class CareLog(Base):
    """Logs care activities performed on a plant."""
    __tablename__ = 'care_logs'

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'))
    task_type = Column(String(50), CheckConstraint("task_type IN ('water', 'fertilize', 'prune', 'rotate')"))
    performed_on = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)

    plant = relationship("Plant", back_populates="care_logs")
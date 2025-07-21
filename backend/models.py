from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from backend.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    location = Column(String(200), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))

    plants = relationship("Plant", back_populates="user", cascade="all, delete")
    ai_logs = relationship("AILog", back_populates="user", cascade="all, delete")


class Plant(Base):
    __tablename__ = 'plants'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    name = Column(String(100), nullable=False)
    species = Column(String(100))
    nickname = Column(String(100))
    location = Column(String(100))
    sunlight = Column(String(50))
    watering_interval_days = Column(Integer)
    fertilizing_interval_days = Column(Integer)
    last_watered = Column(Date)
    last_fertilized = Column(Date)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))

    user = relationship("User", back_populates="plants")
    reminders = relationship("Reminder", back_populates="plant", cascade="all, delete")
    photos = relationship("PlantPhoto", back_populates="plant", cascade="all, delete")
    logs = relationship("CareLog", back_populates="plant", cascade="all, delete")
    ai_logs = relationship("AILog", back_populates="plant")


class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'))
    type = Column(String(50), nullable=False)
    next_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    repeat_interval_days = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))

    plant = relationship("Plant", back_populates="reminders")


class AILog(Base):
    __tablename__ = 'ai_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='SET NULL'), nullable=True)
    input_text = Column(Text, nullable=False)
    ai_response = Column(Text)
    type = Column(String(50), CheckConstraint("type IN ('chat', 'diagnosis')"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))

    user = relationship("User", back_populates="ai_logs")
    plant = relationship("Plant", back_populates="ai_logs")


class PlantPhoto(Base):
    __tablename__ = 'plant_photos'

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'))
    image_path = Column(Text, nullable=False)
    diagnosis = Column(Text)
    uploaded_at = Column(TIMESTAMP(timezone=True), nullable=False,
                         server_default=text('now()'))

    plant = relationship("Plant", back_populates="photos")


class CareLog(Base):
    __tablename__ = 'care_logs'

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'))
    task_type = Column(String(50), CheckConstraint("task_type IN ('water', 'fertilize', 'prune', 'rotate')"))
    performed_on = Column(Date, nullable=False)
    notes = Column(Text)

    plant = relationship("Plant", back_populates="logs")

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from database import Base


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
    photos = relationship("PlantPhoto", back_populates="plant", cascade="all, delete")
    logs = relationship("CareLog", back_populates="plant", cascade="all, delete")
    ai_logs = relationship("AILog", back_populates="plant")


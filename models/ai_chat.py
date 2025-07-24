from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from database import Base


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


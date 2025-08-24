from sqlalchemy import Column, Integer, String, Text, ForeignKey, CheckConstraint, TIMESTAMP, text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
from pgvector.sqlalchemy import Vector

class PlantPhoto(Base):
    """Enhanced plant photo model with diagnosis support."""
    __tablename__ = 'plant_photos'

    id = Column(Integer, primary_key=True, nullable=False)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    image_path = Column(Text, nullable=False, unique=True)
    original_filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    diagnosis_status = Column(String(50), nullable=False, default='pending')
    upload_context = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    plant = relationship("Plant", back_populates="photos")
    user = relationship("User")
    diagnoses = relationship("PhotoDiagnosis", back_populates="photo", cascade="all, delete")
    embeddings = relationship("PhotoEmbedding", back_populates="photo", cascade="all, delete")


class PhotoDiagnosis(Base):
    """Store AI diagnosis results for plant photos."""
    __tablename__ = 'photo_diagnoses'

    id = Column(Integer, primary_key=True, nullable=False)
    photo_id = Column(Integer, ForeignKey('plant_photos.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    diagnosis_text = Column(Text, nullable=False)
    confidence_score = Column(Float, CheckConstraint('confidence_score >= 0 AND confidence_score <= 1'))
    identified_issues = Column(JSONB, nullable=True)
    recommended_actions = Column(JSONB, nullable=True)
    similar_cases_used = Column(JSONB, nullable=True)
    treatment_outcome = Column(String(50), nullable=True)
    user_feedback_rating = Column(Integer, CheckConstraint('user_feedback_rating >= 1 AND user_feedback_rating <= 5'))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    photo = relationship("PlantPhoto", back_populates="diagnoses")
    user = relationship("User")
    feedback = relationship("DiagnosisFeedback", back_populates="diagnosis", cascade="all, delete")


class PhotoEmbedding(Base):
    """Store vector embeddings for RAG functionality."""
    __tablename__ = 'photo_embeddings'

    id = Column(Integer, primary_key=True, nullable=False)
    photo_id = Column(Integer, ForeignKey('plant_photos.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # Note: VECTOR type needs pgvector extension
    embedding_vector = Column(Vector(1536), nullable=True)  # Uncomment when pgvector is available
    embedding_model = Column(String(100), nullable=False, default='text-embedding-ada-002')
    metadata_info = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    photo = relationship("PlantPhoto", back_populates="embeddings")
    user = relationship("User")


class DiagnosisFeedback(Base):
    """Store user feedback on diagnosis accuracy for continuous learning."""
    __tablename__ = 'diagnosis_feedback'

    id = Column(Integer, primary_key=True, nullable=False)
    diagnosis_id = Column(Integer, ForeignKey('photo_diagnoses.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    feedback_type = Column(String(50), nullable=False)
    feedback_text = Column(Text, nullable=True)
    improvement_suggestion = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    diagnosis = relationship("PhotoDiagnosis", back_populates="feedback")
    user = relationship("User")
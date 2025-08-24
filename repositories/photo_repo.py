from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import Optional, List, Dict, Any
from models.photo import PlantPhoto, PhotoDiagnosis, PhotoEmbedding, DiagnosisFeedback
from schemas.photo import (
    PhotoCreate, DiagnosisCreate, DiagnosisUpdate, EmbeddingCreate,
    FeedbackCreate, DiagnosisStatus, TreatmentOutcome
)
from datetime import datetime, timedelta, timezone


def create_photo(db: Session, photo_data: PhotoCreate) -> PlantPhoto:
    """Create a new photo record in database."""
    db_photo = PlantPhoto(**photo_data.model_dump())
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo


def get_photo_by_id(db: Session, photo_id: int, user_id: int) -> Optional[PlantPhoto]:
    """Get photo by ID for specific user."""
    return db.query(PlantPhoto).filter(
        and_(PlantPhoto.id == photo_id, PlantPhoto.user_id == user_id)
    ).first()


def get_user_photos(db: Session, user_id: int, limit: int = 50, offset: int = 0) -> List[PlantPhoto]:
    """Get all photos for a user with pagination."""
    return db.query(PlantPhoto).filter(
        PlantPhoto.user_id == user_id
    ).order_by(desc(PlantPhoto.created_at)).limit(limit).offset(offset).all()


def get_plant_photos(db: Session, plant_id: int, user_id: int) -> List[PlantPhoto()]:
    """Get all photos for a specific plant."""
    return db.query(PlantPhoto).filter(
        and_(PlantPhoto.plant_id == plant_id, PlantPhoto.user_id == user_id)
    ).order_by(desc(PlantPhoto.created_at)).all()


def update_photo_status(db: Session, photo_id: int, status: DiagnosisStatus, user_id: int) -> Optional[PlantPhoto]:
    """Update photo diagnosis status."""
    photo = get_photo_by_id(db, photo_id, user_id)
    if photo:
        photo.diagnosis_status = status
        photo.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(photo)
    return photo


def delete_photo(db: Session, photo_id: int, user_id: int) -> bool:
    """Delete a photo and all related data."""
    photo = get_photo_by_id(db, photo_id, user_id)
    if photo:
        db.delete(photo)
        db.commit()
        return True
    return False


# Diagnosis Repository Functions
def create_diagnosis(db: Session, diagnosis_data: DiagnosisCreate) -> PhotoDiagnosis:
    """Create a new diagnosis record."""
    db_diagnosis = PhotoDiagnosis(**diagnosis_data.model_dump())
    db.add(db_diagnosis)
    db.commit()
    db.refresh(db_diagnosis)
    return db_diagnosis


def get_diagnosis_by_photo_id(db: Session, photo_id: int, user_id: int) -> Optional[PhotoDiagnosis]:
    """Get the latest diagnosis for a photo."""
    return db.query(PhotoDiagnosis).filter(
        and_(PhotoDiagnosis.photo_id == photo_id, PhotoDiagnosis.user_id == user_id)
    ).order_by(desc(PhotoDiagnosis.created_at)).first()


def get_all_diagnoses_for_photo(db: Session, photo_id: int, user_id: int) -> List[PhotoDiagnosis()]:
    """Get all diagnoses for a photo (in case of re-analysis)."""
    return db.query(PhotoDiagnosis).filter(
        and_(PhotoDiagnosis.photo_id == photo_id, PhotoDiagnosis.user_id == user_id)
    ).order_by(desc(PhotoDiagnosis.created_at)).all()


def update_diagnosis(db: Session, diagnosis_id: int, update_data: DiagnosisUpdate, user_id: int) -> Optional[
    PhotoDiagnosis]:
    """Update an existing diagnosis."""
    diagnosis = db.query(PhotoDiagnosis).filter(
        and_(PhotoDiagnosis.id == diagnosis_id, PhotoDiagnosis.user_id == user_id)
    ).first()

    if diagnosis:
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(diagnosis, field, value)
        diagnosis.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(diagnosis)
    return diagnosis


def get_user_diagnoses_history(db: Session, user_id: int, limit: int = 100) -> List[PhotoDiagnosis]:
    """Get user's diagnosis history for RAG context."""
    return db.query(PhotoDiagnosis).filter(
        PhotoDiagnosis.user_id == user_id
    ).order_by(desc(PhotoDiagnosis.created_at)).limit(limit).all()


def get_successful_diagnoses_for_rag(db: Session, plant_species: Optional[str] = None, limit: int = 50) -> List[
    PhotoDiagnosis]:
    """Get successful diagnoses to use as RAG context."""
    query = db.query(PhotoDiagnosis).filter(PhotoDiagnosis.treatment_outcome == TreatmentOutcome.SUCCESSFUL)

    # If plant species is provided, try to filter by it
    if plant_species:
        # Join with photos and plants to filter by species
        from models.plant import Plant
        query = query.join(PlantPhoto).join(Plant).filter(
            Plant.species.ilike(f"%{plant_species}%")
        )

    return query.order_by(desc(PhotoDiagnosis.confidence_score)).limit(limit).all()


# Embedding Repository Functions
def create_embedding(db: Session, embedding_data: EmbeddingCreate) -> PhotoEmbedding:
    """Create a new embedding record."""
    db_embedding = PhotoEmbedding(**embedding_data.model_dump())
    db.add(db_embedding)
    db.commit()
    db.refresh(db_embedding)
    return db_embedding


def get_embedding_by_photo_id(db: Session, photo_id: int) -> Optional[PhotoEmbedding]:
    """Get embedding for a photo."""
    return db.query(PhotoEmbedding).filter(
        PhotoEmbedding.photo_id == photo_id
    ).first()


def find_similar_embeddings(db: Session, target_embedding: List[float], limit: int = 10,
                            exclude_user_id: Optional[int] = None,
                            similarity_threshold: float = 0.7) -> List[PhotoEmbedding]:
    """Find similar embeddings using cosine similarity with pgvector.

    Args:
        db: Database session
        target_embedding: The embedding vector to find similarities for
        limit: Maximum number of results to return
        exclude_user_id: Optional user ID to exclude from results
        similarity_threshold: Minimum similarity score (0-1) to include in results

    Returns:
        List of PhotoEmbedding objects ordered by similarity (most similar first)
    """
    # Convert list to pgvector format
    target_vector = str(target_embedding)

    # Base query with cosine similarity calculation
    query = db.query(
        PhotoEmbedding,
        # Calculate cosine similarity (1 - cosine distance)
        (1 - PhotoEmbedding.embedding_vector.cosine_distance(target_vector)).label('similarity')
    ).filter(
        # Only include embeddings that actually have vector data
        PhotoEmbedding.embedding_vector.isnot(None)
    )

    # Exclude specific user if requested
    if exclude_user_id:
        query = query.filter(PhotoEmbedding.user_id != exclude_user_id)

    # Filter by similarity threshold
    if similarity_threshold > 0:
        query = query.having(
            (1 - PhotoEmbedding.embedding_vector.cosine_distance(target_vector)) >= similarity_threshold
        )

    # Order by similarity (highest first) and limit results
    results = query.order_by(
        desc((1 - PhotoEmbedding.embedding_vector.cosine_distance(target_vector)))
    ).limit(limit).all()

    # Return just the PhotoEmbedding objects (without similarity scores)
    return [result[0] for result in results]


def get_embeddings_by_metadata(db: Session, metadata_filter: Dict[str, Any], limit: int = 20) -> List[PhotoEmbedding]:
    """Get embeddings by metadata criteria."""
    # Simple metadata filtering - in production you might want more sophisticated filtering
    embeddings = db.query(PhotoEmbedding).filter(
        PhotoEmbedding.metadata_info.is_not(None)
    ).limit(limit * 2).all()  # Get more to filter

    # Filter by metadata in Python (could be optimized with JSONB queries)
    filtered_embeddings = []
    for embedding in embeddings:
        if embedding.metadata_info:
            match = True
            for key, value in metadata_filter.items():
                if key not in embedding.metadata_info or embedding.metadata_info[key] != value:
                    match = False
                    break
            if match:
                filtered_embeddings.append(embedding)
                if len(filtered_embeddings) >= limit:
                    break

    return filtered_embeddings


# Feedback Repository Functions
def create_feedback(db: Session, feedback_data: FeedbackCreate) -> DiagnosisFeedback:
    """Create diagnosis feedback."""
    db_feedback = DiagnosisFeedback(**feedback_data.model_dump())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def get_feedback_for_diagnosis(db: Session, diagnosis_id: int, user_id: int) -> List[DiagnosisFeedback()]:
    """Get all feedback for a diagnosis."""
    return db.query(DiagnosisFeedback).filter(
        and_(DiagnosisFeedback.diagnosis_id == diagnosis_id, DiagnosisFeedback.user_id == user_id)
    ).order_by(desc(DiagnosisFeedback.created_at)).all()


# Analytics and Statistics Functions
def get_diagnosis_accuracy_stats(db: Session, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
    """Get diagnosis accuracy statistics."""
    since_date = datetime.now(timezone.utc) - timedelta(days=days)

    query = db.query(PhotoDiagnosis).filter(
        PhotoDiagnosis.created_at >= since_date
    )

    if user_id:
        query = query.filter(PhotoDiagnosis.user_id == user_id)

    total_diagnoses = query.count()
    successful_diagnoses = query.filter(
        PhotoDiagnosis.treatment_outcome == TreatmentOutcome.SUCCESSFUL
    ).count()

    avg_confidence = query.with_entities(
        func.avg(PhotoDiagnosis.confidence_score)
    ).scalar() or 0.0

    return {
        "total_diagnoses": total_diagnoses,
        "successful_diagnoses": successful_diagnoses,
        "success_rate": successful_diagnoses / total_diagnoses if total_diagnoses > 0 else 0.0,
        "average_confidence": float(avg_confidence),
        "period_days": days
    }


def get_common_issues(db: Session, user_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Get most common plant issues from diagnoses."""
    query = db.query(PhotoDiagnosis)

    if user_id:
        query = query.filter(PhotoDiagnosis.user_id == user_id)

    diagnoses = query.filter(
        PhotoDiagnosis.identified_issues.is_not(None)
    ).all()

    # Count issues
    issue_counts = {}
    for diagnosis in diagnoses:
        if diagnosis.identified_issues:
            for category, issues in diagnosis.identified_issues.items():
                for issue in issues:
                    key = f"{category}: {issue}"
                    issue_counts[key] = issue_counts.get(key, 0) + 1

    # Sort by frequency and return top issues
    sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    return [
        {"issue": issue, "count": count, "percentage": (count / len(diagnoses)) * 100}
        for issue, count in sorted_issues
    ]


def get_photos_needing_diagnosis(db: Session, user_id: Optional[int] = None) -> List[PlantPhoto()]:
    """Get photos that need diagnosis (pending or failed)."""
    query = db.query(PlantPhoto).filter(
        PlantPhoto.diagnosis_status.in_([DiagnosisStatus.PENDING, DiagnosisStatus.FAILED])
    )

    if user_id:
        query = query.filter(PlantPhoto.user_id == user_id)

    return query.order_by(PlantPhoto.created_at).all()


def get_photos_with_diagnosis(db: Session, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Get photos with their latest diagnosis for user dashboard."""
    photos = db.query(PlantPhoto).filter(
        PlantPhoto.user_id == user_id
    ).order_by(desc(PlantPhoto.created_at)).limit(limit).all()

    result = []
    for photo in photos:
        diagnosis = get_diagnosis_by_photo_id(db, photo.id, user_id)
        result.append({
            "photo": photo,
            "diagnosis": diagnosis,
            "has_diagnosis": diagnosis is not None
        })

    return result
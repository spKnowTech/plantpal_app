from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from repositories.photo_repo import (
    create_photo, get_photo_by_id, update_photo_status, delete_photo,
    create_diagnosis, get_diagnosis_by_photo_id, update_diagnosis,
    get_user_photos, get_photos_with_diagnosis, get_photos_needing_diagnosis
)
from repositories.plant_repo import get_plant
from schemas.photo import (
    PhotoCreate, PhotoResponse, DiagnosisCreate, DiagnosisResponse,
    PhotoWithDiagnosis, DiagnosisStatus, DiagnosisUpdate
)
from utils.image_processor import (
    save_uploaded_image, delete_image_files, get_image_url, validate_image_exists
)
from models.photo import PlantPhoto
from typing import Optional, Dict, List, Any, Tuple
from services.user_service import get_current_active_user

async def upload_plant_photo(db: Session, file: UploadFile, user_id: int,
                             plant_id: Optional[int] = None,
                             upload_context: Optional[str] = None) -> PhotoResponse:
    """
    Upload and save a plant photo.

    Args:
        db: Database session
        file: Uploaded file
        user_id: ID of the user uploading
        plant_id: Optional ID of the associated plant
        upload_context: Optional context/description from user

    Returns:
        PhotoResponse with uploaded photo details
    """
    # Validate plant exists if plant_id is provided
    if plant_id:
        plant = get_plant(db, plant_id, user_id)
        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found")

    try:
        # get current activate user
        user = get_current_active_user(user_id, db)
        # Save image file for the user
        file_path, file_info = await save_uploaded_image(file, user)

        # Create photo record
        photo_data = PhotoCreate(
            user_id=user_id,
            plant_id=plant_id,
            image_path=file_path,
            original_filename=file_info['original_filename'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            upload_context=upload_context,
            diagnosis_status=DiagnosisStatus.PENDING
        )

        photo = create_photo(db, photo_data)

        # Convert to response format
        return PhotoResponse.model_validate(photo)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")


def get_user_photo_by_id(db: Session, photo_id: int, user_id: int) -> Optional[PhotoResponse]:
    """Get photo by ID for specific user."""
    photo = get_photo_by_id(db, photo_id, user_id)
    if photo:
        return PhotoResponse.model_validate(photo)
    return None


def get_user_photos_list(db: Session, user_id: int, limit: int = 50, offset: int = 0) -> List[PhotoResponse]:
    """Get paginated list of user's photos."""
    photos = get_user_photos(db, user_id, limit, offset)
    return [PhotoResponse.model_validate(photo) for photo in photos]


def get_user_photos_with_diagnoses(db: Session, user_id: int, limit: int = 20) -> List[PhotoWithDiagnosis]:
    """Get user's photos with their diagnoses for dashboard."""
    photos_data = get_photos_with_diagnosis(db, user_id, limit)

    result = []
    for item in photos_data:
        photo = item['photo']
        diagnosis = item['diagnosis']

        # Get plant name if available
        plant_name = None
        if photo.plant_id:
            plant = get_plant(db, photo.plant_id, user_id)
            if plant:
                plant_name = plant.name

        photo_with_diagnosis = PhotoWithDiagnosis(
            photo=PhotoResponse.model_validate(photo),
            diagnosis=DiagnosisResponse.model_validate(diagnosis) if diagnosis else None,
            plant_name=plant_name
        )
        result.append(photo_with_diagnosis)

    return result


def delete_user_photo(db: Session, photo_id: int, user_id: int) -> bool:
    """Delete a photo and its associated files."""
    photo = get_photo_by_id(db, photo_id, user_id)
    if not photo:
        return False

    try:
        # Delete physical files
        if validate_image_exists(photo.image_path):
            delete_image_files(photo.image_path)

        # Delete database record (cascade will handle related records)
        success = delete_photo(db, photo_id, user_id)
        return success

    except Exception as e:
        print(f"Error deleting photo {photo_id}: {str(e)}")
        return False


def update_photo_diagnosis_status(db: Session, photo_id: int, user_id: int,
                                  status: DiagnosisStatus) -> Optional[PhotoResponse]:
    """Update photo diagnosis status."""
    photo = update_photo_status(db, photo_id, status, user_id)
    if photo:
        return PhotoResponse.model_validate(photo)
    return None


def create_photo_diagnosis(db: Session, photo_id: int, user_id: int,
                           diagnosis_text: str, confidence_score: Optional[float] = None,
                           identified_issues: Optional[Dict[str, List[str]]] = None,
                           recommended_actions: Optional[Dict[str, List[str]]] = None,
                           similar_cases_used: Optional[Dict[str, Any]] = None) -> DiagnosisResponse:
    """Create a diagnosis for a photo."""
    # Verify photo exists and belongs to user
    photo = get_photo_by_id(db, photo_id, user_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Create diagnosis
    diagnosis_data = DiagnosisCreate(
        photo_id=photo_id,
        user_id=user_id,
        diagnosis_text=diagnosis_text,
        confidence_score=confidence_score,
        identified_issues=identified_issues,
        recommended_actions=recommended_actions,
        similar_cases_used=similar_cases_used
    )

    diagnosis = create_diagnosis(db, diagnosis_data)

    # Update photo status to analyzed
    update_photo_status(db, photo_id, DiagnosisStatus.ANALYZED, user_id)

    return DiagnosisResponse.model_validate(diagnosis)


def get_photo_diagnosis(db: Session, photo_id: int, user_id: int) -> Optional[DiagnosisResponse]:
    """Get the latest diagnosis for a photo."""
    diagnosis = get_diagnosis_by_photo_id(db, photo_id, user_id)
    if diagnosis:
        return DiagnosisResponse.model_validate(diagnosis)
    return None


def update_photo_diagnosis(db: Session, diagnosis_id: int, user_id: int,
                           update_data: DiagnosisUpdate) -> Optional[DiagnosisResponse]:
    """Update an existing diagnosis."""
    diagnosis = update_diagnosis(db, diagnosis_id, update_data, user_id)
    if diagnosis:
        return DiagnosisResponse.model_validate(diagnosis)
    return None


def get_photo_url_for_display(photo: PhotoResponse, thumbnail: bool = False) -> str:
    """Get URL for displaying photo in frontend."""
    return get_image_url(photo.image_path, thumbnail=thumbnail)


def get_photos_needing_analysis(db: Session, user_id: Optional[int] = None) -> List[PhotoResponse]:
    """Get photos that need diagnosis."""
    photos = get_photos_needing_diagnosis(db, user_id)
    return [PhotoResponse.model_validate(photo) for photo in photos]


def prepare_photo_for_analysis(db: Session, photo_id: int, user_id: int) -> Dict[str, Any]:
    """Prepare photo data for AI analysis."""
    photo = get_photo_by_id(db, photo_id, user_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Update status to analyzing
    update_photo_status(db, photo_id, DiagnosisStatus.ANALYZING, user_id)

    # Prepare data for analysis
    analysis_data = {
        'photo_id': photo.id,
        'user_id': user_id,
        'image_path': photo.image_path,
        'upload_context': photo.upload_context,
        'plant_id': photo.plant_id,
        'original_filename': photo.original_filename,
        'created_at': photo.created_at.isoformat()
    }

    # Add plant context if available
    if photo.plant_id:
        plant = get_plant(db, photo.plant_id, user_id)
        if plant:
            analysis_data['plant_context'] = {
                'name': plant.name,
                'species': plant.species,
                'location': plant.location,
                'current_issues': plant.notes
            }

    return analysis_data


def handle_analysis_failure(db: Session, photo_id: int, user_id: int, error_message: str) -> None:
    """Handle failed photo analysis."""
    # Update photo status to failed
    update_photo_status(db, photo_id, DiagnosisStatus.FAILED, user_id)

    # Create a diagnosis record with the error
    try:
        diagnosis_data = DiagnosisCreate(
            photo_id=photo_id,
            user_id=user_id,
            diagnosis_text=f"Analysis failed: {error_message}",
            confidence_score=0.0,
            identified_issues={"errors": ["analysis_failed"]},
            recommended_actions={"immediate": ["retry_analysis", "contact_support"]}
        )
        create_diagnosis(db, diagnosis_data)
    except Exception as e:
        print(f"Failed to create error diagnosis for photo {photo_id}: {str(e)}")


def get_analysis_statistics(db: Session, user_id: int) -> Dict[str, Any]:
    """Get photo analysis statistics for user."""
    from repositories.photo_repo import get_diagnosis_accuracy_stats, get_common_issues

    # Get accuracy stats
    stats = get_diagnosis_accuracy_stats(db, user_id, days=30)

    # Get common issues
    common_issues = get_common_issues(db, user_id, limit=5)

    # Get photo counts by status
    user_photos = get_user_photos(db, user_id, limit=1000)  # Get all for counting
    status_counts = {}
    for photo in user_photos:
        status = photo.diagnosis_status
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        'accuracy_stats': stats,
        'common_issues': common_issues,
        'photo_counts_by_status': status_counts,
        'total_photos': len(user_photos)
    }


def validate_photo_for_chat(db: Session, photo_id: int, user_id: int) -> Tuple[
    bool, Optional[str], Optional[PlantPhoto]]:
    """
    Validate photo for chat integration.

    Returns:
        Tuple of (is_valid, error_message, photo_object)
    """
    photo = get_photo_by_id(db, photo_id, user_id)

    if not photo:
        return False, "Photo not found", None

    if not validate_image_exists(photo.image_path):
        return False, "Image file not found", None

    return True, None, photo


def get_photo_context_for_chat(photo: PlantPhoto, db: Session) -> Dict[str, Any]:
    """Get photo context for chat AI analysis."""
    context = {
        'photo_id': photo.id,
        'upload_context': photo.upload_context,
        'diagnosis_status': photo.diagnosis_status,
        'created_at': photo.created_at.isoformat(),
        'file_info': {
            'original_filename': photo.original_filename,
            'file_size': photo.file_size,
            'mime_type': photo.mime_type
        }
    }

    # Add plant context if available
    if photo.plant_id:
        plant = get_plant(db, photo.plant_id, photo.user_id)
        if plant:
            context['plant'] = {
                'name': plant.name,
                'species': plant.species,
                'location': plant.location,
                'notes': plant.notes
            }

    # Add existing diagnosis if available
    existing_diagnosis = get_diagnosis_by_photo_id(db, photo.id, photo.user_id)
    if existing_diagnosis:
        context['existing_diagnosis'] = {
            'diagnosis_text': existing_diagnosis.diagnosis_text,
            'confidence_score': existing_diagnosis.confidence_score,
            'identified_issues': existing_diagnosis.identified_issues,
            'recommended_actions': existing_diagnosis.recommended_actions,
            'created_at': existing_diagnosis.created_at.isoformat()
        }

    return context
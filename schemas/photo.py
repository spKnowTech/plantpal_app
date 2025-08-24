from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class DiagnosisStatus(str, Enum):
    """Enum for diagnosis status."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class TreatmentOutcome(str, Enum):
    """Enum for treatment outcomes."""
    PENDING = "pending"
    SUCCESSFUL = "successful"
    PARTIALLY_SUCCESSFUL = "partially_successful"
    FAILED = "failed"


class FeedbackType(str, Enum):
    """Enum for feedback types."""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    PARTIALLY_HELPFUL = "partially_helpful"


# Photo Upload Schemas
class PhotoUpload(BaseModel):
    """Schema for photo upload request."""
    plant_id: Optional[int] = None
    upload_context: Optional[str] = Field(None, max_length=500, description="User's description of the issue")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "photo_id": 1,
                "upload_context": "My plant's leaves are turning yellow and I'm worried"
            }
        }
    )


class PhotoCreate(BaseModel):
    """Schema for creating a photo record."""
    plant_id: Optional[int] = None
    user_id: int
    image_path: str
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    upload_context: Optional[str] = None
    diagnosis_status: DiagnosisStatus = DiagnosisStatus.PENDING


class PhotoResponse(BaseModel):
    """Schema for photo response."""
    id: int
    plant_id: Optional[int]
    user_id: int
    image_path: str
    original_filename: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    diagnosis_status: DiagnosisStatus
    upload_context: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


# Diagnosis Schemas
class DiagnosisCreate(BaseModel):
    """Schema for creating a diagnosis."""
    photo_id: int
    user_id: int
    diagnosis_text: str
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    identified_issues: Optional[Dict[str, List[str]]] = None
    recommended_actions: Optional[Dict[str, List[str]]] = None
    similar_cases_used: Optional[Dict[str, Any]] = None

    @field_validator('identified_issues')
    def validate_identified_issues(cls, v):
        """Validate identified issues structure."""
        if v is not None:
            expected_keys = {'diseases', 'pests', 'deficiencies', 'environmental', 'symptoms'}
            if not isinstance(v, dict):
                raise ValueError('identified_issues must be a dictionary')

            # Check keys
            for key in v.keys():
                if key not in expected_keys:
                    raise ValueError(f"Unexpected key '{key}'. Allowed: {expected_keys}")

            # Allow any keys but validate values are lists
            for key, value in v.items():
                if not isinstance(value, list):
                    raise ValueError(f'Value for {key} must be a list')
        return v

    @field_validator('recommended_actions')
    def validate_recommended_actions(cls, v):
        """Validate recommended actions structure."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('recommended_actions must be a dictionary')
            # Allow any keys but validate values are lists
            for key, value in v.items():
                if not isinstance(value, list):
                    raise ValueError(f'Value for {key} must be a list')
        return v


class DiagnosisUpdate(BaseModel):
    """Schema for updating a diagnosis."""
    diagnosis_text: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    identified_issues: Optional[Dict[str, List[str]]] = None
    recommended_actions: Optional[Dict[str, List[str]]] = None
    treatment_outcome: Optional[TreatmentOutcome] = None
    user_feedback_rating: Optional[int] = Field(None, ge=1, le=5)


class DiagnosisResponse(BaseModel):
    """Schema for diagnosis response."""
    id: int
    photo_id: int
    user_id: int
    diagnosis_text: str
    confidence_score: Optional[float]
    identified_issues: Optional[Dict[str, List[str]]]
    recommended_actions: Optional[Dict[str, List[str]]]
    similar_cases_used: Optional[Dict[str, Any]]
    treatment_outcome: Optional[TreatmentOutcome]
    user_feedback_rating: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


# Embedding Schemas
class EmbeddingCreate(BaseModel):
    """Schema for creating an embedding."""
    photo_id: int
    user_id: int
    embedding_vector: Optional[List[float]] = None  # Will be list instead of VECTOR type
    embedding_model: str
    metadata_info: Optional[Dict[str, Any]] = None


class EmbeddingResponse(BaseModel):
    """Schema for embedding response."""
    id: int
    photo_id: int
    user_id: int
    embedding_model: str
    metadata_info: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# Feedback Schemas
class FeedbackCreate(BaseModel):
    """Schema for creating diagnosis feedback."""
    diagnosis_id: int
    user_id: int
    feedback_type: FeedbackType
    feedback_text: Optional[str] = Field(None, max_length=1000)
    improvement_suggestion: Optional[str] = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: int
    diagnosis_id: int
    user_id: int
    feedback_type: FeedbackType
    feedback_text: Optional[str]
    improvement_suggestion: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# Combined Schemas for Complex Operations
class PhotoWithDiagnosis(BaseModel):
    """Schema combining photo with its diagnosis."""
    photo: PhotoResponse
    diagnosis: Optional[DiagnosisResponse] = None
    plant_name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class DiagnosisAnalysisRequest(BaseModel):
    """Schema for photo analysis request."""
    photo_id: int
    user_message: Optional[str] = Field(None, description="Additional context from user")
    use_rag: bool = Field(True, description="Whether to use RAG for enhanced analysis")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "photo_id": 1,
                "user_message": "I think my plant might have root rot",
                "use_rag": True
            }
        }
    )


class SimilarCase(BaseModel):
    """Schema for similar cases used in RAG."""
    photo_id: int
    diagnosis_id: int
    similarity_score: float
    diagnosis_summary: str
    treatment_outcome: Optional[TreatmentOutcome]
    plant_type: Optional[str]

    model_config = {
        "from_attributes": True
    }


class RAGAnalysisResult(BaseModel):
    """Schema for RAG-enhanced analysis result."""
    diagnosis: DiagnosisResponse
    similar_cases: List[SimilarCase]
    confidence_boost: float  # How much RAG improved confidence
    context_summary: str  # Summary of historical context used

    model_config = {
        "from_attributes": True
    }
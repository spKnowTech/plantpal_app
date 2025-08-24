from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session

from plant_pal_bot.ai_bot_client import embed_text
from repositories.photo_repo import (
create_embedding, get_embedding_by_photo_id, find_similar_embeddings
)
from schemas.photo import EmbeddingCreate
from models.photo import PhotoDiagnosis
from settings import Setting

def generate_diagnosis_text_for_embedding(diagnosis_data: Dict[str, Any],
                                          plant_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a comprehensive text representation for embedding generation.

    Args:
        diagnosis_data: Diagnosis information
        plant_context: Optional plant context information

    Returns:
        Text representation suitable for embedding
    """
    text_parts = []

    # Add plant context if available
    if plant_context:
        if plant_context.get('species'):
            text_parts.append(f"Plant species: {plant_context['species']}")
        if plant_context.get('name'):
            text_parts.append(f"Plant name: {plant_context['name']}")
        if plant_context.get('location'):
            text_parts.append(f"Location: {plant_context['location']}")

    # Add diagnosis text
    if diagnosis_data.get('diagnosis_text'):
        text_parts.append(f"Diagnosis: {diagnosis_data['diagnosis_text']}")

    # Add identified issues
    if diagnosis_data.get('identified_issues'):
        issues = diagnosis_data['identified_issues']
        for category, issue_list in issues.items():
            if issue_list:
                category_text = f"{category.replace('_', ' ')}: {', '.join(issue_list)}"
                text_parts.append(category_text)

    # Add recommended actions
    if diagnosis_data.get('recommended_actions'):
        actions = diagnosis_data['recommended_actions']
        for category, action_list in actions.items():
            if action_list:
                action_text = f"{category.replace('_', ' ')} actions: {', '.join(action_list)}"
                text_parts.append(action_text)

    # Add treatment outcome if available
    if diagnosis_data.get('treatment_outcome'):
        text_parts.append(f"Treatment outcome: {diagnosis_data['treatment_outcome']}")

    # Add user context if available
    if diagnosis_data.get('upload_context'):
        text_parts.append(f"User concern: {diagnosis_data['upload_context']}")

    return " | ".join(text_parts)


def create_embedding_metadata(diagnosis_data: Dict[str, Any],
                              plant_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create metadata dictionary for embedding storage.

    Args:
        diagnosis_data: Diagnosis information
        plant_context: Optional plant context information

    Returns:
        Metadata dictionary
    """
    metadata = {
        'diagnosis_id': diagnosis_data.get('diagnosis_id'),
        'confidence_score': diagnosis_data.get('confidence_score'),
        'treatment_outcome': diagnosis_data.get('treatment_outcome'),
        'created_at': diagnosis_data.get('created_at'),
    }

    # Add plant metadata
    if plant_context:
        metadata['plant_species'] = plant_context.get('species')
        metadata['plant_location'] = plant_context.get('location')
        metadata['plant_name'] = plant_context.get('name')

    # Add issue categories
    if diagnosis_data.get('identified_issues'):
        issues = diagnosis_data['identified_issues']
        metadata['has_diseases'] = len(issues.get('diseases', [])) > 0
        metadata['has_pests'] = len(issues.get('pests', [])) > 0
        metadata['has_deficiencies'] = len(issues.get('deficiencies', [])) > 0
        metadata['has_environmental_issues'] = len(issues.get('environmental', [])) > 0

        # Store specific issues
        all_issues = []
        for issue_list in issues.values():
            all_issues.extend(issue_list)
        metadata['main_issues'] = all_issues[:5]  # Store top 5 issues

    # Add action categories
    if diagnosis_data.get('recommended_actions'):
        actions = diagnosis_data['recommended_actions']
        metadata['has_immediate_actions'] = len(actions.get('immediate', [])) > 0
        metadata['has_longterm_actions'] = len(actions.get('long_term', [])) > 0

    return metadata


def generate_and_store_embedding(db: Session, photo_id: int, user_id: int,
                                 diagnosis_data: Dict[str, Any],
                                 plant_context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Generate and store embedding for a diagnosis.

    Args:
        db: Database session
        photo_id: Photo ID
        user_id: User ID
        diagnosis_data: Diagnosis information
        plant_context: Optional plant context

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if embedding already exists
        existing_embedding = get_embedding_by_photo_id(db, photo_id)
        if existing_embedding:
            print(f"Embedding already exists for photo {photo_id}")
            return True

        # Generate text for embedding
        embedding_text = generate_diagnosis_text_for_embedding(diagnosis_data, plant_context)

        # Generate embedding
        embedding_vector = embed_text(embedding_text)

        # Create metadata
        metadata = create_embedding_metadata(diagnosis_data, plant_context)

        # Store in database
        embedding_data = EmbeddingCreate(
            photo_id=photo_id,
            user_id=user_id,
            embedding_vector=embedding_vector,
            embedding_model=Setting.embedding_model,
            metadata=metadata
        )

        create_embedding(db, embedding_data)
        return True

    except Exception as e:
        print(f"Failed to generate and store embedding for photo {photo_id}: {str(e)}")
        return False


def calculate_cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Cosine similarity score (0 to 1)
    """
    try:
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Normalize to 0-1 range (cosine similarity can be -1 to 1)
        return (similarity + 1) / 2

    except Exception as e:
        print(f"Error calculating cosine similarity: {str(e)}")
        return 0.0


def find_similar_cases_by_text_similarity(db: Session, query_text: str,
                                          exclude_user_id: Optional[int] = None,
                                          plant_species: Optional[str] = None,
                                          limit: int = 10) -> List[Dict[str, Any]]:
    """
    Find similar cases using text embedding similarity.

    Args:
        db: Database session
        query_text: Text to find similar cases for
        exclude_user_id: User ID to exclude from results
        plant_species: Optional plant species filter
        limit: Maximum number of results

    Returns:
        List of similar cases with similarity scores
    """
    try:
        # Generate embedding for query text
        query_embedding = embed_text(query_text)

        # Get all embeddings from database
        candidate_embeddings = find_similar_embeddings(
            db, query_embedding, limit=limit * 2, exclude_user_id=exclude_user_id
        )

        # Calculate similarities
        similar_cases = []
        for embedding_record in candidate_embeddings:
            if not embedding_record.embedding_vector:
                continue

            # Filter by plant species if specified
            if plant_species and embedding_record.metadata:
                record_species = embedding_record.metadata.get('plant_species', '').lower()
                if plant_species.lower() not in record_species:
                    continue

            # Calculate similarity
            similarity = calculate_cosine_similarity(query_embedding, embedding_record.embedding_vector)

            similar_cases.append({
                'embedding_id': embedding_record.id,
                'photo_id': embedding_record.photo_id,
                'user_id': embedding_record.user_id,
                'similarity_score': similarity,
                'metadata': embedding_record.metadata,
                'created_at': embedding_record.created_at
            })

        # Sort by similarity and limit results
        similar_cases.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_cases[:limit]

    except Exception as e:
        print(f"Error finding similar cases: {str(e)}")
        return []


def enhance_query_with_context(original_query: str, plant_context: Optional[Dict[str, Any]] = None,
                               user_history: Optional[List[str]] = None) -> str:
    """
    Enhance query text with additional context for better similarity search.

    Args:
        original_query: Original query text
        plant_context: Plant context information
        user_history: User's previous queries/issues

    Returns:
        Enhanced query text
    """
    query_parts = [original_query]

    # Add plant context
    if plant_context:
        if plant_context.get('species'):
            query_parts.append(f"plant species {plant_context['species']}")
        if plant_context.get('location'):
            query_parts.append(f"located {plant_context['location']}")
        if plant_context.get('current_issues'):
            query_parts.append(f"current issues {plant_context['current_issues']}")

    # Add user history context (recent issues)
    if user_history:
        recent_history = user_history[-3:]  # Last 3 interactions
        history_text = " ".join(recent_history)
        query_parts.append(f"user history context: {history_text}")

    return " | ".join(query_parts)


def batch_generate_embeddings_for_existing_diagnoses(db: Session, limit: int = 100) -> Dict[str, int]:
    """
    Generate embeddings for existing diagnoses that don't have them yet.

    Args:
        db: Database session  
        limit: Maximum number of diagnoses to process

    Returns:
        Dictionary with processing statistics
    """

    stats = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0
    }

    try:
        # Get diagnoses without embeddings
        # This is a simplified approach - in production you might want a more sophisticated query
        diagnoses = db.query(PhotoDiagnosis).limit(limit).all()

        for diagnosis in diagnoses:
            stats['processed'] += 1

            # Check if embedding already exists
            existing_embedding = get_embedding_by_photo_id(db, diagnosis.photo_id)
            if existing_embedding:
                stats['skipped'] += 1
                continue

            # Prepare diagnosis data
            diagnosis_data = {
                'diagnosis_id': diagnosis.id,
                'diagnosis_text': diagnosis.diagnosis_text,
                'identified_issues': diagnosis.identified_issues,
                'recommended_actions': diagnosis.recommended_actions,
                'confidence_score': diagnosis.confidence_score,
                'treatment_outcome': diagnosis.treatment_outcome,
                'created_at': diagnosis.created_at.isoformat() if diagnosis.created_at else None,
                'upload_context': getattr(diagnosis.photo, 'upload_context', None) if diagnosis.photo else None
            }

            # Get plant context if available
            plant_context = None
            if diagnosis.photo and diagnosis.photo.plant:
                plant = diagnosis.photo.plant
                plant_context = {
                    'species': plant.species,
                    'name': plant.name,
                    'location': plant.location
                }

            # Generate and store embedding
            success = generate_and_store_embedding(
                db, diagnosis.photo_id, diagnosis.user_id, diagnosis_data, plant_context
            )

            if success:
                stats['successful'] += 1
            else:
                stats['failed'] += 1

        return stats

    except Exception as e:
        print(f"Error in batch embedding generation: {str(e)}")
        stats['error'] = str(e)
        return stats
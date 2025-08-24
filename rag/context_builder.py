from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from repositories.photo_repo import (
    get_successful_diagnoses_for_rag, get_user_diagnoses_history,
    get_diagnosis_by_photo_id
)
from rag.embeddings_generator import find_similar_cases_by_text_similarity, enhance_query_with_context
from schemas.photo import TreatmentOutcome


def build_rag_context_for_diagnosis(db: Session, query_text: str, user_id: int,
                                    plant_context: Optional[Dict[str, Any]] = None,
                                    user_history: Optional[List[str]] = None,
                                    max_similar_cases: int = 5) -> Dict[str, Any]:
    """
    Build RAG context by finding similar historical cases.

    Args:
        db: Database session
        query_text: User's query or photo context
        user_id: Current user ID
        plant_context: Context about the plant
        user_history: User's previous interactions
        max_similar_cases: Maximum number of similar cases to include

    Returns:
        Dictionary containing RAG context information
    """
    try:
        # Enhance query with additional context
        enhanced_query = enhance_query_with_context(query_text, plant_context, user_history)

        # Get plant species for filtering if available
        plant_species = plant_context.get('species') if plant_context else None

        # Find similar cases using embedding similarity
        similar_cases = find_similar_cases_by_text_similarity(
            db, enhanced_query, exclude_user_id=user_id,
            plant_species=plant_species, limit=max_similar_cases * 2
        )

        # Get additional context from successful treatments
        successful_cases = get_successful_diagnoses_for_rag(
            db, plant_species=plant_species, limit=10
        )

        # Get user's own history for personalization
        user_past_diagnoses = get_user_diagnoses_history(db, user_id, limit=20)

        # Build comprehensive context
        context = {
            'similar_cases': process_similar_cases(db, similar_cases[:max_similar_cases]),
            'successful_treatments': process_successful_cases(successful_cases),
            'user_history_patterns': analyze_user_history_patterns(user_past_diagnoses),
            'plant_specific_insights': get_plant_specific_insights(db, plant_species) if plant_species else {},
            'context_metadata': {
                'total_similar_cases': len(similar_cases),
                'successful_cases_available': len(successful_cases),
                'user_history_length': len(user_past_diagnoses),
                'plant_species': plant_species,
                'enhanced_query_used': enhanced_query != query_text
            }
        }

        return context

    except Exception as e:
        print(f"Error building RAG context: {str(e)}")
        return {
            'similar_cases': [],
            'successful_treatments': [],
            'user_history_patterns': {},
            'plant_specific_insights': {},
            'context_metadata': {'error': str(e)}
        }


def process_similar_cases(db: Session, similar_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process similar cases to extract relevant information for RAG context.

    Args:
        db: Database session
        similar_cases: List of similar cases from embedding search

    Returns:
        Processed similar cases with diagnosis details
    """
    processed_cases = []

    for case in similar_cases:
        try:
            # Get the actual diagnosis record
            diagnosis = get_diagnosis_by_photo_id(db, case['photo_id'], case['user_id'])

            if not diagnosis:
                continue

            processed_case = {
                'similarity_score': case['similarity_score'],
                'diagnosis_summary': create_diagnosis_summary(diagnosis),
                'identified_issues': diagnosis.identified_issues or {},
                'recommended_actions': diagnosis.recommended_actions or {},
                'treatment_outcome': diagnosis.treatment_outcome,
                'confidence_score': diagnosis.confidence_score,
                'plant_context': extract_plant_context_from_metadata(case.get('metadata', {})),
                'time_since_diagnosis': calculate_time_since_diagnosis(diagnosis.created_at),
                'success_indicators': calculate_success_indicators(diagnosis)
            }

            processed_cases.append(processed_case)

        except Exception as e:
            print(f"Error processing similar case: {str(e)}")
            continue

    return processed_cases


def process_successful_cases(successful_diagnoses: List[Any]) -> List[Dict[str, Any]]:
    """
    Process successful diagnosis cases for RAG context.

    Args:
        successful_diagnoses: List of successful diagnosis records

    Returns:
        Processed successful cases
    """
    processed_cases = []

    for diagnosis in successful_diagnoses:
        try:
            case_data = {
                'diagnosis_summary': create_diagnosis_summary(diagnosis),
                'successful_treatments': extract_successful_treatments(diagnosis),
                'issues_resolved': diagnosis.identified_issues or {},
                'treatment_timeline': estimate_treatment_timeline(diagnosis),
                'confidence_score': diagnosis.confidence_score,
                'key_success_factors': identify_key_success_factors(diagnosis)
            }

            processed_cases.append(case_data)

        except Exception as e:
            print(f"Error processing successful case: {str(e)}")
            continue

    return processed_cases


def analyze_user_history_patterns(user_diagnoses: List[Any]) -> Dict[str, Any]:
    """
    Analyze patterns in user's diagnosis history.

    Args:
        user_diagnoses: List of user's past diagnoses

    Returns:
        Dictionary with user history patterns
    """
    if not user_diagnoses:
        return {}

    patterns = {
        'common_issues': {},
        'recurring_problems': [],
        'treatment_preferences': {},
        'success_rate': 0.0,
        'plant_types_experience': {},
        'seasonal_patterns': {},
        'diagnosis_frequency': calculate_diagnosis_frequency(user_diagnoses)
    }

    try:
        # Analyze common issues
        all_issues = {}
        successful_treatments = {}
        plant_types = {}

        for diagnosis in user_diagnoses:
            # Count issues
            if diagnosis.identified_issues:
                for category, issues in diagnosis.identified_issues.items():
                    for issue in issues:
                        key = f"{category}:{issue}"
                        all_issues[key] = all_issues.get(key, 0) + 1

            # Analyze successful treatments
            if diagnosis.treatment_outcome == TreatmentOutcome.SUCCESSFUL and diagnosis.recommended_actions:
                for category, actions in diagnosis.recommended_actions.items():
                    for action in actions:
                        key = f"{category}:{action}"
                        successful_treatments[key] = successful_treatments.get(key, 0) + 1

            # Track plant types
            if diagnosis.photo and diagnosis.photo.plant and diagnosis.photo.plant.species:
                species = diagnosis.photo.plant.species
                plant_types[species] = plant_types.get(species, 0) + 1

        # Process patterns
        patterns['common_issues'] = dict(sorted(all_issues.items(), key=lambda x: x[1], reverse=True)[:10])
        patterns['treatment_preferences'] = dict(
            sorted(successful_treatments.items(), key=lambda x: x[1], reverse=True)[:5])
        patterns['plant_types_experience'] = plant_types

        # Calculate success rate
        successful_count = sum(1 for d in user_diagnoses if d.treatment_outcome == TreatmentOutcome.SUCCESSFUL)
        patterns['success_rate'] = successful_count / len(user_diagnoses) if user_diagnoses else 0.0

        # Identify recurring problems (issues that appear multiple times)
        recurring_issues = [issue for issue, count in all_issues.items() if count > 1]
        patterns['recurring_problems'] = recurring_issues[:5]

    except Exception as e:
        print(f"Error analyzing user history patterns: {str(e)}")
        patterns['error'] = str(e)

    return patterns


def get_plant_specific_insights(db: Session, plant_species: str) -> Dict[str, Any]:
    """
    Get insights specific to a plant species from historical data.

    Args:
        db: Database session
        plant_species: Plant species to analyze

    Returns:
        Plant-specific insights
    """
    try:
        # Get successful diagnoses for this plant species
        successful_cases = get_successful_diagnoses_for_rag(db, plant_species=plant_species, limit=20)

        if not successful_cases:
            return {'message': f'No historical data available for {plant_species}'}

        insights = {
            'species': plant_species,
            'total_cases': len(successful_cases),
            'common_issues': {},
            'effective_treatments': {},
            'average_confidence': 0.0,
            'care_tips': [],
            'prevention_strategies': []
        }

        # Analyze common issues for this species
        species_issues = {}
        species_treatments = {}
        confidence_scores = []

        for diagnosis in successful_cases:
            if diagnosis.confidence_score:
                confidence_scores.append(diagnosis.confidence_score)

            if diagnosis.identified_issues:
                for category, issues in diagnosis.identified_issues.items():
                    for issue in issues:
                        key = f"{category}:{issue}"
                        species_issues[key] = species_issues.get(key, 0) + 1

            if diagnosis.recommended_actions:
                for category, actions in diagnosis.recommended_actions.items():
                    for action in actions:
                        key = f"{category}:{action}"
                        species_treatments[key] = species_treatments.get(key, 0) + 1

        # Process insights
        insights['common_issues'] = dict(sorted(species_issues.items(), key=lambda x: x[1], reverse=True)[:5])
        insights['effective_treatments'] = dict(
            sorted(species_treatments.items(), key=lambda x: x[1], reverse=True)[:5])
        insights['average_confidence'] = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # Generate care tips based on most common successful treatments
        care_tips = []
        for treatment, count in insights['effective_treatments'].items():
            if count >= 2:  # Only include treatments that worked multiple times
                care_tips.append(f"{treatment.replace(':', ' - ')} (successful in {count} cases)")
        insights['care_tips'] = care_tips[:5]

        return insights

    except Exception as e:
        print(f"Error getting plant-specific insights: {str(e)}")
        return {'error': str(e), 'species': plant_species}


def create_diagnosis_summary(diagnosis: Any) -> str:
    """Create a concise summary of a diagnosis."""
    summary_parts = []

    # Add main diagnosis text (first sentence or 100 chars)
    if diagnosis.diagnosis_text:
        first_sentence = diagnosis.diagnosis_text.split('.')[0]
        if len(first_sentence) > 100:
            first_sentence = first_sentence[:100] + "..."
        summary_parts.append(first_sentence)

    # Add key issues
    if diagnosis.identified_issues:
        key_issues = []
        for category, issues in diagnosis.identified_issues.items():
            key_issues.extend(issues[:2])  # Top 2 issues per category
        if key_issues:
            summary_parts.append(f"Issues: {', '.join(key_issues[:3])}")

    return ". ".join(summary_parts) if summary_parts else "No diagnosis summary available"


def extract_plant_context_from_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract plant context from embedding metadata."""
    return {
        'species': metadata.get('plant_species'),
        'location': metadata.get('plant_location'),
        'name': metadata.get('plant_name')
    }


def calculate_time_since_diagnosis(created_at: datetime) -> Dict[str, Any]:
    """Calculate time since diagnosis was created."""
    if not created_at:
        return {'error': 'No creation date available'}

    now = datetime.now(timezone.utc)
    if created_at.tzinfo:
        # Make timezone-aware comparison
        now = now.replace(tzinfo=timezone.utc)

    time_diff = now - created_at

    return {
        'days_ago': time_diff.days,
        'hours_ago': time_diff.seconds // 3600,
        'is_recent': time_diff.days < 7,
        'is_very_recent': time_diff.days < 1,
        'formatted': format_time_since(time_diff)
    }


def format_time_since(time_diff: timedelta) -> str:
    """Format timedelta into human-readable string."""
    days = time_diff.days
    hours = time_diff.seconds // 3600

    if days > 30:
        return f"{days // 30} month{'s' if days // 30 > 1 else ''} ago"
    elif days > 7:
        return f"{days // 7} week{'s' if days // 7 > 1 else ''} ago"
    elif days > 0:
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        return "Less than an hour ago"


def calculate_success_indicators(diagnosis: Any) -> Dict[str, Any]:
    """Calculate indicators of diagnosis success."""
    indicators = {
        'has_successful_outcome': diagnosis.treatment_outcome == TreatmentOutcome.SUCCESSFUL,
        'high_confidence': diagnosis.confidence_score and diagnosis.confidence_score > 0.7,
        'has_specific_issues': bool(diagnosis.identified_issues),
        'has_actionable_recommendations': bool(diagnosis.recommended_actions),
        'user_rated_highly': diagnosis.user_feedback_rating and diagnosis.user_feedback_rating >= 4
    }

    # Calculate overall success score
    success_score = sum([
        1 if indicators['has_successful_outcome'] else 0,
        0.5 if indicators['high_confidence'] else 0,
        0.3 if indicators['has_specific_issues'] else 0,
        0.2 if indicators['has_actionable_recommendations'] else 0,
        0.3 if indicators['user_rated_highly'] else 0
    ])

    indicators['overall_success_score'] = min(1.0, success_score)

    return indicators


def extract_successful_treatments(diagnosis: Any) -> List[str]:
    """Extract successful treatment actions from a diagnosis."""
    treatments = []

    if diagnosis.recommended_actions:
        # Prioritize immediate and short-term actions for successful cases
        for category in ['immediate', 'short_term', 'long_term']:
            actions = diagnosis.recommended_actions.get(category, [])
            for action in actions[:2]:  # Top 2 actions per category
                treatments.append(f"{category}: {action}")

    return treatments[:5]  # Limit to top 5 treatments


def estimate_treatment_timeline(diagnosis: Any) -> Dict[str, Any]:
    """Estimate treatment timeline based on recommended actions."""
    timeline = {
        'immediate': [],
        'short_term': [],
        'long_term': [],
        'monitoring': []
    }

    if diagnosis.recommended_actions:
        for category, actions in diagnosis.recommended_actions.items():
            timeline[category] = actions[:3]  # Top 3 actions per timeframe

    return timeline


def identify_key_success_factors(diagnosis: Any) -> List[str]:
    """Identify key factors that contributed to successful treatment."""
    factors = []

    # High confidence diagnosis
    if diagnosis.confidence_score and diagnosis.confidence_score > 0.8:
        factors.append("High confidence diagnosis")

    # Specific issue identification
    if diagnosis.identified_issues:
        issue_count = sum(len(issues) for issues in diagnosis.identified_issues.values())
        if issue_count <= 3:  # Not too many issues
            factors.append("Focused issue identification")

    # Clear action plan
    if diagnosis.recommended_actions:
        action_count = sum(len(actions) for actions in diagnosis.recommended_actions.values())
        if action_count > 0:
            factors.append("Clear action plan provided")

    # User engagement (if they provided feedback)
    if diagnosis.user_feedback_rating:
        factors.append("User engagement and feedback")

    return factors


def calculate_diagnosis_frequency(diagnoses: List[Any]) -> Dict[str, Any]:
    """Calculate how frequently user requests diagnoses."""
    if not diagnoses or len(diagnoses) < 2:
        return {'frequency': 'insufficient_data'}

    # Sort by creation date
    sorted_diagnoses = sorted(diagnoses, key=lambda d: d.created_at)

    # Calculate intervals between diagnoses
    intervals = []
    for i in range(1, len(sorted_diagnoses)):
        prev_date = sorted_diagnoses[i - 1].created_at
        curr_date = sorted_diagnoses[i].created_at

        if prev_date and curr_date:
            interval_days = (curr_date - prev_date).days
            intervals.append(interval_days)

    if not intervals:
        return {'frequency': 'insufficient_data'}

    avg_interval = sum(intervals) / len(intervals)

    if avg_interval < 7:
        frequency = 'very_frequent'
    elif avg_interval < 30:
        frequency = 'frequent'
    elif avg_interval < 90:
        frequency = 'regular'
    else:
        frequency = 'occasional'

    return {
        'frequency': frequency,
        'average_days_between': avg_interval,
        'total_diagnoses': len(diagnoses),
        'date_range_days': (sorted_diagnoses[-1].created_at - sorted_diagnoses[0].created_at).days
    }


def format_rag_context_for_ai(rag_context: Dict[str, Any]) -> str:
    """
    Format RAG context into a text prompt for AI consumption.

    Args:
        rag_context: RAG context dictionary

    Returns:
        Formatted context string for AI prompt
    """
    context_parts = []

    # Add similar cases information
    similar_cases = rag_context.get('similar_cases', [])
    if similar_cases:
        context_parts.append("SIMILAR HISTORICAL CASES:")
        for i, case in enumerate(similar_cases[:3], 1):  # Top 3 cases
            similarity = case.get('similarity_score', 0) * 100
            summary = case.get('diagnosis_summary', 'No summary')
            outcome = case.get('treatment_outcome', 'Unknown')

            context_parts.append(f"{i}. (Similarity: {similarity:.1f}%) {summary} - Outcome: {outcome}")

    # Add successful treatments
    successful_treatments = rag_context.get('successful_treatments', [])
    if successful_treatments:
        context_parts.append("\nSUCCESSFUL TREATMENT PATTERNS:")
        for treatment in successful_treatments[:3]:
            treatments = treatment.get('successful_treatments', [])
            context_parts.append(f"• {'; '.join(treatments[:2])}")

    # Add user history patterns
    user_patterns = rag_context.get('user_history_patterns', {})
    if user_patterns.get('common_issues'):
        context_parts.append(f"\nUSER'S COMMON ISSUES: {list(user_patterns['common_issues'].keys())[:3]}")

    # Add plant-specific insights
    plant_insights = rag_context.get('plant_specific_insights', {})
    if plant_insights.get('care_tips'):
        context_parts.append(f"\nSPECIES-SPECIFIC TIPS: {'; '.join(plant_insights['care_tips'][:2])}")

    return '\n'.join(context_parts) if context_parts else "No relevant historical context available."

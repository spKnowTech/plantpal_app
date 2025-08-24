import base64
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from plant_pal_bot.ai_bot_client import ask_gpt4o


def extract_plant_issues_from_text(analysis_text: str) -> Dict[str, List[str]]:
    """
    Extract structured issues from analysis text using AI.

    Args:
        analysis_text: Raw analysis text from vision model

    Returns:
        Dictionary with categorized issues
    """
    extraction_prompt = f"""
    Extract and categorize plant health issues from the following analysis text. 
    Return a JSON object with these categories:
    - diseases: specific plant diseases mentioned
    - pests: insects or pest problems identified
    - deficiencies: nutrient or environmental deficiencies
    - environmental: environmental stress factors
    - symptoms: visible symptoms described

    Analysis text: {analysis_text}

    Return only valid JSON. If no issues in a category, use empty list.
    """
    system_prompt = "You are an expert plant pathologist. Extract plant health issues and return only valid JSON."
    try:
        response = ask_gpt4o(user_prompt=extraction_prompt, system_prompt=system_prompt)
        result = json.loads(response)

        # Validate structure
        expected_keys = ['immediate', 'short_term', 'long_term', 'monitoring']
        for key in expected_keys:
            if key not in result:
                result[key] = []
            elif not isinstance(result[key], list):
                result[key] = []

        return result

    except Exception as e:
        print(f"Error extracting recommended actions: {str(e)}")
        return {
            'immediate': [],
            'short_term': [],
            'long_term': [],
            'monitoring': []
        }


def extract_recommended_actions_from_text(analysis_text: str, issues: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Extract recommended actions from analysis text.

    Args:
        analysis_text: Raw analysis text from vision model
        issues: Identified issues for context

    Returns:
        Dictionary with categorized recommended actions
    """
    issues_text = json.dumps(issues, indent=2)

    extraction_prompt = f"""
    Based on the following plant analysis and identified issues, extract recommended actions.
    Return a JSON object with these categories:
    - immediate: actions to take right away
    - short_term: actions for next 1-2 weeks
    - long_term: actions for ongoing care
    - monitoring: what to watch for

    Analysis: {analysis_text}

    Identified Issues: {issues_text}

    Return only valid JSON with actionable recommendations.
    """
    system_prompt = "You are an expert plant care advisor. Provide practical, actionable recommendations in JSON format."
    try:
        response = ask_gpt4o(user_prompt=extraction_prompt, system_prompt=system_prompt)
        result = json.loads(response)

        # Validate structure
        expected_keys = ['diseases', 'pests', 'deficiencies', 'environmental', 'symptoms']
        for key in expected_keys:
            if key not in result:
                result[key] = []
            elif not isinstance(result[key], list):
                result[key] = []

        return result

    except Exception as e:
        print(f"Error extracting plant issues: {str(e)}")
        return {
            'diseases': [],
            'pests': [],
            'deficiencies': [],
            'environmental': [],
            'symptoms': []
        }

def calculate_confidence_score(analysis_text: str, issues: Dict[str, List[str]]) -> float:
    """
    Calculate confidence score based on analysis specificity and clarity.

    Args:
        analysis_text: Raw analysis text
        issues: Identified issues

    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Base confidence factors
    confidence_factors = []

    # Factor 1: Length and detail of analysis
    text_length = len(analysis_text.split())
    if text_length > 100:
        confidence_factors.append(0.8)
    elif text_length > 50:
        confidence_factors.append(0.6)
    else:
        confidence_factors.append(0.4)

    # Factor 2: Number and specificity of issues identified
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    if total_issues == 0:
        confidence_factors.append(0.3)  # Low confidence if no issues found
    elif total_issues <= 2:
        confidence_factors.append(0.7)
    elif total_issues <= 5:
        confidence_factors.append(0.8)
    else:
        confidence_factors.append(0.6)  # Too many issues might indicate uncertainty

    # Factor 3: Presence of specific plant terms
    specific_terms = [
        'chlorosis', 'necrosis', 'aphid', 'scale', 'mite', 'fungal', 'bacterial',
        'overwatering', 'under watering', 'nitrogen', 'phosphorus', 'potassium',
        'root rot', 'leaf spot', 'powdery mildew', 'yellowing', 'browning'
    ]

    term_matches = sum(1 for term in specific_terms if term.lower() in analysis_text.lower())
    if term_matches >= 3:
        confidence_factors.append(0.9)
    elif term_matches >= 1:
        confidence_factors.append(0.7)
    else:
        confidence_factors.append(0.5)

    # Calculate average confidence
    avg_confidence = sum(confidence_factors) / len(confidence_factors)

    # Ensure confidence is within bounds
    return max(0.1, min(1.0, avg_confidence))


def analyze_plant_image_with_gpt4_vision(image_path: str, user_context: Optional[str] = None,
                                         plant_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze plant image using GPT-4 Vision API.

    Args:
        image_path: Path to the image file
        user_context: User's description of the issue
        plant_context: Context about the plant (species, location, etc.)

    Returns:
        Dictionary with analysis results
    """
    try:
        # Build context prompt
        context_parts = []
        if user_context:
            context_parts.append(f"User's concern: {user_context}")

        if plant_context:
            if plant_context.get('species'):
                context_parts.append(f"Plant species: {plant_context['species']}")
            if plant_context.get('location'):
                context_parts.append(f"Location: {plant_context['location']}")
            if plant_context.get('current_issues'):
                context_parts.append(f"Known issues: {plant_context['current_issues']}")

        context_text = "\n".join(context_parts) if context_parts else "No additional context provided."

        # Create analysis prompt
        analysis_prompt = f"""
        Analyze this plant image for health issues and provide a detailed diagnosis.

        Context:
        {context_text}

        Please provide:
        1. Overall plant health assessment
        2. Specific issues identified (diseases, pests, deficiencies, environmental stress)
        3. Detailed description of symptoms visible in the image
        4. Likely causes of any problems
        5. Recommended immediate and long-term treatments
        6. Prevention strategies
        7. Prognosis and recovery timeline

        Be specific and practical in your recommendations. If you're uncertain about something, mention it.
        """

        # Call GPT-4 Vision API
        analysis_text = ask_gpt4o(user_prompt=analysis_prompt, image_path=image_path)

        # Extract structured information from analysis
        identified_issues = extract_plant_issues_from_text(analysis_text)
        recommended_actions = extract_recommended_actions_from_text(analysis_text, identified_issues)
        confidence_score = calculate_confidence_score(analysis_text, identified_issues)
        return {
            'analysis_text': analysis_text,
            'identified_issues': identified_issues,
            'recommended_actions': recommended_actions,
            'confidence_score': confidence_score,
            'model_used': 'gpt-4-vision-preview',
            'analysis_timestamp': None  # Will be set by caller
        }

    except Exception as e:
        raise Exception(f"Vision analysis failed: {str(e)}")


def generate_diagnosis_summary(analysis_result: Dict[str, Any], user_context: Optional[str] = None) -> str:
    """
    Generate a user-friendly diagnosis summary from analysis results.

    Args:
        analysis_result: Result from vision analysis
        user_context: Original user context/concern

    Returns:
        Formatted diagnosis summary for chat display
    """
    summary_parts = []

    # Add user context acknowledgment
    if user_context:
        summary_parts.append(f"📸 **Photo Analysis** - Regarding your concern: \"{user_context}\"")
    else:
        summary_parts.append("📸 **Photo Analysis Results**")

    # Add confidence indicator
    confidence = analysis_result.get('confidence_score', 0.0)
    if confidence >= 0.8:
        confidence_emoji = "🎯"
        confidence_text = "High confidence"
    elif confidence >= 0.6:
        confidence_emoji = "✅"
        confidence_text = "Good confidence"
    elif confidence >= 0.4:
        confidence_emoji = "⚠️"
        confidence_text = "Moderate confidence"
    else:
        confidence_emoji = "❓"
        confidence_text = "Low confidence"

    summary_parts.append(f"{confidence_emoji} **Analysis Confidence:** {confidence_text} ({confidence:.1%})")

    # Add identified issues
    issues = analysis_result.get('identified_issues', {})
    if any(issues.values()):
        summary_parts.append("\n🔍 **Issues Identified:**")
        for category, issue_list in issues.items():
            if issue_list:
                category_name = category.replace('_', ' ').title()
                summary_parts.append(f"• **{category_name}:** {', '.join(issue_list)}")
    else:
        summary_parts.append("\n✅ **Good News:** No major issues detected in this image!")

    # Add immediate recommendations
    actions = analysis_result.get('recommended_actions', {})
    immediate_actions = actions.get('immediate', [])
    if immediate_actions:
        summary_parts.append(f"\n🚨 **Immediate Actions Needed:**")
        for i, action in enumerate(immediate_actions[:3], 1):  # Limit to top 3
            summary_parts.append(f"{i}. {action}")

    # Add main analysis excerpt (first paragraph or two)
    analysis_text = analysis_result.get('analysis_text', '')
    if analysis_text:
        # Extract first meaningful paragraph
        paragraphs = [p.strip() for p in analysis_text.split('\n') if p.strip()]
        if paragraphs:
            first_paragraph = paragraphs[0]
            if len(first_paragraph) > 200:
                first_paragraph = first_paragraph[:200] + "..."
            summary_parts.append(f"\n💭 **Analysis Summary:**\n{first_paragraph}")

    return '\n'.join(summary_parts)


def create_detailed_diagnosis_report(analysis_result: Dict[str, Any],
                                     plant_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a detailed diagnosis report for storage and future reference.

    Args:
        analysis_result: Result from vision analysis
        plant_context: Context about the plant

    Returns:
        Detailed formatted diagnosis report
    """
    report_parts = []

    # Header
    report_parts.append("=== PLANT HEALTH DIAGNOSIS REPORT ===")
    report_parts.append(f"Analysis Date: {analysis_result.get('analysis_timestamp', 'Not specified')}")
    report_parts.append(f"Model Used: {analysis_result.get('model_used', 'Unknown')}")
    report_parts.append(f"Confidence Score: {analysis_result.get('confidence_score', 0.0):.2%}")

    # Plant context
    if plant_context:
        report_parts.append("\n--- PLANT INFORMATION ---")
        if plant_context.get('species'):
            report_parts.append(f"Species: {plant_context['species']}")
        if plant_context.get('location'):
            report_parts.append(f"Location: {plant_context['location']}")
        if plant_context.get('name'):
            report_parts.append(f"Plant Name: {plant_context['name']}")

    # Issues identified
    issues = analysis_result.get('identified_issues', {})
    if any(issues.values()):
        report_parts.append("\n--- ISSUES IDENTIFIED ---")
        for category, issue_list in issues.items():
            if issue_list:
                category_name = category.replace('_', ' ').title()
                report_parts.append(f"\n{category_name}:")
                for issue in issue_list:
                    report_parts.append(f"  • {issue}")

    # Recommended actions
    actions = analysis_result.get('recommended_actions', {})
    if any(actions.values()):
        report_parts.append("\n--- RECOMMENDED ACTIONS ---")
        for category, action_list in actions.items():
            if action_list:
                category_name = category.replace('_', ' ').title()
                report_parts.append(f"\n{category_name}:")
                for action in action_list:
                    report_parts.append(f"  • {action}")

    # Full analysis
    analysis_text = analysis_result.get('analysis_text', '')
    if analysis_text:
        report_parts.append("\n--- DETAILED ANALYSIS ---")
        report_parts.append(analysis_text)

    report_parts.append("\n=== END OF REPORT ===")

    return '\n'.join(report_parts)


def validate_image_for_analysis(image_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate image file before analysis.

    Args:
        image_path: Path to image file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if file exists
        if not Path(image_path).exists():
            return False, "Image file not found"

        # Check file size (max 20MB for Vision API)
        file_size = Path(image_path).stat().st_size
        if file_size > 20 * 1024 * 1024:  # 20MB
            return False, "Image file too large for analysis"

        # Check if it's a valid image by trying to encode it
        try:
            with open(image_path, "rb") as f:
                base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return False, "Invalid or corrupted image file"

        return True, None

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def get_analysis_cost_estimate(image_path: str) -> Dict[str, Any]:
    """
    Estimate the cost of analyzing an image.

    Args:
        image_path: Path to image file

    Returns:
        Dictionary with cost estimation details
    """
    try:
        file_size = Path(image_path).stat().st_size

        # Rough cost estimation (based on OpenAI pricing)
        # These are approximate values and should be updated based on current pricing
        base_cost = 0.01  # Base cost per image
        size_factor = file_size / (1024 * 1024)  # MB
        estimated_cost = base_cost + (size_factor * 0.005)

        return {
            'estimated_cost_usd': round(estimated_cost, 4),
            'file_size_mb': round(size_factor, 2),
            'base_cost': base_cost,
            'size_cost': round(size_factor * 0.005, 4)
        }

    except Exception:
        return {
            'estimated_cost_usd': 0.01,
            'file_size_mb': 0.0,
            'base_cost': 0.01,
            'size_cost': 0.0
        }

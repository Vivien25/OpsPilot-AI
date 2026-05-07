import re
from services.gemini.vision_service import analyze_image
from services.mongodb.incident_repository import save_incident, find_similar_incidents


def extract_issue_type(vision_summary: str) -> str:
    text = vision_summary.lower()

    if "aisle" in text or "obstruction" in text or "blocked" in text:
        return "blocked_aisle"
    if "damaged" in text or "broken" in text:
        return "damaged_package"
    if "spill" in text or "leak" in text:
        return "spill_or_leak"
    if "safety" in text or "hazard" in text:
        return "safety_hazard"

    return "general_incident"


def extract_severity(vision_summary: str) -> str:
    if not vision_summary:
        return "unknown"

    text = vision_summary.lower()

    if "severity" not in text:
        return "unknown"

    severity_section = text.split("severity", 1)[1][:100]

    if "high" in severity_section:
        return "high"
    if "medium" in severity_section:
        return "medium"
    if "low" in severity_section:
        return "low"

    return "unknown"


def run_investigation(image_bytes: bytes, mime_type: str):
    vision_summary = analyze_image(image_bytes, mime_type)

    issue_type = extract_issue_type(vision_summary)
    severity = extract_severity(vision_summary)

    similar_incidents = find_similar_incidents(issue_type)

    recommendation = (
        "Review the detected issue, compare it with similar historical incidents, "
        "and assign the appropriate operator to resolve it."
    )

    incident = {
        "issue_type": issue_type,
        "severity": severity,
        "vision_summary": vision_summary,
        "similar_incidents_found": len(similar_incidents),
        "recommendation": recommendation,
    }

    incident_id = save_incident(incident)

    return {
        "incident_id": incident_id,
        "issue_type": issue_type,
        "severity": severity,
        "vision_summary": vision_summary,
        "similar_incidents": similar_incidents,
        "recommendation": recommendation,
    }
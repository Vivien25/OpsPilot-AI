def classify_issue(vision_summary: str) -> dict:
    """
    Classification Agent:
    Converts the vision summary into issue type and severity.
    For now, this is deterministic. Later we can replace this with Gemini JSON.
    """
    text = (vision_summary or "").lower()

    if "aisle" in text or "obstruction" in text or "blocked" in text:
        issue_type = "blocked_aisle"
    elif "damaged" in text or "broken" in text:
        issue_type = "damaged_package"
    elif "spill" in text or "leak" in text:
        issue_type = "spill_or_leak"
    elif "safety" in text or "hazard" in text:
        issue_type = "safety_hazard"
    else:
        issue_type = "general_incident"

    severity = "unknown"
    if "high" in text:
        severity = "high"
    elif "medium" in text:
        severity = "medium"
    elif "low" in text:
        severity = "low"

    return {
        "issue_type": issue_type,
        "severity": severity,
    }
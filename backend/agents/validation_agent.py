def validate_incident_report(report: dict) -> dict:
    """
    Validation Agent:
    Checks whether the final incident report is complete and reliable.
    """

    missing_fields = []

    required_fields = [
        "issue_type",
        "severity",
        "vision_summary",
        "recommendation",
    ]

    for field in required_fields:
        if not report.get(field):
            missing_fields.append(field)

    is_valid = len(missing_fields) == 0

    return {
        "is_valid": is_valid,
        "missing_fields": missing_fields,
        "validation_summary": (
            "Incident report is complete."
            if is_valid
            else f"Incident report is missing: {', '.join(missing_fields)}"
        ),
    }
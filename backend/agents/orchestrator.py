from uuid import uuid4

from agents.vision_agent import run_vision_agent
from agents.classification_agent import classify_issue
from agents.memory_agent import run_memory_agent
from agents.recommendation_agent import generate_recommendation
from agents.validation_agent import validate_incident_report
from services.bigquery_service import save_analysis_result
from services.rag_service import find_item, find_similar_incidents, find_contact_by_zone
from services.storage.gcs_service import upload_incident_image


def analyze_wrong_zone(vision_result: dict):
    item_id = vision_result.get("item_id") or vision_result.get("detected_item")
    detected_zone = vision_result.get("detected_zone")

    item = find_item(item_id)

    if not item:
        return {
            "detected_item": item_id,
            "item_id": item_id,
            "detected_zone": detected_zone,
            "expected_zone": None,
            "is_wrong_zone": None,
            "similar_incidents": [],
            "responsible_contact": None,
            "responsible_person": None,
            "risk": "Item master data was not found in MongoDB.",
            "reason": "The item could not be matched to operational knowledge.",
            "recommendation": "Please verify the item label manually."
        }

    expected_zone = item["expected_zone"]
    is_wrong_zone = (
        detected_zone.lower() != expected_zone.lower()
        if detected_zone
        else None
    )

    incidents = find_similar_incidents(item_id)
    contact = find_contact_by_zone(expected_zone)

    return {
        "item_id": item_id,
        "detected_item": item_id,
        "item_name": item.get("item_name") or item.get("label"),
        "item_description": item.get("description"),
        "detected_zone": detected_zone,
        "expected_zone": expected_zone,
        "is_wrong_zone": is_wrong_zone,
        "risk_level": item["risk_level"],
        "handling_rules": item.get("handling_rules", []),
        "similar_incidents": incidents,
        "responsible_contact": contact,
        "responsible_person": contact.get("name") if contact else None,
        "reason": (
            f"{item_id} was detected in {detected_zone}, but item master data says it belongs in {expected_zone}."
            if detected_zone
            else f"{item_id} belongs in {expected_zone}, but no detected zone was returned."
        ),
        "risk": (
            f"This item is {item.get('risk_level', 'unknown').lower()} risk. "
            f"{item.get('description', '')}"
        ),
        "recommendation": (
            f"Move {item_id} to {expected_zone} and notify "
            f"{contact['name']}." if is_wrong_zone and contact
            else "No wrong-zone issue detected."
        )
    }


def run_investigation(image_bytes: bytes, mime_type: str) -> dict:
    """
    Orchestrator:
    Coordinates all agents and returns the final incident report.
    """
    incident_id = str(uuid4())
    image_uri = upload_incident_image(
        image_bytes=image_bytes,
        mime_type=mime_type,
        incident_id=incident_id,
    )

    vision_result = run_vision_agent(
        image_bytes=image_bytes,
        mime_type=mime_type,
    )
    vision_summary = vision_result.get("vision_summary", "")
    wrong_zone_result = analyze_wrong_zone(vision_result)

    classification = classify_issue(vision_summary)
    issue_type = classification["issue_type"]
    severity = classification["severity"]

    similar_incidents = run_memory_agent(issue_type)
    item_incidents = wrong_zone_result.get("similar_incidents") or similar_incidents

    recommendation_result = generate_recommendation(
    issue_type=issue_type,
    severity=severity,
    vision_summary=vision_summary,
    similar_incidents=item_incidents,
 )

    incident = {
    "incident_id": incident_id,
    "image_uri": image_uri,
    "issue_type": issue_type,
    "severity": severity,
    "vision_summary": vision_summary,
    "visible_label": vision_result.get("visible_label"),
    "item_type": vision_result.get("item_type"),
    "visual_evidence": vision_result.get("visual_evidence"),
    "vision_confidence": vision_result.get("vision_confidence"),
    "item_id": wrong_zone_result.get("item_id"),
    "detected_item": wrong_zone_result.get("detected_item"),
    "item_name": wrong_zone_result.get("item_name"),
    "detected_zone": wrong_zone_result.get("detected_zone"),
    "expected_zone": wrong_zone_result.get("expected_zone"),
    "is_wrong_zone": wrong_zone_result.get("is_wrong_zone"),
    "reason": wrong_zone_result.get("reason"),
    "risk": wrong_zone_result.get("risk"),
    "risk_level": wrong_zone_result.get("risk_level"),
    "similar_incidents_found": len(item_incidents),
    "responsible_contact": wrong_zone_result.get("responsible_contact"),
    "responsible_person": wrong_zone_result.get("responsible_person"),
    "root_cause": recommendation_result["root_cause"],
    "recommendation": wrong_zone_result.get("recommendation") or recommendation_result["recommended_action"],
    "confidence": recommendation_result["confidence"],
    "action_steps": recommendation_result["action_steps"],
    "risk_notes": recommendation_result["risk_notes"],
}

    validation = validate_incident_report(incident)

    incident["validation"] = validation

    save_analysis_result(incident)

    return {
    "incident_id": incident_id,
    "image_gcs_uri": image_uri,
    "issue_type": issue_type,
    "severity": severity,
    "vision_summary": vision_summary,
    "visible_label": incident["visible_label"],
    "item_type": incident["item_type"],
    "visual_evidence": incident["visual_evidence"],
    "vision_confidence": incident["vision_confidence"],
    "item_id": incident["item_id"],
    "detected_item": incident["detected_item"],
    "item_name": incident["item_name"],
    "detected_zone": incident["detected_zone"],
    "expected_zone": incident["expected_zone"],
    "is_wrong_zone": incident["is_wrong_zone"],
    "reason": incident["reason"],
    "risk": incident["risk"],
    "risk_level": incident["risk_level"],
    "similar_incidents": item_incidents,
    "responsible_contact": incident["responsible_contact"],
    "responsible_person": incident["responsible_person"],
    "root_cause": incident["root_cause"],
    "recommendation": incident["recommendation"],
    "confidence": incident["confidence"],
    "action_steps": incident["action_steps"],
    "risk_notes": incident["risk_notes"],
    "validation": validation,
    "agent_trace": [
        "Vision Agent analyzed the image",
        "Classification Agent identified issue type and severity",
        "Memory Agent retrieved similar historical incidents",
        "Recommendation Agent generated AI next action",
        "Validation Agent checked report completeness",
    ],
}

from uuid import uuid4

from services.gemini.vision_service import analyze_damage_image
from services.rag_service import find_contact_by_item_type, find_contact_by_zone, find_item, find_sop
from services.storage.gcs_service import upload_incident_image


ITEM_TYPE_BY_PREFIX = {
    "CHEM": "Hazardous Chemical",
    "FG": "Finished Product",
    "RAW": "Production Material",
    "PKG": "Packaging Supply",
    "MRO": "Maintenance Spare Part",
}


def _infer_item_type(item_id: str | None) -> str | None:
    if not item_id or "-" not in item_id:
        return None
    return ITEM_TYPE_BY_PREFIX.get(item_id.split("-", 1)[0].upper())


def run_incident_ticket(image_bytes: bytes, mime_type: str) -> dict:
    ticket_id = str(uuid4())
    image_uri = upload_incident_image(
        image_bytes=image_bytes,
        mime_type=mime_type,
        incident_id=ticket_id,
    )
    vision_result = analyze_damage_image(image_bytes=image_bytes, mime_type=mime_type)

    item_id = vision_result.get("item_id")
    item = find_item(item_id)
    item_type = (
        vision_result.get("item_type")
        or (item.get("item_type") if item else None)
        or _infer_item_type(item_id)
        or "Unknown"
    )
    item_name = (item.get("item_name") or item.get("label")) if item else None
    expected_zone = item.get("expected_zone") if item else None
    sop = find_sop(item_type, "damaged_item")
    contact = find_contact_by_item_type(item_type) or find_contact_by_zone(expected_zone)
    severity = vision_result.get("severity") or item.get("risk_level") if item else vision_result.get("severity")
    severity = severity or "Unknown"

    if sop:
        sop_steps = sop.get("steps", [])
        sop_title = sop.get("title")
    else:
        sop_steps = [
            "Stop handling the damaged item.",
            "Isolate the item from active inventory.",
            "Photograph the label, damage, and storage location.",
            "Notify the responsible supervisor.",
            "Create and submit an incident report.",
        ]
        sop_title = "General Damaged Item Handling SOP"

    if contact:
        next_action = f"Follow {sop_title} and notify {contact['name']}, {contact['position']}."
    else:
        next_action = f"Follow {sop_title} and notify the responsible supervisor."

    damage_summary = vision_result.get("damage_summary") or (
        f"Damage detected for {item_id or 'an unidentified item'}."
    )

    return {
        "ticket_id": ticket_id,
        "image_gcs_uri": image_uri,
        "issue_type": "damaged_item",
        "damage_summary": damage_summary,
        "item_id": item_id,
        "item_name": item_name,
        "item_type": item_type,
        "damage_type": vision_result.get("damage_type"),
        "severity": severity,
        "visible_label": vision_result.get("visible_label"),
        "vision_confidence": vision_result.get("vision_confidence"),
        "expected_zone": expected_zone,
        "sop": sop,
        "sop_title": sop_title,
        "sop_steps": sop_steps,
        "responsible_contact": contact,
        "responsible_person": contact.get("name") if contact else None,
        "recommendation": next_action,
        "next_action": next_action,
        "needs_manual_review": not bool(item_id and sop),
        "missing_observations": [
            label
            for label, value in {
                "item_id": item_id,
                "sop": sop,
            }.items()
            if not value
        ],
        "agent_trace": [
            "Gemini Vision detected item and damage signals",
            "OpsPilot retrieved item information",
            "OpsPilot retrieved the matching SOP document",
            "OpsPilot retrieved the responsible contact",
            "Incident Ticket Agent generated next action",
        ],
    }

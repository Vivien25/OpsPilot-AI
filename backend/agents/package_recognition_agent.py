from uuid import uuid4

from services.bigquery_service import fetch_box_master
from services.gemini.vision_service import analyze_package_image
from services.rag_service import find_contact_by_zone
from services.storage.gcs_service import upload_incident_image


FALLBACK_BOXES = [
    {
        "box_id": "BOX-CHEM-102",
        "item_id": "CHEM-102",
        "item_name": "Solvent Drum Kit",
        "box_description": "Boxed solvent drum kit for chemical storage.",
        "expected_zone": "Chemical Storage",
        "expected_rack": "A03",
        "length_cm": 60.0,
        "width_cm": 40.0,
        "height_cm": 40.0,
        "weight_kg": 18.5,
        "color": "blue",
        "package_type": "drum box",
        "visual_description": "blue chemical box with hazard sticker",
        "sample_image_gcs_uri": "gs://opspilot-box-samples/chem-102.jpg",
        "responsible_contact_id": "C-101",
        "risk_level": "High",
        "last_updated": "2026-05-08T10:00:00Z",
    }
]


def _tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    return {
        token.strip(".,:;()[]{}").lower()
        for token in text.split()
        if len(token.strip(".,:;()[]{}")) > 2
    }


def _find_by_label(boxes: list[dict], box_id: str | None, item_id: str | None) -> dict | None:
    for box in boxes:
        if box_id and box.get("box_id", "").lower() == box_id.lower():
            return box
        if item_id and box.get("item_id", "").lower() == item_id.lower():
            return box
    return None


def _best_visual_matches(boxes: list[dict], vision_result: dict, limit: int = 3) -> list[dict]:
    observed_tokens = _tokenize(
        " ".join(
            str(value)
            for value in [
                vision_result.get("color"),
                vision_result.get("package_type"),
                vision_result.get("visual_description"),
            ]
            if value
        )
    )

    scored = []
    for box in boxes:
        box_tokens = _tokenize(
            " ".join(
                str(value)
                for value in [
                    box.get("color"),
                    box.get("package_type"),
                    box.get("visual_description"),
                    box.get("box_description"),
                ]
                if value
            )
        )
        overlap = len(observed_tokens & box_tokens)
        if overlap:
            scored.append((overlap, box))

    return [box for _, box in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]


def run_package_recognition(image_bytes: bytes, mime_type: str) -> dict:
    recognition_id = str(uuid4())
    image_uri = upload_incident_image(
        image_bytes=image_bytes,
        mime_type=mime_type,
        incident_id=recognition_id,
    )
    vision_result = analyze_package_image(image_bytes=image_bytes, mime_type=mime_type)
    boxes = fetch_box_master(100) or FALLBACK_BOXES

    matched_box = _find_by_label(boxes, vision_result.get("box_id"), vision_result.get("item_id"))
    match_source = "visible_label" if matched_box else "visual_similarity"
    visual_matches = [] if matched_box else _best_visual_matches(boxes, vision_result)

    if not matched_box and visual_matches:
        matched_box = visual_matches[0]

    contact = find_contact_by_zone(matched_box.get("expected_zone")) if matched_box else None
    expected_zone = matched_box.get("expected_zone") if matched_box else None
    expected_rack = matched_box.get("expected_rack") if matched_box else None
    risk_level = matched_box.get("risk_level") if matched_box else "Unknown"
    item_name = matched_box.get("item_name") if matched_box else None
    box_id = matched_box.get("box_id") if matched_box else vision_result.get("box_id")
    item_id = matched_box.get("item_id") if matched_box else vision_result.get("item_id")

    if matched_box:
        recommendation = (
            f"Route {box_id or item_id} to {expected_zone}, rack {expected_rack}. "
            f"Notify {contact['name']}." if contact else f"Route {box_id or item_id} to {expected_zone}, rack {expected_rack}."
        )
    else:
        recommendation = "No package match found. Retake the photo with the box label visible or manually enter the box ID."

    return {
        "recognition_id": recognition_id,
        "image_gcs_uri": image_uri,
        "issue_type": "Package Recognition",
        "severity": risk_level,
        "vision_summary": vision_result.get("vision_summary"),
        "box_id": box_id,
        "item_id": item_id,
        "item_name": item_name,
        "detected_item": item_id or box_id,
        "visible_label": vision_result.get("visible_label"),
        "label_found": vision_result.get("label_found"),
        "color": vision_result.get("color"),
        "package_type": vision_result.get("package_type"),
        "visual_description": vision_result.get("visual_description"),
        "expected_zone": expected_zone,
        "expected_rack": expected_rack,
        "detected_zone": None,
        "is_wrong_zone": None,
        "risk_level": risk_level,
        "responsible_contact": contact,
        "responsible_person": contact.get("name") if contact else None,
        "similar_incidents": visual_matches,
        "match_source": match_source,
        "matched_box": matched_box,
        "recommendation": recommendation,
        "confidence": vision_result.get("vision_confidence"),
        "needs_manual_review": not bool(matched_box),
        "missing_observations": [] if matched_box else ["box_id or readable visual match"],
        "action_steps": [
            "Check the visible package label",
            "Match against box master",
            "Route package to expected zone and rack",
        ],
        "risk_notes": matched_box.get("box_description") if matched_box else "Package could not be matched confidently.",
        "agent_trace": [
            "Gemini Vision checked the package label",
            "Box Master lookup matched by label or visual features",
            "Zone and contact context were retrieved",
            "Package Recognition Agent generated routing recommendation",
        ],
    }

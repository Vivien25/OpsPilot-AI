import json
import re

from observability.tracing import set_span_attributes, start_span
from services.gemini.gemini_client import client, MODEL


def _extract_json(text: str) -> dict:
    if not text:
        return {}

    cleaned = text.strip()
    cleaned = re.sub(r"^```json", "", cleaned)
    cleaned = re.sub(r"^```", "", cleaned)
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}

    return {}

def analyze_image(image_bytes: bytes, mime_type: str) -> dict:
    prompt = """
You are an industrial operations vision extractor.

Extract only observable facts from this warehouse image.
Do not decide whether the placement is correct.
Do not recommend an action.
Do not infer policy from outside the image.

Return ONLY valid JSON in this exact shape:

{
  "item_id": "item id such as CHEM-102, or null",
  "detected_zone": "visible warehouse zone sign such as Finished Goods, or null",
  "visible_label": "visible label text, or null",
  "item_type": "brief visible item type, or null",
  "visual_evidence": "one sentence describing the visual evidence",
  "confidence": 0.0
}
"""

    try:
        with start_span(
            "gemini_vision_agent",
            {
                "llm.model_name": MODEL,
                "input.mime_type": mime_type,
                "input.image_bytes": len(image_bytes),
                "input.value": prompt,
            },
        ) as span:
            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_bytes,
                                }
                            },
                        ],
                    }
                ],
            )
            set_span_attributes(span, {"output.value": response.text or ""})
        text = response.text or ""
        data = _extract_json(text)

        if data:
            visual_evidence = data.get("visual_evidence") or "No visual evidence returned."
            set_span_attributes(
                span,
                {
                    "vision.item_id": data.get("item_id") or data.get("detected_item"),
                    "vision.detected_zone": data.get("detected_zone"),
                    "vision.confidence": data.get("confidence"),
                },
            )
            return {
                "vision_summary": visual_evidence,
                "item_id": data.get("item_id") or data.get("detected_item"),
                "detected_item": data.get("item_id") or data.get("detected_item"),
                "detected_zone": data.get("detected_zone"),
                "visible_label": data.get("visible_label"),
                "item_type": data.get("item_type"),
                "visual_evidence": visual_evidence,
                "vision_confidence": data.get("confidence"),
            }

        return {
            "vision_summary": text or "No vision summary returned.",
            "item_id": None,
            "detected_item": None,
            "detected_zone": None,
            "visible_label": None,
            "item_type": None,
            "visual_evidence": text or "No visual evidence returned.",
            "vision_confidence": None,
        }

    except Exception as e:
        print("Gemini Vision error:", e)
        return {
            "vision_summary": (
                "Gemini Vision is temporarily unavailable due to high demand. "
                "Please retry the upload in a moment."
            ),
            "item_id": None,
            "detected_item": None,
            "detected_zone": None,
            "visible_label": None,
            "item_type": None,
            "visual_evidence": None,
            "vision_confidence": None,
        }


def analyze_package_image(image_bytes: bytes, mime_type: str) -> dict:
    prompt = """
You are an industrial package recognition vision extractor.

Extract only observable facts from this box or package photo.
Do not decide whether the package is in the right place.
Do not recommend an action.

If a label is visible, extract box_id and item_id exactly as written.
If no label is visible, describe visual features that can be used for lookup.

Return ONLY valid JSON in this exact shape:

{
  "box_id": "box id such as BOX-CHEM-102, or null",
  "item_id": "item id such as CHEM-102, or null",
  "visible_label": "visible label text, or null",
  "label_found": true,
  "color": "main package color, or null",
  "package_type": "box, carton, crate, drum box, parts bin, or null",
  "visual_description": "one sentence describing visual features",
  "confidence": 0.0
}
"""

    try:
        with start_span(
            "gemini_package_vision_agent",
            {
                "llm.model_name": MODEL,
                "input.mime_type": mime_type,
                "input.image_bytes": len(image_bytes),
                "input.value": prompt,
            },
        ) as span:
            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_bytes,
                                }
                            },
                        ],
                    }
                ],
            )
            set_span_attributes(span, {"output.value": response.text or ""})
        text = response.text or ""
        data = _extract_json(text)

        if data:
            set_span_attributes(
                span,
                {
                    "vision.box_id": data.get("box_id"),
                    "vision.item_id": data.get("item_id"),
                    "vision.label_found": bool(data.get("label_found") or data.get("box_id") or data.get("item_id")),
                    "vision.confidence": data.get("confidence"),
                },
            )
            return {
                "vision_summary": data.get("visual_description") or "No visual description returned.",
                "box_id": data.get("box_id"),
                "item_id": data.get("item_id"),
                "visible_label": data.get("visible_label"),
                "label_found": bool(data.get("label_found") or data.get("box_id") or data.get("item_id")),
                "color": data.get("color"),
                "package_type": data.get("package_type"),
                "visual_description": data.get("visual_description"),
                "vision_confidence": data.get("confidence"),
            }

        return {
            "vision_summary": text or "No vision summary returned.",
            "box_id": None,
            "item_id": None,
            "visible_label": None,
            "label_found": False,
            "color": None,
            "package_type": None,
            "visual_description": text or "No visual description returned.",
            "vision_confidence": None,
        }

    except Exception as e:
        print("Gemini Package Vision error:", e)
        return {
            "vision_summary": "Gemini Vision is temporarily unavailable. Please retry the upload in a moment.",
            "box_id": None,
            "item_id": None,
            "visible_label": None,
            "label_found": False,
            "color": None,
            "package_type": None,
            "visual_description": None,
            "vision_confidence": None,
        }


def compare_package_to_reference(
    uploaded_image_bytes: bytes,
    uploaded_mime_type: str,
    reference_image_bytes: bytes,
    reference_mime_type: str,
    reference_item: dict,
) -> dict:
    prompt = f"""
You are an industrial package validation agent.

Compare the uploaded package photo with the reference product image and item-master data.
Use the uploaded image as the inspected shipment item.
Use the reference image and item-master fields as the expected product.

Item-master data:
- item_id: {reference_item.get("item_id")}
- item_name: {reference_item.get("item_name")}
- package_type: {reference_item.get("package_type")}
- expected_zone: {reference_item.get("expected_zone")}
- dimensions_cm: {reference_item.get("length_cm")} x {reference_item.get("width_cm")} x {reference_item.get("height_cm")}
- visual_description: {reference_item.get("visual_description")}

Return ONLY valid JSON in this exact shape:

{{
  "label_match": true,
  "package_match": true,
  "condition_ok": true,
  "visual_match_score": 0.0,
  "detected_label": "label text visible in uploaded image, or null",
  "detected_package_type": "package type visible in uploaded image, or null",
  "condition_summary": "brief condition summary",
  "comparison_summary": "brief explanation of match or mismatch",
  "confidence": 0.0
}}
"""

    try:
        with start_span(
            "gcs_reference_image_comparison",
            {
                "llm.model_name": MODEL,
                "reference.item_id": reference_item.get("item_id"),
                "reference.image_bytes": len(reference_image_bytes),
                "uploaded.image_bytes": len(uploaded_image_bytes),
                "input.value": prompt,
            },
        ) as span:
            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": uploaded_mime_type,
                                    "data": uploaded_image_bytes,
                                }
                            },
                            {
                                "inline_data": {
                                    "mime_type": reference_mime_type,
                                    "data": reference_image_bytes,
                                }
                            },
                        ],
                    }
                ],
            )
            set_span_attributes(span, {"output.value": response.text or ""})

        data = _extract_json(response.text or "")
        if data:
            set_span_attributes(
                span,
                {
                    "comparison.label_match": bool(data.get("label_match")),
                    "comparison.package_match": bool(data.get("package_match")),
                    "comparison.condition_ok": bool(data.get("condition_ok")),
                    "comparison.visual_match_score": data.get("visual_match_score"),
                    "comparison.confidence": data.get("confidence"),
                },
            )
            return data

        return {
            "label_match": False,
            "package_match": False,
            "condition_ok": False,
            "visual_match_score": 0,
            "detected_label": None,
            "detected_package_type": None,
            "condition_summary": "Reference comparison did not return structured output.",
            "comparison_summary": response.text or "No comparison output returned.",
            "confidence": 0,
        }
    except Exception as e:
        print("Gemini reference comparison error:", e)
        return {
            "label_match": False,
            "package_match": False,
            "condition_ok": False,
            "visual_match_score": 0,
            "detected_label": None,
            "detected_package_type": None,
            "condition_summary": "Reference comparison unavailable.",
            "comparison_summary": f"Reference comparison unavailable: {e}",
            "confidence": 0,
        }


def analyze_damage_image(image_bytes: bytes, mime_type: str) -> dict:
    prompt = """
You are an industrial damage ticket vision extractor.

Extract only observable facts from the damaged warehouse item photo.
Do not recommend an action.

Return ONLY valid JSON in this exact shape:

{
  "item_id": "item id such as CHEM-102, or null",
  "item_type": "Hazardous Chemical, Finished Product, Production Material, Packaging Supply, Maintenance Spare Part, or null",
  "damage_type": "leakage, crushed package, puncture, wet packaging, broken seal, corrosion, missing component, or brief observed damage",
  "severity": "High, Medium, Low, or Unknown",
  "visible_label": "visible label text, or null",
  "damage_summary": "one sentence describing what is damaged and visible evidence",
  "confidence": 0.0
}
"""

    try:
        with start_span(
            "gemini_damage_vision_agent",
            {
                "llm.model_name": MODEL,
                "input.mime_type": mime_type,
                "input.image_bytes": len(image_bytes),
                "input.value": prompt,
            },
        ) as span:
            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_bytes,
                                }
                            },
                        ],
                    }
                ],
            )
            set_span_attributes(span, {"output.value": response.text or ""})
        text = response.text or ""
        data = _extract_json(text)

        if data:
            set_span_attributes(
                span,
                {
                    "vision.item_id": data.get("item_id"),
                    "vision.item_type": data.get("item_type"),
                    "vision.damage_type": data.get("damage_type"),
                    "vision.severity": data.get("severity") or "Unknown",
                    "vision.confidence": data.get("confidence"),
                },
            )
            return {
                "vision_summary": data.get("damage_summary") or "No damage summary returned.",
                "item_id": data.get("item_id"),
                "item_type": data.get("item_type"),
                "damage_type": data.get("damage_type"),
                "severity": data.get("severity") or "Unknown",
                "visible_label": data.get("visible_label"),
                "damage_summary": data.get("damage_summary"),
                "vision_confidence": data.get("confidence"),
            }

        return {
            "vision_summary": text or "No vision summary returned.",
            "item_id": None,
            "item_type": None,
            "damage_type": None,
            "severity": "Unknown",
            "visible_label": None,
            "damage_summary": text or "No damage summary returned.",
            "vision_confidence": None,
        }

    except Exception as e:
        print("Gemini Damage Vision error:", e)
        return {
            "vision_summary": "Gemini Vision is temporarily unavailable. Please retry the upload in a moment.",
            "item_id": None,
            "item_type": None,
            "damage_type": None,
            "severity": "Unknown",
            "visible_label": None,
            "damage_summary": None,
            "vision_confidence": None,
        }

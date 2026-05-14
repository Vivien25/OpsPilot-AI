import json
import re

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
        text = response.text or ""
        data = _extract_json(text)

        if data:
            visual_evidence = data.get("visual_evidence") or "No visual evidence returned."
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
        text = response.text or ""
        data = _extract_json(text)

        if data:
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

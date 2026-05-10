import json
import re

from services.gemini.gemini_client import client, MODEL


def _extract_json(text: str) -> dict:
    """
    Safely extract JSON from Gemini response text.
    Handles cases where the model wraps JSON in markdown.
    """
    if not text:
        return {}

    text = text.strip()

    # Remove markdown fences if present
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}

    return {}


def generate_recommendation(
    issue_type: str,
    severity: str,
    vision_summary: str,
    similar_incidents: list,
) -> dict:
    """
    Recommendation Agent:
    Uses Gemini to generate root cause, recommendation, confidence, and action steps.
    """

    prompt = f"""
You are an industrial operations incident response expert.

Based on the image analysis and historical incidents, generate a practical incident response recommendation.

Issue type:
{issue_type}

Severity:
{severity}

Vision summary:
{vision_summary}

Similar historical incidents:
{similar_incidents}

Return ONLY valid JSON in this exact format:

{{
  "root_cause": "short likely root cause",
  "recommended_action": "clear practical next action",
  "confidence": 0.85,
  "action_steps": [
    "step 1",
    "step 2",
    "step 3"
  ],
  "risk_notes": "short safety or operations note"
}}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        data = _extract_json(response.text or "")

        return {
            "root_cause": data.get(
                "root_cause",
                "Potential operational process gap or incomplete staging workflow.",
            ),
            "recommended_action": data.get(
                "recommended_action",
                "Review the detected issue, compare it with similar historical incidents, and assign the appropriate operator to resolve it.",
            ),
            "confidence": data.get("confidence", 0.7),
            "action_steps": data.get(
                "action_steps",
                [
                    "Review detected issue",
                    "Compare historical cases",
                    "Assign operator remediation",
                ],
            ),
            "risk_notes": data.get(
                "risk_notes",
                "Confirm the area is safe before returning to normal operations.",
            ),
        }

    except Exception as e:
        print("Recommendation Agent error:", e)

        return {
            "root_cause": "Potential operational process gap or incomplete staging workflow.",
            "recommended_action": "Review the detected issue, compare it with similar historical incidents, and assign the appropriate operator to resolve it.",
            "confidence": 0.5,
            "action_steps": [
                "Review detected issue",
                "Compare historical cases",
                "Assign operator remediation",
            ],
            "risk_notes": "Recommendation agent fallback used. Please review manually.",
        }
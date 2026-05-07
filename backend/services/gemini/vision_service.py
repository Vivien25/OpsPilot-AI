from services.gemini.gemini_client import client, MODEL

def analyze_image(image_bytes: bytes, mime_type: str) -> str:
    prompt = """
You are an industrial operations AI assistant.

Analyze this image and identify:
1. What is visible
2. Any operational issue, defect, safety risk, or abnormal condition
3. Severity: low, medium, or high
4. Possible root cause
5. Recommended next action

Return a concise operational summary.
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
        return response.text or "No vision summary returned."

    except Exception as e:
        print("Gemini Vision error:", e)
        return (
            "Gemini Vision is temporarily unavailable due to high demand. "
            "Please retry the upload in a moment."
        )
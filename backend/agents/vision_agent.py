from services.gemini.vision_service import analyze_image


def run_vision_agent(image_bytes: bytes, mime_type: str) -> dict:
    """
    Vision Agent:
    Reads the uploaded image and produces an operational summary.
    """
    return analyze_image(image_bytes=image_bytes, mime_type=mime_type)

from datetime import datetime, timezone
from uuid import uuid4

from utils.config import GCP_PROJECT_ID, GCS_BUCKET_NAME, USE_GCS


def _storage_client():
    if not USE_GCS or not GCS_BUCKET_NAME:
        return None

    try:
        from google.cloud import storage
    except ImportError:
        return None

    return storage.Client(project=GCP_PROJECT_ID)


def upload_incident_image(image_bytes: bytes, mime_type: str, incident_id: str | None = None) -> str | None:
    """
    Store the raw incident image in GCS and return its gs:// URI.
    Falls back to None when GCS is not configured so local development still works.
    """
    client = _storage_client()
    if not client:
        return None

    safe_incident_id = incident_id or str(uuid4())
    extension = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }.get(mime_type, "bin")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    blob_name = f"raw-images/{timestamp}-{safe_incident_id}.{extension}"

    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    return f"gs://{GCS_BUCKET_NAME}/{blob_name}"

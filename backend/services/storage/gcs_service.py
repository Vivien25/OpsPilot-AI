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


def download_gcs_image(gcs_uri: str) -> tuple[bytes, str] | None:
    client = _storage_client()
    if not client or not gcs_uri or not gcs_uri.startswith("gs://"):
        return None

    path = gcs_uri.removeprefix("gs://")
    bucket_name, _, blob_name = path.partition("/")
    if not bucket_name or not blob_name:
        return None

    try:
        blob = client.bucket(bucket_name).blob(blob_name)
        image_bytes = blob.download_as_bytes()
        mime_type = blob.content_type or _mime_type_from_name(blob_name)
        return image_bytes, mime_type
    except Exception as exc:
        print(f"GCS image download skipped for {gcs_uri}: {exc}")
        return None


def _mime_type_from_name(name: str) -> str:
    lowered = name.lower()
    if lowered.endswith(".jpg") or lowered.endswith(".jpeg"):
        return "image/jpeg"
    if lowered.endswith(".webp"):
        return "image/webp"
    return "image/png"

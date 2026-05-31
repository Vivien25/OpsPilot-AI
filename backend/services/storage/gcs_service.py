from datetime import datetime, timezone
import re
from uuid import uuid4

from utils.config import GCP_PROJECT_ID, GCS_BUCKET_NAME, PRODUCT_IMAGE_GCS_BUCKET, USE_GCS


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
    extension = _extension_from_mime_type(mime_type)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    blob_name = f"raw-images/{timestamp}-{safe_incident_id}.{extension}"

    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    return f"gs://{GCS_BUCKET_NAME}/{blob_name}"


def upload_daily_product_image(
    image_bytes: bytes,
    mime_type: str,
    shipment_id: str | None = None,
    item_id: str | None = None,
    original_filename: str | None = None,
) -> str | None:
    """
    Store worker-uploaded product intake images under a daily folder.
    Example:
    gs://bucket/daily-product-images/2026-05-30/20260530T200501Z-SHIP-B-1500-FG-220.jpg
    """
    client = _storage_client()
    if not client or not PRODUCT_IMAGE_GCS_BUCKET:
        return None

    now = datetime.now(timezone.utc)
    day = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    safe_shipment = _safe_path_part(shipment_id or "unknown-shipment")
    safe_item = _safe_path_part(item_id or "unknown-item")
    extension = _extension_from_mime_type(mime_type, original_filename)
    blob_name = f"daily-product-images/{day}/{timestamp}-{safe_shipment}-{safe_item}.{extension}"

    bucket = client.bucket(PRODUCT_IMAGE_GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.metadata = {
        "shipment_id": shipment_id or "",
        "item_id": item_id or "",
        "original_filename": original_filename or "",
        "uploaded_for": "product_recognition",
    }
    blob.upload_from_string(image_bytes, content_type=mime_type)

    return f"gs://{PRODUCT_IMAGE_GCS_BUCKET}/{blob_name}"


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


def _extension_from_mime_type(mime_type: str, filename: str | None = None) -> str:
    extension = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }.get(mime_type)
    if extension:
        return extension

    if filename:
        lowered = filename.lower()
        if lowered.endswith((".jpg", ".jpeg")):
            return "jpg"
        if lowered.endswith(".png"):
            return "png"
        if lowered.endswith(".webp"):
            return "webp"

    return "bin"


def _safe_path_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-")
    return cleaned or "unknown"

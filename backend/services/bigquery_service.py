from datetime import datetime, timezone
from uuid import uuid4

from utils.config import (
    BIGQUERY_ANALYSIS_RESULTS_TABLE,
    BIGQUERY_DATASET,
    GCP_PROJECT_ID,
    USE_BIGQUERY_ANALYTICS,
)


def _bigquery_client():
    if not USE_BIGQUERY_ANALYTICS:
        return None

    try:
        from google.cloud import bigquery
    except ImportError:
        return None

    return bigquery.Client(project=GCP_PROJECT_ID)


def _table(table_name: str) -> str:
    return f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{table_name}"


def save_analysis_result(report: dict) -> str:
    """
    Persist the final agent result for analytics/dashboard history.
    MongoDB remains the operational knowledge source.
    """
    analysis_id = report.get("analysis_id") or report.get("incident_id") or str(uuid4())
    timestamp = report.get("timestamp") or datetime.now(timezone.utc).isoformat()

    client = _bigquery_client()
    if not client:
        return analysis_id

    row = {
        "analysis_id": analysis_id,
        "timestamp": timestamp,
        "image_gcs_uri": report.get("image_gcs_uri") or report.get("image_uri"),
        "item_id": report.get("item_id") or report.get("detected_item"),
        "detected_zone": report.get("detected_zone"),
        "expected_zone": report.get("expected_zone"),
        "issue_type": report.get("issue_type"),
        "severity": report.get("severity"),
        "recommendation": report.get("recommendation"),
        "contact_name": report.get("contact_name") or report.get("responsible_person"),
        "confidence": report.get("vision_confidence") or report.get("confidence"),
    }

    errors = client.insert_rows_json(_table(BIGQUERY_ANALYSIS_RESULTS_TABLE), [row])
    if errors:
        raise RuntimeError(f"BigQuery analytics insert failed: {errors}")

    return analysis_id

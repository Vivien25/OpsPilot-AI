from datetime import datetime, timezone
from uuid import uuid4

from utils.config import (
    BIGQUERY_ANALYSIS_RESULTS_TABLE,
    BIGQUERY_BOX_MASTER_TABLE,
    BIGQUERY_DATASET,
    BIGQUERY_INVENTORY_MAP_TABLE,
    BIGQUERY_ORCHESTRATION_RUNS_TABLE,
    BIGQUERY_RACK_MASTER_TABLE,
    BIGQUERY_WAREHOUSE_STATUS_TABLE,
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


def save_orchestration_run(run: dict) -> str:
    """
    Persist Cloud Scheduler-triggered orchestration runs for audit/history.
    This gives the midnight automation a durable side effect beyond returning JSON.
    """
    run_id = run.get("run_id") or str(uuid4())
    timestamp = run.get("generated_at") or datetime.now(timezone.utc).isoformat()

    client = _bigquery_client()
    if not client:
        return run_id

    validation = run.get("validation") or {}
    metrics = run.get("metrics") or {}
    incidents = run.get("incidents") or []

    row = {
        "run_id": run_id,
        "timestamp": timestamp,
        "trigger_source": run.get("trigger_source") or "manual",
        "system_status": run.get("system_status"),
        "shipments_today": metrics.get("shipments_today"),
        "agents_active": metrics.get("agents_active"),
        "map_records": metrics.get("map_records"),
        "open_incidents": metrics.get("open_incidents"),
        "validation_status": validation.get("status"),
        "missing_item_count": len(validation.get("missing_items") or []),
        "wrong_zone_count": len(validation.get("wrong_zone_items") or []),
        "incident_count": len(incidents),
    }

    errors = client.insert_rows_json(_table(BIGQUERY_ORCHESTRATION_RUNS_TABLE), [row])
    if errors:
        raise RuntimeError(f"BigQuery orchestration run insert failed: {errors}")

    return run_id


def fetch_inventory_map(limit: int = 100) -> list[dict]:
    """
    Read the warehouse inventory map used by the frontend warehouse map.
    BigQuery is analytics storage, so callers should tolerate an empty result.
    """
    client = _bigquery_client()
    if not client:
        return []

    safe_limit = max(1, min(int(limit), 500))
    query = f"""
        SELECT
            item_id,
            item_name,
            item_type,
            zone,
            rack,
            bin_location,
            quantity,
            shipment_id,
            status,
            risk_level,
            CAST(last_updated AS STRING) AS last_updated
        FROM `{_table(BIGQUERY_INVENTORY_MAP_TABLE)}`
        ORDER BY zone, rack, bin_location
        LIMIT {safe_limit}
    """

    try:
        return [dict(row) for row in client.query(query).result()]
    except Exception as exc:
        print(f"BigQuery inventory map read skipped: {exc}")
        return []


def fetch_rack_master(limit: int = 200) -> list[dict]:
    """
    Read the physical rack layout table. Occupancy is calculated by map_agent
    against inventory_map so this stays a stable rack master.
    """
    client = _bigquery_client()
    if not client:
        return []

    safe_limit = max(1, min(int(limit), 1000))
    query = f"""
        SELECT
            rack_id,
            zone,
            aisle,
            rack_label,
            x_position,
            y_position,
            capacity_slots,
            allowed_item_types,
            risk_zone,
            is_active,
            CAST(last_updated AS STRING) AS last_updated
        FROM `{_table(BIGQUERY_RACK_MASTER_TABLE)}`
        ORDER BY zone, aisle, rack_label
        LIMIT {safe_limit}
    """

    try:
        return [dict(row) for row in client.query(query).result()]
    except Exception as exc:
        print(f"BigQuery rack master read skipped: {exc}")
        return []


def fetch_box_master(limit: int = 100) -> list[dict]:
    client = _bigquery_client()
    if not client:
        return []

    safe_limit = max(1, min(int(limit), 500))
    query = f"""
        SELECT
            box_id,
            item_id,
            item_name,
            box_description,
            expected_zone,
            expected_rack,
            length_cm,
            width_cm,
            height_cm,
            weight_kg,
            package_type,
            visual_description,
            sample_image_gcs_uri,
            responsible_contact_id,
            risk_level,
            CAST(last_updated AS STRING) AS last_updated
        FROM `{_table(BIGQUERY_BOX_MASTER_TABLE)}`
        ORDER BY box_id
        LIMIT {safe_limit}
    """

    try:
        return [dict(row) for row in client.query(query).result()]
    except Exception as exc:
        print(f"BigQuery box master read skipped: {exc}")
        return []


def fetch_warehouse_status(limit: int = 50) -> list[dict]:
    client = _bigquery_client()
    if not client:
        return []

    safe_limit = max(1, min(int(limit), 200))
    query = f"""
        SELECT
            shipment_id,
            shipment_name,
            arrival_time,
            status,
            expected_zone,
            expected_items,
            map_refresh_required,
            last_checked
        FROM `{_table(BIGQUERY_WAREHOUSE_STATUS_TABLE)}`
        ORDER BY arrival_time
        LIMIT {safe_limit}
    """

    try:
        return [dict(row) for row in client.query(query).result()]
    except Exception as exc:
        print(f"BigQuery warehouse status read skipped: {exc}")
        return []

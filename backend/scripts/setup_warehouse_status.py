from datetime import datetime, timezone
from pathlib import Path
import sys

from google.cloud import bigquery

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.config import BIGQUERY_DATASET, GCP_PROJECT_ID


TABLE_NAME = "warehouse_status"


def build_rows() -> list[dict]:
    today = datetime.now(timezone.utc).date().isoformat()
    return [
        {
            "shipment_id": "SHIP-A-0800",
            "shipment_name": "Shipment A",
            "arrival_time": f"{today}T08:00:00Z",
            "status": "arriving_today",
            "expected_zone": "Chemical Storage",
            "expected_items": ["CHEM-102", "CHEM-130", "CHEM-145"],
            "map_refresh_required": True,
            "last_checked": f"{today}T01:00:00Z",
        },
        {
            "shipment_id": "SHIP-B-1500",
            "shipment_name": "Shipment B",
            "arrival_time": f"{today}T15:00:00Z",
            "status": "arriving_today",
            "expected_zone": "Finished Goods",
            "expected_items": ["FG-220", "FG-141", "FG-156"],
            "map_refresh_required": True,
            "last_checked": f"{today}T01:00:00Z",
        },
    ]


def main():
    client = bigquery.Client(project=GCP_PROJECT_ID)
    dataset_id = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}"
    table_id = f"{dataset_id}.{TABLE_NAME}"

    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)

    schema = [
        bigquery.SchemaField("shipment_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("shipment_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("arrival_time", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("expected_zone", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("expected_items", "STRING", mode="REPEATED"),
        bigquery.SchemaField("map_refresh_required", "BOOLEAN", mode="REQUIRED"),
        bigquery.SchemaField("last_checked", "TIMESTAMP", mode="REQUIRED"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    client.delete_table(table_id, not_found_ok=True)
    client.create_table(table)

    rows = build_rows()
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    print(f"Ready: {table_id} with {len(rows)} warehouse status records")


if __name__ == "__main__":
    main()

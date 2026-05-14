from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from google.cloud import bigquery

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.config import BIGQUERY_DATASET, GCP_PROJECT_ID


TABLE_NAME = "rack_master"

ZONE_CONFIG = [
    ("Receiving", "REC", ["Raw Material", "Packaging", "Finished Goods"], "Medium"),
    ("Raw Materials", "RAW", ["Raw Material"], "Medium"),
    ("Chemical Storage", "CHEM", ["Chemical"], "High"),
    ("Packaging", "PKG", ["Packaging"], "Low"),
    ("Production", "PROD", ["Raw Material", "Packaging"], "Medium"),
    ("Finished Goods", "FG", ["Finished Goods"], "Low"),
    ("Shipping", "SHIP", ["Finished Goods"], "Low"),
    ("Maintenance", "MRO", ["Maintenance Part"], "Medium"),
]


def build_rows() -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc).replace(microsecond=0)

    for zone_index, (zone, prefix, allowed_types, risk_zone) in enumerate(ZONE_CONFIG):
        for rack_index in range(1, 13):
            aisle_number = (rack_index - 1) // 4 + 1
            rack_letter = chr(ord("A") + zone_index)
            rack_number = rack_index + zone_index
            rack_id = f"{rack_letter}{rack_number:02d}"

            rows.append(
                {
                    "rack_id": rack_id,
                    "zone": zone,
                    "aisle": f"{prefix}-{aisle_number}",
                    "rack_label": f"{zone[:3].upper()} Rack {rack_index:02d}",
                    "x_position": zone_index * 120 + (rack_index % 4) * 24,
                    "y_position": aisle_number * 90 + zone_index * 12,
                    "capacity_slots": 8 + (rack_index % 5) * 2,
                    "allowed_item_types": allowed_types,
                    "risk_zone": risk_zone,
                    "is_active": rack_index != 12,
                    "last_updated": (now - timedelta(hours=rack_index + zone_index)).isoformat(),
                }
            )

    rows[2].update(
        {
            "rack_id": "A03",
            "zone": "Chemical Storage",
            "aisle": "CHEM-1",
            "rack_label": "Chemical Rack A03",
            "x_position": 538,
            "y_position": 96,
            "capacity_slots": 16,
            "allowed_item_types": ["Chemical"],
            "risk_zone": "High",
            "is_active": True,
        }
    )
    rows[21].update(
        {
            "rack_id": "B12",
            "zone": "Finished Goods",
            "aisle": "FG-3",
            "rack_label": "Finished Goods Rack B12",
            "x_position": 488,
            "y_position": 318,
            "capacity_slots": 24,
            "allowed_item_types": ["Finished Goods"],
            "risk_zone": "Low",
            "is_active": True,
        }
    )

    return rows


def main():
    client = bigquery.Client(project=GCP_PROJECT_ID)
    dataset_id = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}"
    table_id = f"{dataset_id}.{TABLE_NAME}"

    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)

    schema = [
        bigquery.SchemaField("rack_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("zone", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("aisle", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("rack_label", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("x_position", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("y_position", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("capacity_slots", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("allowed_item_types", "STRING", mode="REPEATED"),
        bigquery.SchemaField("risk_zone", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED"),
        bigquery.SchemaField("last_updated", "TIMESTAMP", mode="REQUIRED"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    client.delete_table(table_id, not_found_ok=True)
    client.create_table(table)

    rows = build_rows()
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    print(f"Ready: {table_id} with {len(rows)} rack records")


if __name__ == "__main__":
    main()

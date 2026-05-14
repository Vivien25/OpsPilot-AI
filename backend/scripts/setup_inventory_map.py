from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from google.cloud import bigquery

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.config import BIGQUERY_DATASET, GCP_PROJECT_ID


TABLE_NAME = "inventory_map"

ITEM_TYPES = [
    ("CHEM", "Hazardous Chemical", "Chemical Storage", "High", "active"),
    ("FG", "Finished Product", "Finished Goods", "Low", "ready_to_ship"),
    ("RAW", "Production Material", "Raw Materials", "Medium", "active"),
    ("PKG", "Packaging Supply", "Packaging", "Low", "active"),
    ("MRO", "Maintenance Spare Part", "Maintenance", "Medium", "reserved"),
]

ITEM_NAMES = {
    "CHEM": ["Solvent Drum", "Cleaning Acid Tote", "Lubricant Barrel", "Resin Container"],
    "FG": ["Product Box", "Retail Case", "Finished Pallet", "Outbound Carton"],
    "RAW": ["Steel Coil", "Plastic Pellet Bag", "Fabric Roll", "Component Crate"],
    "PKG": ["Label Roll", "Mailer Box", "Shrink Wrap Case", "Pallet Sleeve"],
    "MRO": ["Pump Seal Kit", "Conveyor Belt", "Motor Assembly", "Valve Pack"],
}


def build_rows(count: int = 100) -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc).replace(microsecond=0)

    for index in range(count):
        prefix, item_type, zone, risk_level, status = ITEM_TYPES[index % len(ITEM_TYPES)]
        item_number = 100 + index
        rack_letter = chr(ord("A") + (index % 8))
        rack_number = (index % 18) + 1
        shelf = chr(ord("A") + (index % 4))
        bin_number = (index % 6) + 1
        shipment_prefix = "OUT" if prefix == "FG" else "IN"

        rows.append(
            {
                "item_id": f"{prefix}-{item_number}",
                "item_name": ITEM_NAMES[prefix][index % len(ITEM_NAMES[prefix])],
                "item_type": item_type,
                "zone": zone,
                "rack": f"{rack_letter}{rack_number:02d}",
                "bin_location": f"{rack_letter}{rack_number:02d}-{shelf}{bin_number}",
                "quantity": (index * 7) % 96 + 4,
                "shipment_id": f"{shipment_prefix}-{7700 + index}",
                "status": status,
                "risk_level": risk_level,
                "last_updated": (now - timedelta(hours=index * 3)).isoformat(),
            }
        )

    rows[2].update(
        {
            "item_id": "CHEM-102",
            "item_name": "Solvent Drum",
            "item_type": "Hazardous Chemical",
            "zone": "Chemical Storage",
            "rack": "A03",
            "bin_location": "A03-B2",
            "quantity": 12,
            "shipment_id": "IN-7782",
            "status": "active",
            "risk_level": "High",
        }
    )
    rows[20].update(
        {
            "item_id": "FG-220",
            "item_name": "Product Box",
            "item_type": "Finished Product",
            "zone": "Finished Goods",
            "rack": "B12",
            "bin_location": "B12-C1",
            "quantity": 40,
            "shipment_id": "OUT-5521",
            "status": "ready_to_ship",
            "risk_level": "Low",
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
        bigquery.SchemaField("item_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("item_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("item_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("zone", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("rack", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("bin_location", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("quantity", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("shipment_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("risk_level", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("last_updated", "TIMESTAMP", mode="REQUIRED"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    client.delete_table(table_id, not_found_ok=True)
    client.create_table(table)

    errors = client.insert_rows_json(table_id, build_rows())
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    print(f"Ready: {table_id} with 100 sample records")


if __name__ == "__main__":
    main()

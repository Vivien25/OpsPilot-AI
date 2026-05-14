from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from google.cloud import bigquery

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.config import BIGQUERY_DATASET, GCP_PROJECT_ID


TABLE_NAME = "box_master"

BOX_TYPES = [
    {
        "prefix": "CHEM",
        "item_type": "Hazardous Chemical",
        "zone": "Chemical Storage",
        "rack": "A03",
        "color": "blue",
        "package_type": "drum box",
        "risk": "High",
        "contact": "C-101",
        "description": "blue chemical box with hazard sticker",
    },
    {
        "prefix": "FG",
        "item_type": "Finished Product",
        "zone": "Finished Goods",
        "rack": "B12",
        "color": "white",
        "package_type": "shipping carton",
        "risk": "Low",
        "contact": "C-202",
        "description": "white finished goods carton with outbound label",
    },
    {
        "prefix": "RAW",
        "item_type": "Production Material",
        "zone": "Raw Materials",
        "rack": "C06",
        "color": "brown",
        "package_type": "bulk material crate",
        "risk": "Medium",
        "contact": "C-303",
        "description": "brown raw material crate with supplier label",
    },
    {
        "prefix": "PKG",
        "item_type": "Packaging Supply",
        "zone": "Packaging",
        "rack": "D09",
        "color": "tan",
        "package_type": "supply case",
        "risk": "Low",
        "contact": "C-404",
        "description": "tan packaging supply case with roll labels",
    },
    {
        "prefix": "MRO",
        "item_type": "Maintenance Spare Part",
        "zone": "Maintenance",
        "rack": "E04",
        "color": "gray",
        "package_type": "parts bin",
        "risk": "Medium",
        "contact": "C-505",
        "description": "gray maintenance parts bin with service tag",
    },
]

ITEM_NAMES = {
    "CHEM": ["Solvent Drum Kit", "Cleaning Acid Case", "Lubricant Pack", "Resin Safety Box"],
    "FG": ["Product Box", "Retail Case", "Finished Pallet Box", "Outbound Carton"],
    "RAW": ["Steel Coil Crate", "Plastic Pellet Tote", "Fabric Roll Case", "Component Crate"],
    "PKG": ["Label Roll Case", "Mailer Box Bundle", "Shrink Wrap Case", "Pallet Sleeve Pack"],
    "MRO": ["Pump Seal Kit", "Conveyor Belt Box", "Motor Assembly Crate", "Valve Pack"],
}


def build_rows(count: int = 60) -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc).replace(microsecond=0)

    for index in range(count):
        config = BOX_TYPES[index % len(BOX_TYPES)]
        prefix = config["prefix"]
        item_number = 100 + index
        base_size = 28 + (index % 8) * 4

        rows.append(
            {
                "box_id": f"BOX-{prefix}-{item_number}",
                "item_id": f"{prefix}-{item_number}",
                "item_name": ITEM_NAMES[prefix][index % len(ITEM_NAMES[prefix])],
                "box_description": f"{config['item_type']} package for warehouse handling.",
                "expected_zone": config["zone"],
                "expected_rack": config["rack"],
                "length_cm": float(base_size + 20),
                "width_cm": float(base_size + 8),
                "height_cm": float(base_size),
                "weight_kg": round(6.5 + (index % 9) * 2.4, 1),
                "color": config["color"],
                "package_type": config["package_type"],
                "visual_description": config["description"],
                "sample_image_gcs_uri": f"gs://opspilot-box-samples/{prefix.lower()}-{item_number}.jpg",
                "responsible_contact_id": config["contact"],
                "risk_level": config["risk"],
                "last_updated": (now - timedelta(hours=index * 2)).isoformat(),
            }
        )

    rows[2].update(
        {
            "box_id": "BOX-CHEM-102",
            "item_id": "CHEM-102",
            "item_name": "Solvent Drum Kit",
            "box_description": "Boxed solvent drum kit for chemical storage.",
            "expected_zone": "Chemical Storage",
            "expected_rack": "A03",
            "length_cm": 60.0,
            "width_cm": 40.0,
            "height_cm": 40.0,
            "weight_kg": 18.5,
            "color": "blue",
            "package_type": "drum box",
            "visual_description": "blue chemical box with hazard sticker",
            "sample_image_gcs_uri": "gs://opspilot-box-samples/chem-102.jpg",
            "responsible_contact_id": "C-101",
            "risk_level": "High",
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
        bigquery.SchemaField("box_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("item_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("item_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("box_description", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("expected_zone", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("expected_rack", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("length_cm", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("width_cm", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("height_cm", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("weight_kg", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("color", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("package_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("visual_description", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("sample_image_gcs_uri", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("responsible_contact_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("risk_level", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("last_updated", "TIMESTAMP", mode="REQUIRED"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    client.delete_table(table_id, not_found_ok=True)
    client.create_table(table)

    rows = build_rows()
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    print(f"Ready: {table_id} with {len(rows)} box records")


if __name__ == "__main__":
    main()

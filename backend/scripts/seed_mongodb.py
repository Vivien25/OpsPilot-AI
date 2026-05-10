from datetime import datetime, timezone
from pathlib import Path
import sys

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.mongodb.mongo_client import db

load_dotenv()


ITEMS = [
    {
        "item_id": "CHEM-102",
        "item_name": "Solvent Drum",
        "description": "Flammable solvent used for cleaning production equipment.",
        "expected_zone": "Chemical Storage",
        "risk_level": "High",
        "handling_rules": [
            "Store in Chemical Storage",
            "Keep away from heat",
            "Do not place near finished goods",
        ],
    },
    {
        "item_id": "FG-220",
        "item_name": "Finished Product Box",
        "description": "Packaged finished goods ready for outbound shipment.",
        "expected_zone": "Finished Goods",
        "risk_level": "Low",
        "handling_rules": [
            "Store in Finished Goods",
            "Keep pallet label visible",
            "Stage near outbound lane only after release",
        ],
    },
]

INCIDENTS = [
    {
        "incident_id": "INC-001",
        "item_id": "CHEM-102",
        "issue_type": "Wrong Zone",
        "detected_zone": "Finished Goods",
        "expected_zone": "Chemical Storage",
        "description": "Solvent drum was placed in Finished Goods zone.",
        "root_cause": "Forklift operator followed outdated staging instruction.",
        "recommended_action": "Move item to Chemical Storage and notify supervisor.",
        "created_at": datetime(2026, 5, 1, tzinfo=timezone.utc),
    },
]

CONTACTS = [
    {
        "contact_id": "C-101",
        "name": "John Smith",
        "zone": "Chemical Storage",
        "position": "Chemical Storage Supervisor",
        "email": "john.smith@example.com",
        "phone": "555-123-4567",
    },
    {
        "contact_id": "C-102",
        "name": "Amy Chen",
        "zone": "Finished Goods",
        "position": "Finished Goods Lead",
        "email": "amy.chen@example.com",
        "phone": "555-222-8888",
    },
]


def upsert_many(collection_name: str, key: str, rows: list[dict]):
    collection = db[collection_name]
    for row in rows:
        collection.update_one({key: row[key]}, {"$set": row}, upsert=True)


def main():
    upsert_many("items", "item_id", ITEMS)
    upsert_many("incidents", "incident_id", INCIDENTS)
    upsert_many("contacts", "contact_id", CONTACTS)
    db["items"].create_index("item_id", unique=True)
    db["incidents"].create_index([("item_id", 1), ("issue_type", 1)])
    db["contacts"].create_index("zone")
    print("Seeded MongoDB collections: items, incidents, contacts")


if __name__ == "__main__":
    main()

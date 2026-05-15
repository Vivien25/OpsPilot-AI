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
        "item_type": "Hazardous Chemical",
        "position": "Chemical Storage Supervisor",
        "email": "john.smith@example.com",
        "phone": "555-123-4567",
    },
    {
        "contact_id": "C-102",
        "name": "Amy Chen",
        "zone": "Finished Goods",
        "item_type": "Finished Product",
        "position": "Finished Goods Lead",
        "email": "amy.chen@example.com",
        "phone": "555-222-8888",
    },
]

SOPS = [
    {
        "sop_id": "SOP-CHEM-DAMAGE-001",
        "item_type": "Hazardous Chemical",
        "issue_type": "damaged_item",
        "title": "Hazardous Chemical Damage Handling SOP",
        "summary": "Steps for isolating, reporting, and escalating damaged chemical packages.",
        "gcs_uri": "gs://opspilot-sop-docs/sops/damaged-hazardous-chemical-package-handling-procedure.md",
        "steps": [
            "Do not move the item unless there is immediate danger.",
            "Isolate the area and keep workers away.",
            "Check for leakage or odor.",
            "Notify the Chemical Storage Supervisor.",
            "Create an incident report.",
        ],
        "contact_role": "Chemical Storage Supervisor",
    },
    {
        "sop_id": "SOP-FG-DAMAGE-001",
        "item_type": "Finished Product",
        "issue_type": "damaged_item",
        "title": "Finished Product Packaging Damage Handling SOP",
        "summary": "Steps for separating, inspecting, and holding damaged finished product packaging.",
        "gcs_uri": "gs://opspilot-sop-docs/sops/finished-product-packaging-damage-handling-procedure.md",
        "steps": [
            "Separate the affected inventory from shipment-ready material.",
            "Verify pallet stability before movement.",
            "Move the item to inspection or hold if safe.",
            "Photograph shipment labels and visible damage.",
            "Do not load damaged cartons until review is complete.",
        ],
        "contact_role": "Finished Goods Lead",
    },
    {
        "sop_id": "SOP-MRO-DAMAGE-001",
        "item_type": "Maintenance Spare Part",
        "issue_type": "damaged_item",
        "title": "Maintenance Spare Part Damage Handling SOP",
        "summary": "Steps for securing damaged spare parts and escalating to maintenance leadership.",
        "gcs_uri": "gs://opspilot-sop-docs/sops/maintenance-spare-part-damage-handling-procedure.md",
        "steps": [
            "Verify the part identification number.",
            "Place damaged parts in the maintenance hold location.",
            "Secure small components to prevent accidental reuse.",
            "Photograph part numbers, shelf location, and damage.",
            "Wait for maintenance lead approval before returning to inventory.",
        ],
        "contact_role": "Maintenance Lead",
    },
    {
        "sop_id": "SOP-PKG-DAMAGE-001",
        "item_type": "Packaging Supply",
        "issue_type": "damaged_item",
        "title": "Packaging Supply Damage Handling SOP",
        "summary": "Steps for removing damaged packaging supplies from active inventory.",
        "gcs_uri": "gs://opspilot-sop-docs/sops/packaging-supply-damage-handling-procedure.md",
        "steps": [
            "Inspect whether packaging remains suitable for shipment preparation.",
            "Remove compromised packaging materials from active inventory.",
            "Inspect nearby pallets and shelves for water exposure or impact.",
            "Document the damaged material and surrounding area.",
            "Do not use structurally weak packaging for outbound shipments.",
        ],
        "contact_role": "Packaging Lead",
    },
    {
        "sop_id": "SOP-RAW-DAMAGE-001",
        "item_type": "Production Material",
        "issue_type": "damaged_item",
        "title": "Production Material Damage Handling SOP",
        "summary": "Steps for holding damaged production material before quality inspection.",
        "gcs_uri": "gs://opspilot-sop-docs/sops/production-material-damage-handling-procedure.md",
        "steps": [
            "Separate the affected material from active production supply inventory.",
            "Verify material ID, lot number, and storage location.",
            "Inspect nearby inventory in the same rack or pallet group.",
            "Photograph damage, pallet condition, and rack location.",
            "Do not supply damaged material to production before quality inspection.",
        ],
        "contact_role": "Raw Materials Lead",
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
    upsert_many("sops", "sop_id", SOPS)
    db["items"].create_index("item_id", unique=True)
    db["incidents"].create_index([("item_id", 1), ("issue_type", 1)])
    db["contacts"].create_index("zone")
    db["contacts"].create_index("item_type")
    db["sops"].create_index([("item_type", 1), ("issue_type", 1)])
    print("Seeded MongoDB collections: items, incidents, contacts, sops")


if __name__ == "__main__":
    main()

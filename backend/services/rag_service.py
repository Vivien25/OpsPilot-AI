import json
from pathlib import Path

from services.mongodb.mongo_client import db

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_json(filename: str):
    with open(DATA_DIR / filename, "r") as f:
        return json.load(f)


ITEMS = load_json("items.json")
INCIDENTS = load_json("incidents.json")
CONTACTS = load_json("contacts.json")

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
]


def find_item(item_id: str):
    if not item_id:
        return None

    item = db["items"].find_one(
        {"item_id": {"$regex": f"^{item_id}$", "$options": "i"}},
        {"_id": 0},
    )
    if item:
        return item

    for item in ITEMS:
        if item["item_id"].lower() == item_id.lower():
            return item
    return None


def find_similar_incidents(item_id: str, issue_type: str = "Wrong Zone"):
    if not item_id:
        return []

    incidents = list(
        db["incidents"]
        .find(
            {
                "item_id": {"$regex": f"^{item_id}$", "$options": "i"},
                "issue_type": {"$regex": f"^{issue_type}$", "$options": "i"},
            },
            {"_id": 0},
        )
        .sort("created_at", -1)
        .limit(5)
    )
    if incidents:
        return incidents

    return [
        incident for incident in INCIDENTS
        if incident["item_id"].lower() == item_id.lower()
        and incident["issue_type"].lower() == issue_type.lower()
    ]


def find_contact_by_zone(zone: str):
    if not zone:
        return None

    contact = db["contacts"].find_one(
        {"zone": {"$regex": f"^{zone}$", "$options": "i"}},
        {"_id": 0},
    )
    if contact:
        return contact

    for contact in CONTACTS:
        if contact["zone"].lower() == zone.lower():
            return contact
    return None


def find_contact_by_item_type(item_type: str):
    if not item_type:
        return None

    contact = db["contacts"].find_one(
        {"item_type": {"$regex": f"^{item_type}$", "$options": "i"}},
        {"_id": 0},
    )
    if contact:
        return contact

    for contact in CONTACTS:
        if contact.get("item_type", "").lower() == item_type.lower():
            return contact
    return None


def find_sop(item_type: str, issue_type: str = "damaged_item"):
    if not item_type:
        return None

    sop = db["sops"].find_one(
        {
            "item_type": {"$regex": f"^{item_type}$", "$options": "i"},
            "issue_type": {"$regex": f"^{issue_type}$", "$options": "i"},
        },
        {"_id": 0},
    )
    if sop:
        return sop

    for sop in SOPS:
        if sop["item_type"].lower() == item_type.lower() and sop["issue_type"].lower() == issue_type.lower():
            return sop
    return None

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

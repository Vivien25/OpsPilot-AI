from datetime import datetime
from services.mongodb.mongo_client import db

collection = db["incidents"]

def save_incident(incident: dict) -> str:
    incident["created_at"] = datetime.utcnow()
    result = collection.insert_one(incident)
    return str(result.inserted_id)


def find_similar_incidents(issue_type: str, limit: int = 3):
    results = collection.find(
        {"issue_type": issue_type},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit)

    return list(results)
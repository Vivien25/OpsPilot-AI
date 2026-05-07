import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "opspilot_ai")

if not MONGODB_URI:
    raise RuntimeError("Missing MONGODB_URI in .env")

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
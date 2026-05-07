import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY or GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)
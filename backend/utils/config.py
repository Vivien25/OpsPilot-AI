import os

from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "opspilotai")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "opspilotai-incident-images")

BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "opspilot_ai")
BIGQUERY_ANALYSIS_RESULTS_TABLE = os.getenv("BIGQUERY_ANALYSIS_RESULTS_TABLE", "analysis_results")

USE_GCS = os.getenv("USE_GCS", "true").lower() == "true"
USE_BIGQUERY_ANALYTICS = os.getenv("USE_BIGQUERY_ANALYTICS", "true").lower() == "true"

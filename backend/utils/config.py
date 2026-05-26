import os

from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "opspilotai")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "opspilotai-incident-images")

BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "opspilot_ai")
BIGQUERY_ANALYSIS_RESULTS_TABLE = os.getenv("BIGQUERY_ANALYSIS_RESULTS_TABLE", "analysis_results")
BIGQUERY_INVENTORY_MAP_TABLE = os.getenv("BIGQUERY_INVENTORY_MAP_TABLE", "inventory_map")
BIGQUERY_RACK_MASTER_TABLE = os.getenv("BIGQUERY_RACK_MASTER_TABLE", "rack_master")
BIGQUERY_BOX_MASTER_TABLE = os.getenv("BIGQUERY_BOX_MASTER_TABLE", "box_master")
BIGQUERY_WAREHOUSE_STATUS_TABLE = os.getenv("BIGQUERY_WAREHOUSE_STATUS_TABLE", "warehouse_status")
BIGQUERY_ORCHESTRATION_RUNS_TABLE = os.getenv("BIGQUERY_ORCHESTRATION_RUNS_TABLE", "orchestration_runs")

USE_GCS = os.getenv("USE_GCS", "true").lower() == "true"
USE_BIGQUERY_ANALYTICS = os.getenv("USE_BIGQUERY_ANALYTICS", "true").lower() == "true"

ENABLE_ARIZE_AX = os.getenv("ENABLE_ARIZE_AX", "false").lower() == "true"
ARIZE_PROJECT_NAME = os.getenv("ARIZE_PROJECT_NAME", "opspilot-ai")
ARIZE_TRACE_HTTP_REQUESTS = os.getenv("ARIZE_TRACE_HTTP_REQUESTS", "false").lower() == "true"

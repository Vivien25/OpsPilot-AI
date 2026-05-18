from pathlib import Path
import sys

from google.cloud import bigquery

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.config import BIGQUERY_DATASET, BIGQUERY_ORCHESTRATION_RUNS_TABLE, GCP_PROJECT_ID


def main():
    client = bigquery.Client(project=GCP_PROJECT_ID)
    dataset_id = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}"
    table_id = f"{dataset_id}.{BIGQUERY_ORCHESTRATION_RUNS_TABLE}"

    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)

    schema = [
        bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("trigger_source", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("system_status", "STRING"),
        bigquery.SchemaField("shipments_today", "INTEGER"),
        bigquery.SchemaField("agents_active", "INTEGER"),
        bigquery.SchemaField("map_records", "INTEGER"),
        bigquery.SchemaField("open_incidents", "INTEGER"),
        bigquery.SchemaField("validation_status", "STRING"),
        bigquery.SchemaField("missing_item_count", "INTEGER"),
        bigquery.SchemaField("wrong_zone_count", "INTEGER"),
        bigquery.SchemaField("incident_count", "INTEGER"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table, exists_ok=True)
    print(f"Ready: {table_id}")


if __name__ == "__main__":
    main()

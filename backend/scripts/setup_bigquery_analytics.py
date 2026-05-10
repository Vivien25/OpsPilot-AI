from pathlib import Path
import sys

from google.cloud import bigquery

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.config import BIGQUERY_ANALYSIS_RESULTS_TABLE, BIGQUERY_DATASET, GCP_PROJECT_ID


def main():
    client = bigquery.Client(project=GCP_PROJECT_ID)
    dataset_id = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}"
    table_id = f"{dataset_id}.{BIGQUERY_ANALYSIS_RESULTS_TABLE}"

    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)

    schema = [
        bigquery.SchemaField("analysis_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("image_gcs_uri", "STRING"),
        bigquery.SchemaField("item_id", "STRING"),
        bigquery.SchemaField("detected_zone", "STRING"),
        bigquery.SchemaField("expected_zone", "STRING"),
        bigquery.SchemaField("issue_type", "STRING"),
        bigquery.SchemaField("severity", "STRING"),
        bigquery.SchemaField("recommendation", "STRING"),
        bigquery.SchemaField("contact_name", "STRING"),
        bigquery.SchemaField("confidence", "FLOAT"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table, exists_ok=True)
    print(f"Ready: {table_id}")


if __name__ == "__main__":
    main()

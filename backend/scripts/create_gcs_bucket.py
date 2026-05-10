from pathlib import Path
import sys

from google.cloud import storage

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.config import GCP_PROJECT_ID, GCS_BUCKET_NAME


def main():
    client = storage.Client(project=GCP_PROJECT_ID)
    existing = client.lookup_bucket(GCS_BUCKET_NAME)
    if existing:
        print(f"Ready: gs://{GCS_BUCKET_NAME}")
        return

    bucket = storage.Bucket(client, name=GCS_BUCKET_NAME)
    bucket.location = "US"
    client.create_bucket(bucket)
    print(f"Ready: gs://{GCS_BUCKET_NAME}")


if __name__ == "__main__":
    main()

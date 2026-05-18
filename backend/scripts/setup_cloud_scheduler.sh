#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-opspilotai}"
REGION="${REGION:-us-central1}"
JOB_NAME="${JOB_NAME:-opspilot-daily-warehouse-check}"
SERVICE_NAME="${SERVICE_NAME:-opspilot}"
TIME_ZONE="${TIME_ZONE:-America/Chicago}"
SCHEDULE="${SCHEDULE:-0 1 * * *}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-opspilot-scheduler}"

if [[ -z "${SERVICE_URL:-}" ]]; then
  SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --format='value(status.url)')"
fi

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud services enable cloudscheduler.googleapis.com run.googleapis.com iam.googleapis.com \
  --project="${PROJECT_ID}"

if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT_EMAIL}" \
  --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
    --project="${PROJECT_ID}" \
    --display-name="OpsPilot Cloud Scheduler caller"
fi

gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/run.invoker" >/dev/null

if gcloud scheduler jobs describe "${JOB_NAME}" \
  --project="${PROJECT_ID}" \
  --location="${REGION}" >/dev/null 2>&1; then
  gcloud scheduler jobs update http "${JOB_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --schedule="${SCHEDULE}" \
    --time-zone="${TIME_ZONE}" \
    --uri="${SERVICE_URL}/api/orchestration/daily-run" \
    --http-method=POST \
    --oidc-service-account-email="${SERVICE_ACCOUNT_EMAIL}" \
    --oidc-token-audience="${SERVICE_URL}"
else
  gcloud scheduler jobs create http "${JOB_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --schedule="${SCHEDULE}" \
    --time-zone="${TIME_ZONE}" \
    --uri="${SERVICE_URL}/api/orchestration/daily-run" \
    --http-method=POST \
    --oidc-service-account-email="${SERVICE_ACCOUNT_EMAIL}" \
    --oidc-token-audience="${SERVICE_URL}"
fi

echo "Ready: ${JOB_NAME} -> ${SERVICE_URL}/api/orchestration/daily-run at ${SCHEDULE} (${TIME_ZONE})"

# Vertex AI Agent Builder Setup

This folder contains the repo-side configuration for connecting OpsPilot AI to Vertex AI Agent Builder.

## What Is Included

- `openapi.yaml`: OpenAPI tool schema for the deployed OpsPilot FastAPI backend.
- `agent_builder.yaml`: Agent configuration notes, instructions, model choice, and tool list.

## Setup Flow

1. Deploy the backend to Cloud Run.
2. Replace `https://YOUR_CLOUD_RUN_SERVICE_URL` in `openapi.yaml` and `agent_builder.yaml` with the Cloud Run URL.
3. Open Vertex AI Agent Builder in Google Cloud.
4. Create a new agent named `OpsPilot AI Warehouse Operations Agent`.
5. Use the instructions from `agent_builder.yaml`.
6. Add tools from `openapi.yaml`.
7. Test these prompts:

```text
What shipments are arriving today, and which agents are active?
```

```text
Validate item FG-101 for Shipment B with label "FG-101 Retail Case FINISHED PRODUCT".
```

```text
Show me the current warehouse map status and open incidents.
```

## Required Backend Environment

The deployed backend should have:

```env
GOOGLE_API_KEY=your_gemini_key
GCP_PROJECT_ID=your_project
BIGQUERY_DATASET=warehouse_ops
GCS_BUCKET_NAME=your_reference_image_bucket
ENABLE_ARIZE_AX=true
ARIZE_SPACE_ID=your_arize_space_id
ARIZE_API_KEY=your_arize_api_key
```

## Notes

Agent Builder setup still requires Google Cloud console access and project permissions. This repository provides the deployable API and tool schemas needed for the configuration.

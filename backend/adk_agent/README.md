# OpsPilot ADK Agent

This package defines a Google Agent Development Kit (ADK) agent for OpsPilot AI.
The agent wraps the deployed OpsPilot Cloud Run backend as ADK function tools.

## Tools

- `check_opspilot_health`
- `get_daily_orchestration`
- `get_warehouse_map`
- `validate_product_intake`

## Local Run

From the repo root:

```bash
/usr/local/bin/python3.11 -m venv backend/adk_agent/.venv
source backend/adk_agent/.venv/bin/activate
python --version
pip install -r backend/adk_agent/requirements.txt

export OPSPILOT_API_BASE=https://opspilot-457509635383.us-central1.run.app
adk run backend/adk_agent
```

Try prompts such as:

```text
Check today's warehouse orchestration status.
```

```text
Validate product intake for item FG-101 in shipment IN-7782. The visible label is FG-101 Retail Case FINISHED PRODUCT, package type is shipping carton, condition is normal, and zone is Finished Goods.
```

## Deploy To Vertex AI Agent Engine

Authenticate first:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

Deploy from the repo root:

```bash
gcloud storage buckets create gs://YOUR_AGENT_STAGING_BUCKET \
  --location=us-central1

source backend/adk_agent/.venv/bin/activate
python -m backend.adk_agent.deploy_agent \
  --project YOUR_PROJECT_ID \
  --location us-central1 \
  --staging-bucket gs://YOUR_AGENT_STAGING_BUCKET \
  --api-base https://opspilot-457509635383.us-central1.run.app
```

After deployment, the agent should appear in Google Cloud under **Agents > Your deployed agents** or **Agents > Deployments**.

# OpsPilot AI

AI-powered warehouse operations nerve center for shipment validation, inventory mapping, incident detection, and autonomous operational workflows.

OpsPilot AI combines Gemini Vision, multi-agent orchestration, BigQuery analytics, GCS reference retrieval, and Arize observability to help warehouse and manufacturing teams detect operational issues before they become expensive incidents.

This project is built for the **Arize Track** of the Google Cloud Rapid Agent Hackathon. The repo includes a deployed Vertex AI Agent Engine agent, Vertex AI Agent Builder configuration assets, Arize AX tracing, Arize MCP configuration, and a stdio MCP server so OpsPilot can be exposed as agent-callable operational tools.

Deployed Agent Engine resource:

```text
projects/457509635383/locations/us-central1/reasoningEngines/7301050228281442304
```

## Why OpsPilot AI?

Modern warehouses still rely heavily on:

- manual shipment verification
- spreadsheet-based rack tracking
- delayed incident reporting
- human-dependent inventory validation
- disconnected operational systems

OpsPilot AI introduces an AI operations layer that continuously monitors:

- inbound shipments
- warehouse maps
- product intake photos
- rack placement consistency
- zone validation
- incident escalation workflows

The system autonomously coordinates specialized AI agents to:

- validate products using computer vision
- compare intake images against reference inventory
- detect wrong-zone placement
- generate operational investigations
- route incidents to the correct owner
- provide real-time operational traceability

## Key Features

### Multi-Agent Orchestration

OpsPilot AI uses a collaborative AI-agent architecture:

| Agent | Responsibility |
| --- | --- |
| Warehouse Status Agent | Detect inbound shipments |
| Orchestrator Agent | Assign workflows and coordinate agents |
| Map Agent | Refresh warehouse spatial inventory |
| Product Recognition Agent | Analyze shipment intake photos |
| Validation Agent | Compare detected product vs expected product |
| Misload Detection Agent | Detect wrong-zone inventory |
| Incident Agent | Generate operational tickets |
| Notification Agent | Route alerts to correct warehouse owners |

### Gemini Vision Product Validation

OpsPilot AI uses Google Gemini Vision to analyze shipment intake photos.

The system extracts:

- item IDs
- visible labels
- package types
- damage indicators
- detected warehouse zones
- visual evidence

The AI compares uploaded shipment photos against:

- BigQuery item-master records
- GCS reference product images
- expected warehouse locations

This enables:

- intake approval automation
- mislabeled product detection
- package mismatch detection
- damaged shipment escalation
- wrong-zone investigation

### Real-Time Warehouse Spatial Intelligence

OpsPilot AI visualizes:

- occupied racks
- available racks
- inactive racks
- expected zones
- detected zones
- shipment destinations

The AI continuously validates:

- whether products are stored correctly
- whether inbound inventory was mapped successfully
- whether warehouse maps match real operational conditions

### AI Investigation Workflows

When anomalies are detected, OpsPilot AI automatically:

- investigates the mismatch
- validates expected vs actual location
- evaluates incident severity
- creates operational trace logs
- routes incidents to responsible owners

This dramatically reduces:

- manual investigation time
- warehouse downtime
- inventory confusion
- operational delays

### Arize AI Observability

OpsPilot AI integrates with Arize AX for:

- AI agent tracing
- Gemini request monitoring
- workflow observability
- confidence tracking
- validation debugging
- operational transparency

Every agent decision can be traced across:

- orchestration runs
- validation workflows
- Gemini Vision outputs
- retrieval operations
- incident escalation paths

This provides production-grade AI observability for enterprise operations.

## Google Cloud Architecture

OpsPilot AI is built on Google Cloud technologies:

| Service | Purpose |
| --- | --- |
| Gemini Vision | Product image understanding |
| BigQuery | Inventory analytics and warehouse data |
| Google Cloud Storage (GCS) | Reference product images |
| FastAPI | Backend orchestration APIs |
| React + Vite | Frontend dashboard |
| Arize AX | AI observability and tracing |
| Arize MCP | Partner MCP integration for tracing guidance and Arize AX docs access |
| Vertex AI Agent Builder | Agent configuration, OpenAPI tool connection, and Agent Engine deployment |
| MCP | Agent tool interoperability through Arize MCP and the OpsPilot stdio MCP server |

## Example Workflow

### Scenario: Wrong-Zone Chemical Shipment

#### 1. Shipment Detection

At 1:00 AM, the Warehouse Status Agent detects:

- Shipment A arriving at 8:00 AM
- Shipment B arriving at 3:00 PM

#### 2. Orchestration

The Orchestrator Agent assigns:

- map refresh
- inventory validation
- product recognition tasks

#### 3. Product Intake

A warehouse worker uploads a product intake photo.

Gemini Vision extracts:

- item ID
- visible label
- package type
- detected zone

#### 4. Validation

The Validation Agent compares:

- uploaded image
- expected product
- reference image from GCS
- BigQuery inventory metadata

#### 5. Misload Detection

OpsPilot AI detects:

- product expected in Chemical Storage
- product detected in Receiving Dock

#### 6. Incident Workflow

The Incident Agent:

- creates an operational alert
- logs AI reasoning
- routes notification to warehouse supervisor

#### 7. Arize Trace

Arize captures:

- orchestration flow
- agent handoffs
- Gemini reasoning chain
- validation confidence
- investigation timeline

## Product Screens

### Operations Dashboard

- live orchestration status
- active agents
- inbound shipments
- validation status
- operational insights

### Warehouse Map

- real-time rack occupancy
- expected vs actual placement
- zone visualization

### Product Recognition

- shipment photo intake
- Gemini Vision validation
- GCS reference comparison

### Investigation Console

- operational trace graph
- mismatch reasoning
- AI workflow timeline
- incident routing

## Project Structure

```text
OpsPilot-AI/
├── backend/
│   ├── adk_agent/
│   ├── agents/
│   ├── api/
│   ├── observability/
│   ├── services/
│   │   ├── gemini/
│   │   ├── storage/
│   │   └── bigquery_service.py
│   ├── scripts/
│   ├── mcp_server.py
│   └── main.py
├── docs/
│   ├── agent_builder/
│   ├── arize_mcp/
│   └── mcp/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── styles/
│   └── package.json
└── README.md
```

## Local Development

### Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend

```bash
cd frontend

npm install
npm run dev
```

### MCP Server

```bash
cd backend
source .venv/bin/activate
python mcp_server.py
```

The MCP server exposes:

- `get_daily_orchestration`
- `get_warehouse_map`
- `validate_product_intake`
- `lookup_item_master`
- `lookup_shipment_status`

See [docs/mcp/README.md](docs/mcp/README.md).

### Arize MCP Integration

OpsPilot targets the Arize hackathon track and includes Arize MCP setup files in
[docs/arize_mcp](docs/arize_mcp). The Arize MCP integration is used alongside
Arize AX tracing so developers and judges can inspect instrumentation guidance,
trace debugging context, and Arize AX documentation from an MCP-capable agent
environment.

### Vertex AI ADK Agent

OpsPilot includes a Google ADK package in [backend/adk_agent](backend/adk_agent).
It exposes the Cloud Run backend as ADK function tools for orchestration status,
warehouse map retrieval, and product intake validation.

```bash
/usr/local/bin/python3.11 -m venv backend/adk_agent/.venv
source backend/adk_agent/.venv/bin/activate
python --version
pip install -r backend/adk_agent/requirements.txt

export OPSPILOT_API_BASE=https://opspilot-457509635383.us-central1.run.app
adk run backend/adk_agent
```

Deploy to Vertex AI Agent Engine:

```bash
python -m backend.adk_agent.deploy_agent \
  --project YOUR_PROJECT_ID \
  --location us-central1 \
  --staging-bucket gs://YOUR_AGENT_STAGING_BUCKET \
  --api-base https://opspilot-457509635383.us-central1.run.app
```

### Vertex AI Agent Builder

Agent Builder configuration files are in [docs/agent_builder](docs/agent_builder):

- `openapi.yaml` for deployed FastAPI tools
- `agent_builder.yaml` for agent instructions, ADK package notes, and tool configuration notes

Deploy the backend to Cloud Run, then add the OpenAPI tools or deploy the ADK package in Vertex AI Agent Builder.

## Environment Variables

Create `.env` inside `/backend`:

```env
GOOGLE_API_KEY=your_gemini_key

GCP_PROJECT_ID=your_project

ENABLE_ARIZE_AX=true
ARIZE_SPACE_ID=your_arize_space_id
ARIZE_API_KEY=your_arize_api_key

BIGQUERY_DATASET=warehouse_ops
```

## Future Roadmap

- real-time warehouse camera streams
- autonomous forklift routing
- predictive inventory congestion detection
- AI-powered root cause analysis
- voice-driven warehouse investigation assistant
- digital twin warehouse simulation
- IoT sensor integration
- multimodal operational copilots

## Hackathon Vision

OpsPilot AI demonstrates how multi-agent AI systems can evolve beyond chatbots into real operational infrastructure.

Instead of simply answering questions, OpsPilot AI:

- monitors the physical world
- validates operational reality
- orchestrates autonomous workflows
- investigates anomalies
- explains AI decisions
- routes operational actions

This is the future of AI-powered operations.

## Team

Built for the Rapid Agent AI Hackathon using:

- Google Gemini
- Google Cloud
- Arize AX
- Arize MCP
- FastAPI
- React
- BigQuery
- GCS

## License

MIT License. See [LICENSE](LICENSE).

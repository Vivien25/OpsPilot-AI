# OpsPilot AI MCP Server

OpsPilot AI includes a stdio Model Context Protocol server at:

```text
backend/mcp_server.py
```

It implements JSON-RPC MCP methods:

- `initialize`
- `notifications/initialized`
- `ping`
- `tools/list`
- `tools/call`

## Tools

| Tool | Purpose |
| --- | --- |
| `get_daily_orchestration` | Run daily shipment and agent orchestration. |
| `get_warehouse_map` | Return warehouse map, rack occupancy, zones, and inventory. |
| `validate_product_intake` | Validate product intake data and return approval or exception details. |
| `lookup_item_master` | Look up a BigQuery `box_master` item row. |
| `lookup_shipment_status` | Look up a BigQuery `warehouse_status` shipment row. |

## Run Locally

```bash
cd backend
source .venv/bin/activate
python mcp_server.py
```

## Example MCP Client Config

```json
{
  "mcpServers": {
    "opspilot-ai": {
      "command": "python",
      "args": ["/absolute/path/to/OpsPilot-AI/backend/mcp_server.py"],
      "env": {
        "GOOGLE_API_KEY": "your_gemini_key",
        "GCP_PROJECT_ID": "your_project",
        "BIGQUERY_DATASET": "warehouse_ops"
      }
    }
  }
}
```

Use the backend virtual environment's Python path if your MCP client supports absolute commands:

```text
/absolute/path/to/OpsPilot-AI/backend/.venv/bin/python
```

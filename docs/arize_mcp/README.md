# Arize MCP Integration

OpsPilot AI is submitted for the Arize track. The product uses Arize AX for AI
observability and includes Arize MCP configuration so MCP-capable development
agents can access Arize tracing guidance and Arize AX documentation while
instrumenting and debugging the warehouse agent workflow.

## Partner MCP Servers

Arize documents two MCP servers:

- `arize-tracing-assistant`: tracing and instrumentation guidance.
- `arize-ax-docs`: Arize AX documentation and reference search.

The manual MCP configuration is in [arize_mcp_config.json](arize_mcp_config.json).

## Gemini CLI

```bash
gemini extensions install https://github.com/Arize-ai/arize-tracing-assistant
gemini mcp add arize-ax-docs https://arize.com/docs/mcp
```

## Claude Code

```bash
claude mcp add arize-tracing-assistant uvx arize-tracing-assistant@latest
claude mcp add arize-ax-docs --transport http https://arize.com/docs/mcp
claude mcp list
```

## Cursor Or Manual MCP Client

Add this configuration to the MCP client settings:

```json
{
  "mcpServers": {
    "arize-tracing-assistant": {
      "command": "uvx",
      "args": ["arize-tracing-assistant@latest"]
    },
    "arize-ax-docs": {
      "url": "https://arize.com/docs/mcp"
    }
  }
}
```

## How OpsPilot Uses Arize

OpsPilot emits Arize AX traces from the FastAPI backend and the product
recognition workflow. The Arize MCP servers support the developer and judge
workflow by exposing Arize instrumentation help and documentation through MCP
while the deployed Gemini agent and Cloud Run backend perform the operational
work.

Relevant OpsPilot files:

- `backend/observability/arize_ax_setup.py`
- `backend/observability/tracing.py`
- `backend/api/product_recognition.py`
- `backend/adk_agent/agent.py`

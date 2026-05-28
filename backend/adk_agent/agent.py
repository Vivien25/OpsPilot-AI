import json
import os
from typing import Any
from urllib import error, request

from google.adk.agents import Agent


DEFAULT_API_BASE = "https://opspilot-457509635383.us-central1.run.app"
API_BASE = os.getenv("OPSPILOT_API_BASE", DEFAULT_API_BASE).rstrip("/")
MODEL = os.getenv("OPSPILOT_ADK_MODEL", "gemini-2.5-flash")


def _call_backend(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(f"{API_BASE}{path}", data=body, method=method, headers=headers)

    try:
        with request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {"status": "empty_response"}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {
            "error": "backend_http_error",
            "status_code": exc.code,
            "detail": detail,
            "api_base": API_BASE,
            "path": path,
        }
    except Exception as exc:
        return {
            "error": "backend_unavailable",
            "detail": str(exc),
            "api_base": API_BASE,
            "path": path,
        }


def check_opspilot_health() -> dict[str, Any]:
    """Check whether the deployed OpsPilot backend is reachable."""
    return _call_backend("GET", "/health/")


def get_daily_orchestration() -> dict[str, Any]:
    """Retrieve today's warehouse orchestration run, active agents, shipments, and incidents."""
    return _call_backend("GET", "/api/orchestration/daily")


def get_warehouse_map() -> dict[str, Any]:
    """Retrieve the warehouse map, rack occupancy, zones, and inventory placement status."""
    return _call_backend("GET", "/api/map")


def validate_product_intake(
    item_id: str,
    shipment_id: str = "IN-7782",
    detected_label: str = "",
    detected_package_size: str = "",
    detected_condition: str = "No visible abnormal signs",
    detected_zone: str = "Unknown",
) -> dict[str, Any]:
    """Validate a product intake record against item master and shipment expectations."""
    payload = {
        "item_id": item_id,
        "shipment_id": shipment_id,
        "detected_label": detected_label or item_id,
        "detected_package_size": detected_package_size or "Unknown package size",
        "detected_condition": detected_condition,
        "detected_zone": detected_zone,
    }
    return _call_backend("POST", "/api/product-recognition", payload)


root_agent = Agent(
    model=MODEL,
    name="opspilot_ai_agent",
    description="Warehouse operations agent for OpsPilot AI.",
    instruction="""
You are OpsPilot AI, an AI-powered warehouse operations agent.

Use your tools before answering operational questions. Check orchestration status
for shipment timing and active agents. Check the warehouse map for rack, zone,
and placement questions. Use product intake validation when the user gives an
item ID, detected label, package type, condition, or zone.

When responding, explain the operational decision clearly:
- expected product and detected product
- expected zone and detected zone
- approval or exception decision
- incident owner or next action when something is abnormal

If backend data is unavailable, say which OpsPilot service could not be reached
and what the warehouse team should verify next.
""",
    tools=[
        check_opspilot_health,
        get_daily_orchestration,
        get_warehouse_map,
        validate_product_intake,
    ],
)

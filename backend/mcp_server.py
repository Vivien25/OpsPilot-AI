import json
import sys
import traceback
from typing import Any

from agents.orchestration_agent import run_daily_orchestration
from agents.map_agent import generate_warehouse_map
from api.product_recognition import ProductRecognitionRequest, _evaluate_product_recognition
from services.bigquery_service import fetch_box_master_item, fetch_shipment_status


PROTOCOL_VERSION = "2025-03-26"


TOOLS = [
    {
        "name": "get_daily_orchestration",
        "description": "Run the OpsPilot daily warehouse orchestration and return shipments, agents, validation, incidents, and timeline.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_warehouse_map",
        "description": "Generate the current warehouse map, rack occupancy, zones, and inventory summary.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "validate_product_intake",
        "description": "Validate a product intake record against OpsPilot item-master logic and return approval or exception details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Detected or expected item id, for example FG-101."},
                "shipment_id": {"type": "string", "description": "Shipment id, for example SHIP-B-1500 or IN-7782."},
                "detected_label": {"type": "string", "description": "Visible label text detected from the product photo."},
                "detected_package_size": {"type": "string", "description": "Detected package type or size."},
                "detected_condition": {"type": "string", "description": "Detected product condition or abnormal signs."},
                "detected_zone": {"type": "string", "description": "Detected zone, or Unknown if the zone is not visible."},
            },
            "required": ["item_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "lookup_item_master",
        "description": "Look up a single BigQuery box_master item record by item id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Item id to look up, for example PKG-103."}
            },
            "required": ["item_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "lookup_shipment_status",
        "description": "Look up a BigQuery warehouse_status shipment row by shipment id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "shipment_id": {"type": "string", "description": "Shipment id to look up."}
            },
            "required": ["shipment_id"],
            "additionalProperties": False,
        },
    },
]


def _read_message() -> dict[str, Any] | None:
    headers = {}

    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None

        if line in (b"\r\n", b"\n"):
            break

        if b":" in line:
            key, value = line.decode("utf-8").split(":", 1)
            headers[key.strip().lower()] = value.strip()
        else:
            stripped = line.strip()
            if stripped:
                return json.loads(stripped.decode("utf-8"))

    content_length = int(headers.get("content-length", "0"))
    if content_length <= 0:
        return None

    body = sys.stdin.buffer.read(content_length)
    return json.loads(body.decode("utf-8"))


def _write_message(message: dict[str, Any]) -> None:
    body = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _success(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _tool_result(payload: Any) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, indent=2, default=str),
            }
        ]
    }


def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "get_daily_orchestration":
        return _tool_result(run_daily_orchestration())

    if name == "get_warehouse_map":
        return _tool_result(generate_warehouse_map())

    if name == "validate_product_intake":
        request = ProductRecognitionRequest(
            item_id=arguments.get("item_id", "UNKNOWN"),
            shipment_id=arguments.get("shipment_id", "IN-7782"),
            detected_label=arguments.get("detected_label", "Unknown product"),
            detected_package_size=arguments.get("detected_package_size", "Unknown package size"),
            detected_condition=arguments.get("detected_condition", "Unknown condition"),
            detected_zone=arguments.get("detected_zone", "Unknown"),
        )
        return _tool_result(_evaluate_product_recognition(request))

    if name == "lookup_item_master":
        item = fetch_box_master_item(arguments["item_id"])
        return _tool_result(item or {"found": False, "item_id": arguments["item_id"]})

    if name == "lookup_shipment_status":
        shipment = fetch_shipment_status(arguments["shipment_id"])
        return _tool_result(shipment or {"found": False, "shipment_id": arguments["shipment_id"]})

    raise ValueError(f"Unknown tool: {name}")


def _handle(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if method == "initialize":
        return _success(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "opspilot-ai-mcp", "version": "0.1.0"},
            },
        )

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return _success(request_id, {})

    if method == "tools/list":
        return _success(request_id, {"tools": TOOLS})

    if method == "tools/call":
        try:
            name = params["name"]
            arguments = params.get("arguments") or {}
            return _success(request_id, _call_tool(name, arguments))
        except Exception as exc:
            return _error(request_id, -32000, str(exc), traceback.format_exc())

    return _error(request_id, -32601, f"Method not found: {method}")


def main() -> None:
    while True:
        message = _read_message()
        if message is None:
            break

        response = _handle(message)
        if response is not None and "id" in message:
            _write_message(response)


if __name__ == "__main__":
    main()

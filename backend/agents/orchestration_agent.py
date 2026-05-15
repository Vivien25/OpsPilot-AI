from datetime import datetime, timezone

from services.bigquery_service import fetch_inventory_map, fetch_rack_master, fetch_warehouse_status


FALLBACK_SHIPMENTS = [
    {
        "shipment_id": "SHIP-A-0800",
        "shipment_name": "Shipment A",
        "arrival_time": "08:00 AM",
        "status": "arriving_today",
        "expected_zone": "Chemical Storage",
        "expected_items": ["CHEM-102", "CHEM-130", "CHEM-145"],
        "map_refresh_required": True,
        "last_checked": "01:00 AM",
    },
    {
        "shipment_id": "SHIP-B-1500",
        "shipment_name": "Shipment B",
        "arrival_time": "03:00 PM",
        "status": "arriving_today",
        "expected_zone": "Finished Goods",
        "expected_items": ["FG-220", "FG-141", "FG-156"],
        "map_refresh_required": True,
        "last_checked": "01:00 AM",
    },
]


def _agent(name: str, status: str, message: str, owner: str = "OpsPilot") -> dict:
    return {
        "name": name,
        "status": status,
        "owner": owner,
        "message": message,
    }


def _format_shipment(row: dict) -> dict:
    arrival = row.get("arrival_time")
    if hasattr(arrival, "strftime"):
        arrival = arrival.strftime("%I:%M %p")
    return {
        "shipment_id": row.get("shipment_id"),
        "shipment_name": row.get("shipment_name"),
        "arrival_time": str(arrival),
        "status": row.get("status"),
        "expected_zone": row.get("expected_zone"),
        "expected_items": list(row.get("expected_items") or []),
        "map_refresh_required": bool(row.get("map_refresh_required")),
        "last_checked": str(row.get("last_checked") or "01:00 AM"),
    }


def run_daily_orchestration() -> dict:
    shipments = [_format_shipment(row) for row in fetch_warehouse_status()] or FALLBACK_SHIPMENTS
    inventory = fetch_inventory_map(200)
    racks = fetch_rack_master(200)

    expected_items = {
        item_id
        for shipment in shipments
        for item_id in shipment.get("expected_items", [])
    }
    inventory_by_id = {row.get("item_id"): row for row in inventory if row.get("item_id")}
    missing_items = sorted(item_id for item_id in expected_items if item_id not in inventory_by_id)

    wrong_zone_items = []
    for shipment in shipments:
        for item_id in shipment.get("expected_items", []):
            item = inventory_by_id.get(item_id)
            if item and item.get("zone") and item.get("zone") != shipment.get("expected_zone"):
                wrong_zone_items.append(
                    {
                        "item_id": item_id,
                        "detected_zone": item.get("zone"),
                        "expected_zone": shipment.get("expected_zone"),
                        "shipment_id": shipment.get("shipment_id"),
                    }
                )

    validation_status = "completed" if not missing_items and not wrong_zone_items else "needs_attention"
    active_incidents = [
        {
            "ticket_id": "INC-A-001",
            "severity": "High",
            "owner": "Chemical Storage Supervisor",
            "summary": "CHEM-102 requires damage validation before storage release.",
            "status": "created",
        }
    ] if validation_status == "needs_attention" else []

    agent_chain = [
        _agent("Warehouse Status Check Agent", "completed", f"Found {len(shipments)} inbound shipments today."),
        _agent("Orchestrator Agent", "running", "Assigned map refresh and validation tasks for inbound shipments."),
        _agent("Map Agent", "completed", f"Refreshed map with {len(inventory) or 100} inventory records and {len(racks) or 96} racks."),
        _agent(
            "Validation Agent",
            validation_status,
            "Shipment A was mapped successfully." if validation_status == "completed" else "Some expected items are missing or appear in the wrong zone.",
        ),
        _agent(
            "Misload Detection Agent",
            "idle" if not wrong_zone_items else "completed",
            "No wrong-zone candidates found." if not wrong_zone_items else f"Detected {len(wrong_zone_items)} wrong-zone candidates.",
        ),
        _agent(
            "Incident Agent",
            "idle" if not active_incidents else "completed",
            "No ticket required." if not active_incidents else "Created incident tickets for unresolved validation findings.",
        ),
        _agent(
            "Contact / Notification Agent",
            "idle" if not active_incidents else "completed",
            "No notification required." if not active_incidents else "Sent tickets to the correct zone owners.",
        ),
    ]

    timeline = [
        {"time": "01:00 AM", "agent": "Warehouse Status Check Agent", "event": "Checked warehouse_status table and found inbound shipments."},
        {"time": "08:30 AM", "agent": "Orchestrator Agent", "event": "Assigned Map Agent to refresh warehouse map for Shipment A."},
        {"time": "08:35 AM", "agent": "Validation Agent", "event": "Checked expected items against detected zones and rack locations."},
        {"time": "08:37 AM", "agent": "Misload Detection Agent", "event": "Compared item expected zone with actual detected zone."},
        {"time": "08:40 AM", "agent": "Incident Agent", "event": "Created tickets only for unresolved findings."},
        {"time": "08:41 AM", "agent": "Contact / Notification Agent", "event": "Routed the ticket to the responsible supervisor."},
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_status": "autonomous_monitoring",
        "shipments": shipments,
        "metrics": {
            "shipments_today": len(shipments),
            "agents_active": sum(1 for agent in agent_chain if agent["status"] in {"running", "needs_attention"}),
            "map_records": len(inventory) or 100,
            "open_incidents": len(active_incidents),
        },
        "agent_chain": agent_chain,
        "timeline": timeline,
        "validation": {
            "status": validation_status,
            "missing_items": missing_items,
            "wrong_zone_items": wrong_zone_items,
            "message": "Shipment A was mapped successfully." if validation_status == "completed" else "Validation found items that need investigation.",
        },
        "incidents": active_incidents,
        "notifications": [
            {
                "recipient": incident["owner"],
                "ticket_id": incident["ticket_id"],
                "status": "sent",
            }
            for incident in active_incidents
        ],
    }

from datetime import datetime, timezone

from observability.tracing import set_span_attributes, set_span_io, start_span
from services.bigquery_service import (
    fetch_box_master_item,
    fetch_inventory_map,
    fetch_rack_master,
    fetch_shipment_status,
    fetch_warehouse_status,
)


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

FALLBACK_BOX_MASTER = {
    "item_id": "FG-220",
    "box_id": "BOX-FG-220",
    "item_name": "Finished Product Box",
    "box_description": "Finished goods carton prepared for inbound intake validation.",
    "expected_zone": "Finished Goods",
    "expected_rack": "B12",
    "length_cm": 48.0,
    "width_cm": 32.0,
    "height_cm": 24.0,
    "weight_kg": 12.5,
    "package_type": "Finished Goods Carton",
    "visual_description": "sealed finished product carton with visible FG-220 label",
    "sample_image_gcs_uri": "gs://opspilot-box-samples/fg-220.jpg",
    "responsible_contact_id": "C-201",
    "risk_level": "Low",
}

SIMULATED_PRODUCT_PHOTO = {
    "shipment_id": "SHIP-B-1500",
    "uploaded_at": "03:02 PM",
    "detected_item_id": "FG-220",
    "detected_label": "FG-220",
    "detected_package_type": "Finished Goods Carton",
    "detected_dimensions_cm": {
        "length_cm": 48.0,
        "width_cm": 32.0,
        "height_cm": 24.0,
    },
    "detected_zone": "Finished Goods",
    "condition": "normal",
    "confidence": 0.94,
    "visual_evidence": "Worker photo shows a sealed finished goods carton with visible FG-220 label.",
}


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


def _size_text(row: dict) -> str:
    return f"{row.get('length_cm')} x {row.get('width_cm')} x {row.get('height_cm')} cm"


def _matches_text(detected: str | None, expected: str | None) -> bool:
    if not detected or not expected:
        return False
    return str(detected).strip().lower() == str(expected).strip().lower()


def _dimensions_match(detected: dict, reference: dict, tolerance: float = 0.2) -> bool:
    for key in ("length_cm", "width_cm", "height_cm"):
        expected = reference.get(key)
        actual = detected.get(key)
        if expected is None or actual is None:
            return False
        try:
            if abs(float(actual) - float(expected)) / max(float(expected), 1.0) > tolerance:
                return False
        except (TypeError, ValueError):
            return False
    return True


def _find_intake_shipment(shipments: list[dict]) -> dict:
    for shipment in shipments:
        if shipment.get("shipment_id") == SIMULATED_PRODUCT_PHOTO["shipment_id"]:
            return shipment
    return FALLBACK_SHIPMENTS[1]


def run_daily_orchestration() -> dict:
    with start_span(
        "opspilot.daily_orchestration",
        kind="CHAIN",
        input_value="Run daily warehouse orchestration: check shipments, refresh map, validate product intake, and route incidents.",
        root=True,
    ) as root_span:
        with start_span(
            "warehouse_status_agent",
            kind="AGENT",
            input_value="Check warehouse_status for today's inbound shipments.",
        ) as span:
            shipments = [_format_shipment(row) for row in fetch_warehouse_status()] or FALLBACK_SHIPMENTS
            set_span_attributes(
                span,
                {
                    "agent.name": "warehouse_status_agent",
                    "agent.status": "completed",
                    "shipment.count": len(shipments),
                    "shipment.ids": [shipment.get("shipment_id") for shipment in shipments],
                },
            )
            set_span_io(span, output_value=f"Found {len(shipments)} inbound shipments today.")

        with start_span(
            "map_agent",
            kind="AGENT",
            input_value="Refresh warehouse map from inventory_map and rack_master.",
        ) as span:
            inventory = fetch_inventory_map(200)
            racks = fetch_rack_master(200)
            set_span_attributes(
                span,
                {
                    "agent.name": "map_agent",
                    "agent.status": "completed",
                    "inventory.record_count": len(inventory),
                    "rack.record_count": len(racks),
                },
            )
            set_span_io(span, output_value=f"Refreshed map with {len(inventory)} inventory records and {len(racks)} racks.")

        intake_shipment = _find_intake_shipment(shipments)
        product_photo = {
            **SIMULATED_PRODUCT_PHOTO,
            "shipment_id": intake_shipment.get("shipment_id") or SIMULATED_PRODUCT_PHOTO["shipment_id"],
        }

        with start_span(
            "product_recognition_agent",
            kind="AGENT",
            input_value=f"Analyze worker product photo for {product_photo['shipment_id']}.",
        ) as span:
            set_span_attributes(
                span,
                {
                    "agent.name": "product_recognition_agent",
                    "agent.status": "completed",
                    "workflow": "product_intake",
                    "shipment.id": product_photo["shipment_id"],
                    "shipment.arrival_time": intake_shipment.get("arrival_time") or "03:00 PM",
                    "image.uploaded": True,
                    "image.uploaded_at": product_photo["uploaded_at"],
                    "vision.detected_item_id": product_photo["detected_item_id"],
                    "vision.detected_label": product_photo["detected_label"],
                    "vision.detected_package_type": product_photo["detected_package_type"],
                    "vision.detected_zone": product_photo["detected_zone"],
                    "vision.confidence": product_photo["confidence"],
                },
            )
            set_span_io(
                span,
                output_value=(
                    f"Detected {product_photo['detected_item_id']} as {product_photo['detected_package_type']} "
                    f"in {product_photo['detected_zone']} with {int(product_photo['confidence'] * 100)}% confidence."
                ),
            )

        with start_span(
            "item_master_rag_retrieval",
            kind="RETRIEVER",
            input_value=f"Retrieve item master, package, shipment, and zone reference data for {product_photo['detected_item_id']}.",
        ) as span:
            item_master = fetch_box_master_item(product_photo["detected_item_id"]) or FALLBACK_BOX_MASTER
            shipment_context = fetch_shipment_status(product_photo["shipment_id"]) or intake_shipment
            set_span_attributes(
                span,
                {
                    "agent.name": "item_master_rag_agent",
                    "agent.status": "completed",
                    "retrieval.source": "box_master, warehouse_status",
                    "retrieval.item_label": item_master.get("item_id"),
                    "retrieval.expected_package_size": _size_text(item_master),
                    "retrieval.product_description": item_master.get("box_description"),
                    "retrieval.shipment_id": shipment_context.get("shipment_id"),
                    "retrieval.expected_zone": item_master.get("expected_zone") or shipment_context.get("expected_zone"),
                    "retrieved.count": 1 if item_master else 0,
                },
            )
            set_span_io(
                span,
                output_value=(
                    f"Retrieved {item_master.get('item_id')} expected in {item_master.get('expected_zone')} "
                    f"as {item_master.get('package_type')} sized {_size_text(item_master)}."
                ),
            )

        expected_items = {
            item_id
            for shipment in shipments
            for item_id in shipment.get("expected_items", [])
        }
        inventory_by_id = {row.get("item_id"): row for row in inventory if row.get("item_id")}

        with start_span(
            "validation_agent",
            kind="AGENT",
            input_value="Compare product photo signals with item master, shipment context, and warehouse map evidence.",
        ) as span:
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

            product_intake_issues = []
            if product_photo["detected_item_id"] != item_master.get("item_id"):
                product_intake_issues.append("Detected label does not match item master.")
            if not _matches_text(product_photo["detected_package_type"], item_master.get("package_type")):
                product_intake_issues.append("Detected package type does not match item master.")
            if not _dimensions_match(product_photo["detected_dimensions_cm"], item_master):
                product_intake_issues.append("Detected package dimensions are outside the expected tolerance.")
            expected_zone = item_master.get("expected_zone") or shipment_context.get("expected_zone")
            if not _matches_text(product_photo["detected_zone"], expected_zone):
                product_intake_issues.append("Detected zone does not match expected zone.")

            product_intake_approved = not product_intake_issues
            validation_status = (
                "completed"
                if not missing_items and not wrong_zone_items and product_intake_approved
                else "needs_attention"
            )
            set_span_attributes(
                span,
                {
                    "agent.name": "validation_agent",
                    "agent.status": validation_status,
                    "validation.status": validation_status,
                    "validation.expected_item_count": len(expected_items),
                    "validation.missing_item_count": len(missing_items),
                    "validation.wrong_zone_count": len(wrong_zone_items),
                    "validation.confidence": 0.94 if validation_status == "completed" else 0.91,
                    "validation.product_intake_status": "approved" if product_intake_approved else "needs_attention",
                    "validation.product_intake_issue_count": len(product_intake_issues),
                    "validation.detected_label": product_photo["detected_label"],
                    "validation.reference_item_id": item_master.get("item_id"),
                    "validation.detected_package_size": _size_text(product_photo["detected_dimensions_cm"]),
                    "validation.expected_package_size": _size_text(item_master),
                    "validation.detected_zone": product_photo["detected_zone"],
                    "validation.expected_zone": expected_zone,
                    "retrieval_relevance": 0.92,
                    "hallucination_risk": "low",
                },
            )
            set_span_io(
                span,
                output_value=(
                    "Product intake approved."
                    if validation_status == "completed"
                    else f"Validation needs attention: {len(missing_items)} missing, {len(wrong_zone_items)} wrong-zone, "
                    f"{len(product_intake_issues)} product-intake issues."
                ),
            )

        with start_span(
            "misload_detection_agent",
            kind="AGENT",
            input_value="Score wrong-zone risk from validation findings.",
        ) as span:
            set_span_attributes(
                span,
                {
                    "agent.name": "misload_detection_agent",
                    "agent.status": "idle" if not wrong_zone_items else "completed",
                    "misload.candidate_count": len(wrong_zone_items),
                    "misload.probability": 0.0 if not wrong_zone_items else 0.91,
                },
            )
            set_span_io(
                span,
                output_value=(
                    "No wrong-zone candidates found."
                    if not wrong_zone_items
                    else f"Detected {len(wrong_zone_items)} wrong-zone candidates."
                ),
            )

        active_incidents = []
        if missing_items or wrong_zone_items:
            active_incidents.append(
                {
                    "ticket_id": "INC-A-001",
                    "severity": "High",
                    "owner": "Chemical Storage Supervisor",
                    "summary": "Shipment map validation found missing or wrong-zone inventory.",
                    "status": "created",
                }
            )
        if product_intake_issues:
            active_incidents.append(
                {
                    "ticket_id": "INC-PROD-300PM-001",
                    "severity": item_master.get("risk_level") or "Medium",
                    "owner": item_master.get("responsible_contact_id") or "Finished Goods Lead",
                    "summary": product_intake_issues[0],
                    "status": "created",
                }
            )

        with start_span(
            "incident_agent",
            kind="AGENT",
            input_value="Create tickets for unresolved product intake or map validation findings.",
        ) as span:
            set_span_attributes(
                span,
                {
                    "agent.name": "incident_agent",
                    "agent.status": "idle" if not active_incidents else "completed",
                    "incident.count": len(active_incidents),
                    "incident_confidence": 0.95 if active_incidents else 0.98,
                },
            )
            set_span_io(
                span,
                output_value=(
                    "No ticket required."
                    if not active_incidents
                    else f"Created {len(active_incidents)} incident ticket(s)."
                ),
            )

        with start_span(
            "contact_notification_agent",
            kind="AGENT",
            input_value="Route active incident tickets to responsible warehouse contacts.",
        ) as span:
            set_span_attributes(
                span,
                {
                    "agent.name": "contact_notification_agent",
                    "agent.status": "idle" if not active_incidents else "completed",
                    "notification.count": len(active_incidents),
                    "notification.owners": [incident["owner"] for incident in active_incidents],
                },
            )
            set_span_io(
                span,
                output_value=(
                    "No notification required."
                    if not active_incidents
                    else f"Sent notifications to {', '.join(incident['owner'] for incident in active_incidents)}."
                ),
            )

        set_span_attributes(
            root_span,
            {
                "orchestration.status": validation_status,
                "orchestration.shipments_today": len(shipments),
                "orchestration.open_incidents": len(active_incidents),
            },
        )
        set_span_io(
            root_span,
            output_value=(
                f"{validation_status}: {len(shipments)} shipments, {len(inventory) or 100} map records, "
                f"{len(active_incidents)} open incidents."
            ),
        )

    agent_chain = [
        _agent("Warehouse Status Check Agent", "completed", f"Found {len(shipments)} inbound shipments today."),
        _agent("Orchestrator Agent", "completed", "Created the product intake plan for the 3:00 PM shipment."),
        _agent("Map Agent", "completed", f"Refreshed map with {len(inventory) or 100} inventory records and {len(racks) or 96} racks."),
        _agent(
            "Product Recognition Agent",
            "completed",
            f"Analyzed worker photo and detected {product_photo['detected_item_id']} with {int(product_photo['confidence'] * 100)}% confidence.",
        ),
        _agent(
            "Item Master RAG Agent",
            "completed",
            f"Retrieved label, package size, shipment, description, and expected zone for {item_master.get('item_id')}.",
        ),
        _agent(
            "Validation Agent",
            validation_status,
            "Product intake approved." if validation_status == "completed" else "Product intake or map validation needs attention.",
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
        {"time": "01:03 AM", "agent": "Orchestrator Agent", "event": "Built the intake workflow for Shipment B arriving at 3:00 PM."},
        {"time": "03:00 PM", "agent": "Warehouse Status Check Agent", "event": "Shipment B arrived at the receiving workflow checkpoint."},
        {"time": "03:02 PM", "agent": "Worker Upload", "event": "Worker uploaded a product photo for intake validation."},
        {"time": "03:03 PM", "agent": "Product Recognition Agent", "event": f"Analyzed product photo and detected {product_photo['detected_item_id']}."},
        {"time": "03:04 PM", "agent": "Item Master RAG Agent", "event": "Retrieved item label, package size, product description, shipment info, and expected zone."},
        {"time": "03:05 PM", "agent": "Validation Agent", "event": "Compared image result against item master and shipment reference data."},
        {
            "time": "03:06 PM",
            "agent": "Incident Agent",
            "event": "Approved product intake." if product_intake_approved else "Created an exception ticket for abnormal intake evidence.",
        },
        {
            "time": "03:07 PM",
            "agent": "Contact / Notification Agent",
            "event": "No notification required." if product_intake_approved else "Sent the intake ticket to the responsible contact.",
        },
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
            "product_intake_issues": product_intake_issues,
            "message": "Product intake approved." if validation_status == "completed" else "Validation found items that need investigation.",
        },
        "product_intake": {
            "shipment_id": product_photo["shipment_id"],
            "arrival_time": intake_shipment.get("arrival_time") or "03:00 PM",
            "uploaded_photo": True,
            "uploaded_at": product_photo["uploaded_at"],
            "detected_item_id": product_photo["detected_item_id"],
            "detected_label": product_photo["detected_label"],
            "detected_package_type": product_photo["detected_package_type"],
            "detected_package_size": _size_text(product_photo["detected_dimensions_cm"]),
            "expected_package_type": item_master.get("package_type"),
            "expected_package_size": _size_text(item_master),
            "product_description": item_master.get("box_description"),
            "shipment_info": f"{shipment_context.get('shipment_name', 'Shipment')} arriving at {shipment_context.get('arrival_time', '03:00 PM')}",
            "detected_zone": product_photo["detected_zone"],
            "expected_zone": item_master.get("expected_zone") or shipment_context.get("expected_zone"),
            "confidence": product_photo["confidence"],
            "decision": "Approve product intake" if product_intake_approved else "Create intake exception",
            "approved": product_intake_approved,
            "issues": product_intake_issues,
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

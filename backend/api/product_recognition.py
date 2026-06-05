import re

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from observability.tracing import set_span_io, start_span

router = APIRouter()


class ProductRecognitionRequest(BaseModel):
    item_id: str = "CHEM-102"
    shipment_id: str = "IN-7782"
    detected_label: str = "Solvent Drum"
    detected_package_size: str = "55 gallon drum"
    detected_condition: str = "minor carton deformation"
    detected_zone: str = "Chemical Storage"


ITEM_MASTER = {
    "CHEM-102": {
        "item_id": "CHEM-102",
        "item_label": "Solvent Drum",
        "expected_package_size": "55 gallon drum",
        "product_description": "Flammable solvent used in production line cleaning.",
        "shipment_info": "Inbound shipment #IN-7782 arriving at 3:00 PM",
        "expected_zone": "Chemical Storage",
        "responsible_contact": "Chemical Storage Supervisor",
    },
    "FG-220": {
        "item_id": "FG-220",
        "item_label": "Finished Product Box",
        "expected_package_size": "standard finished-goods carton",
        "product_description": "Packaged finished goods ready for outbound shipment.",
        "shipment_info": "Outbound shipment #OUT-5521",
        "expected_zone": "Finished Goods",
        "responsible_contact": "Finished Goods Lead",
    },
    "FG-101": {
        "item_id": "FG-101",
        "item_label": "Retail Case",
        "expected_package_size": "shipping carton",
        "product_description": "Finished product retail case packaged for warehouse handling.",
        "shipment_info": "Inbound shipment #IN-7782 arriving at 3:00 PM",
        "expected_zone": "Finished Goods",
        "responsible_contact": "Finished Goods Lead",
    },
    "PKG-103": {
        "item_id": "PKG-103",
        "item_label": "Pallet Sleeve Pack",
        "expected_package_size": "supply case",
        "product_description": "Packaging supply pack for warehouse handling.",
        "shipment_info": "Inbound shipment #IN-7782 arriving at 3:00 PM",
        "expected_zone": "Packaging Supply",
        "responsible_contact": "Packaging Supply Lead",
    },
}


@router.post("/product-recognition")
def run_product_recognition(request: ProductRecognitionRequest):
    return _evaluate_product_recognition(request)


@router.post("/product-recognition/image")
async def run_product_recognition_image(
    image: UploadFile = File(...),
    expected_item_id: str | None = Form(None),
    shipment_id: str = Form("IN-7782"),
):
    image_bytes = await image.read()
    mime_type = image.content_type or "image/png"
    vision = _analyze_uploaded_image(image_bytes, mime_type)
    detected_label = vision.get("visible_label") or vision.get("item_id") or vision.get("package_type") or "Unknown product"
    detected_item_id = vision.get("item_id") or _extract_item_id(detected_label) or expected_item_id or "UNKNOWN"
    detected_package_size = vision.get("package_type") or vision.get("visual_description") or "Unknown package size"
    detected_condition = _condition_from_vision(vision.get("visual_description") or vision.get("vision_summary"))
    bq_reference = _fetch_bigquery_reference(detected_item_id)
    image_gcs_uri = _store_daily_product_image(
        image_bytes=image_bytes,
        mime_type=mime_type,
        shipment_id=shipment_id,
        item_id=detected_item_id,
        original_filename=image.filename,
    )
    reference_comparison = _compare_with_gcs_reference(image_bytes, mime_type, bq_reference)
    shipment_context = _fetch_shipment_context(shipment_id)

    request = ProductRecognitionRequest(
        item_id=detected_item_id,
        shipment_id=shipment_id,
        detected_label=reference_comparison.get("detected_label") or detected_label,
        detected_package_size=reference_comparison.get("detected_package_type") or detected_package_size,
        detected_condition=reference_comparison.get("condition_summary") or detected_condition,
        detected_zone="Unknown",
    )
    return _evaluate_product_recognition(
        request,
        reference_override=_reference_from_bigquery_row(bq_reference, shipment_context, shipment_id) if bq_reference else None,
        image_result_override={
            "filename": image.filename,
            "mime_type": mime_type,
            "image_gcs_uri": image_gcs_uri,
            "detected_label": request.detected_label,
            "detected_package_size": request.detected_package_size,
            "detected_condition": request.detected_condition,
            "detected_zone": request.detected_zone,
            "confidence": vision.get("vision_confidence") or 0,
            "visual_evidence": vision.get("visual_description") or vision.get("vision_summary"),
            "box_id": vision.get("box_id"),
            "item_id": detected_item_id,
            "reference_image_gcs_uri": bq_reference.get("sample_image_gcs_uri") if bq_reference else None,
            "visual_match_score": reference_comparison.get("visual_match_score"),
            "comparison_summary": reference_comparison.get("comparison_summary"),
        },
        reference_comparison=reference_comparison,
    )


def _evaluate_product_recognition(
    request: ProductRecognitionRequest,
    image_result_override: dict | None = None,
    reference_override: dict | None = None,
    reference_comparison: dict | None = None,
):
    with start_span(
        "product_recognition_agent",
        {
            "item_id": request.item_id,
            "shipment_id": request.shipment_id,
            "input.modality": "image",
            "workflow": "product_recognition",
        },
        kind="AGENT",
        input_value={
            "item_id": request.item_id,
            "shipment_id": request.shipment_id,
            "detected_label": request.detected_label,
            "detected_package_size": request.detected_package_size,
            "detected_condition": request.detected_condition,
            "detected_zone": request.detected_zone,
        },
    ) as recognition_span:
        image_result = image_result_override or {
            "detected_label": request.detected_label,
            "detected_package_size": request.detected_package_size,
            "detected_condition": request.detected_condition,
            "detected_zone": request.detected_zone,
            "confidence": 0.94,
        }

        with start_span(
            "item_master_rag_lookup",
            {"item_id": request.item_id, "retrieval.k": 1},
            kind="RETRIEVER",
            input_value={
                "query_item_id": request.item_id,
                "shipment_id": request.shipment_id,
                "lookup": "item label, package size, product description, shipment info, expected zone",
            },
        ) as span:
            reference = reference_override or ITEM_MASTER.get(request.item_id) or _inferred_reference(request)
            set_span_io(
                span,
                output_value={
                    "item_id": reference["item_id"],
                    "item_label": reference["item_label"],
                    "expected_package_size": reference["expected_package_size"],
                    "expected_zone": reference["expected_zone"],
                    "responsible_contact": reference["responsible_contact"],
                },
            )

        checks = []
        exceptions = []

        with start_span(
            "package_validation_agent",
            {"expected_size": reference["expected_package_size"]},
            kind="AGENT",
            input_value={
                "detected_package_size": request.detected_package_size,
                "expected_package_size": reference["expected_package_size"],
            },
        ) as span:
            package_ok = (
                bool(reference_comparison.get("package_match"))
                if reference_comparison and "package_match" in reference_comparison
                else _matches(request.detected_package_size, reference["expected_package_size"])
            )
            checks.append(_check("Package size", package_ok, request.detected_package_size, reference["expected_package_size"]))
            if not package_ok:
                exceptions.append("Package size is unavailable or does not match item master.")
            set_span_io(span, output_value={"package_ok": package_ok, "exception_count": len(exceptions)})

        with start_span(
            "label_validation_agent",
            {"expected_label": reference["item_label"]},
            kind="AGENT",
            input_value={
                "detected_label": request.detected_label,
                "expected_label": reference["item_label"],
                "detected_zone": request.detected_zone,
                "expected_zone": reference["expected_zone"],
                "detected_condition": request.detected_condition,
            },
        ) as span:
            label_ok = (
                bool(reference_comparison.get("label_match"))
                if reference_comparison and "label_match" in reference_comparison
                else _matches(request.detected_label, reference["item_label"])
            )
            zone_detected = request.detected_zone
            if request.detected_zone.strip().lower() == "unknown" and reference["item_id"] != "UNKNOWN":
                zone_detected = f"Zone not visible; {reference['item_id']} maps to {reference['expected_zone']}"
                zone_ok = True
            else:
                zone_ok = _matches(request.detected_zone, reference["expected_zone"])
            condition_ok = (
                bool(reference_comparison.get("condition_ok"))
                if reference_comparison and "condition_ok" in reference_comparison
                else "damage" not in request.detected_condition.lower() and "leak" not in request.detected_condition.lower()
            )
            checks.extend(
                [
                    _check("Label correctness", label_ok, request.detected_label, reference["item_label"]),
                    _check("Product condition", condition_ok, request.detected_condition, "No damage, leakage, or abnormal signs"),
                    _check("Expected zone or item match", zone_ok, zone_detected, reference["expected_zone"]),
                ]
            )
            if reference_comparison:
                visual_ok = float(reference_comparison.get("visual_match_score") or 0) >= 0.72
                checks.append(
                    _check(
                        "Reference image match",
                        visual_ok,
                        reference_comparison.get("comparison_summary") or "Compared uploaded image to GCS sample.",
                        reference.get("sample_image_gcs_uri") or "GCS reference image",
                    )
                )
                if not visual_ok:
                    exceptions.append("Uploaded image does not sufficiently match the GCS reference image.")
            if not label_ok:
                exceptions.append("Detected label differs from item master.")
            if not condition_ok:
                exceptions.append("Product condition requires inspection.")
            if not zone_ok:
                exceptions.append("Detected zone does not match expected zone.")
            set_span_io(
                span,
                output_value={
                    "label_ok": label_ok,
                    "zone_ok": zone_ok,
                    "condition_ok": condition_ok,
                    "exception_count": len(exceptions),
                },
            )

        approved = not exceptions
        with start_span(
            "intake_approval_agent",
            {"approved": approved, "exception_count": len(exceptions)},
            kind="AGENT",
            input_value={"checks": checks, "exceptions": exceptions},
        ) as span:
            decision = "Approve product intake" if approved else "Create intake exception"
            set_span_io(span, output_value={"approved": approved, "decision": decision})

        incident = None
        if not approved:
            with start_span(
                "incident_agent",
                {"responsible_contact": reference["responsible_contact"]},
                kind="AGENT",
                input_value={"exceptions": exceptions, "responsible_contact": reference["responsible_contact"]},
            ) as span:
                incident = {
                    "ticket_id": "INC-PROD-300PM-001",
                    "status": "open",
                    "assigned_to": reference["responsible_contact"],
                    "summary": exceptions[0],
                }
                set_span_io(span, output_value=incident)

        result = {
            "workflow": "POST /api/product-recognition",
            "decision": decision,
            "approved": approved,
            "image_result": image_result,
            "reference_data": reference,
            "checks": checks,
            "exceptions": exceptions,
            "incident": incident,
            "trace_spans": [
                "product_recognition_agent",
                "item_master_rag_lookup",
                "package_validation_agent",
                "label_validation_agent",
                "intake_approval_agent",
                "incident_agent",
            ],
        }
        set_span_io(
            recognition_span,
            output_value={
                "decision": decision,
                "approved": approved,
                "detected_item_id": image_result.get("item_id") or request.item_id,
                "exception_count": len(exceptions),
                "incident_created": bool(incident),
            },
        )
        return result


def _analyze_uploaded_image(image_bytes: bytes, mime_type: str) -> dict:
    try:
        from services.gemini.vision_service import analyze_package_image
    except Exception as exc:
        return {
            "vision_summary": f"Vision analysis unavailable: {exc}",
            "item_id": None,
            "visible_label": None,
            "package_type": None,
            "visual_description": "Vision model unavailable; using exception workflow.",
            "vision_confidence": 0,
        }

    return analyze_package_image(image_bytes, mime_type)


def _fetch_bigquery_reference(item_id: str) -> dict | None:
    try:
        from services.bigquery_service import fetch_box_master_item
    except Exception as exc:
        print(f"BigQuery item master unavailable: {exc}")
        return None

    return fetch_box_master_item(item_id)


def _fetch_shipment_context(shipment_id: str) -> dict | None:
    try:
        from services.bigquery_service import fetch_shipment_status
    except Exception as exc:
        print(f"BigQuery shipment lookup unavailable: {exc}")
        return None

    return fetch_shipment_status(shipment_id)


def _store_daily_product_image(
    image_bytes: bytes,
    mime_type: str,
    shipment_id: str,
    item_id: str,
    original_filename: str | None,
) -> str | None:
    try:
        from services.storage.gcs_service import upload_daily_product_image
    except Exception as exc:
        print(f"Daily product image upload unavailable: {exc}")
        return None

    try:
        return upload_daily_product_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            shipment_id=shipment_id,
            item_id=item_id,
            original_filename=original_filename,
        )
    except Exception as exc:
        print(f"Daily product image upload skipped: {exc}")
        return None


def _compare_with_gcs_reference(image_bytes: bytes, mime_type: str, reference: dict | None) -> dict:
    if not reference or not reference.get("sample_image_gcs_uri"):
        return {}

    try:
        from services.gemini.vision_service import compare_package_to_reference
        from services.storage.gcs_service import download_gcs_image
    except Exception as exc:
        print(f"GCS reference comparison unavailable: {exc}")
        return {}

    downloaded = download_gcs_image(reference["sample_image_gcs_uri"])
    if not downloaded:
        return {}

    reference_bytes, reference_mime_type = downloaded
    return compare_package_to_reference(image_bytes, mime_type, reference_bytes, reference_mime_type, reference)


def _reference_from_bigquery_row(row: dict, shipment: dict | None = None, shipment_id: str | None = None) -> dict:
    shipment_info = _shipment_info(shipment, shipment_id)
    return {
        "item_id": row.get("item_id") or "UNKNOWN",
        "item_label": row.get("item_name") or row.get("item_id") or "Known item label required",
        "expected_package_size": row.get("package_type") or "Known package size required",
        "product_description": row.get("box_description") or row.get("visual_description") or "BigQuery item-master record.",
        "shipment_info": shipment_info,
        "expected_zone": row.get("expected_zone") or "Known zone required",
        "responsible_contact": row.get("responsible_contact_id") or "Receiving Supervisor",
        "sample_image_gcs_uri": row.get("sample_image_gcs_uri"),
        "expected_rack": row.get("expected_rack"),
        "dimensions_cm": f"{row.get('length_cm')} x {row.get('width_cm')} x {row.get('height_cm')}",
        "weight_kg": row.get("weight_kg"),
        "risk_level": row.get("risk_level"),
    }


def _shipment_info(shipment: dict | None, shipment_id: str | None) -> str:
    if not shipment:
        return f"Shipment {shipment_id or 'unknown'}; no warehouse_status row found."

    name = shipment.get("shipment_name") or shipment.get("shipment_id") or shipment_id or "Shipment"
    arrival = shipment.get("arrival_time") or "arrival time pending"
    status = shipment.get("status") or "status pending"
    expected_zone = shipment.get("expected_zone") or "zone pending"
    expected_items = shipment.get("expected_items") or []
    if isinstance(expected_items, list):
        expected_items_text = ", ".join(expected_items) if expected_items else "items pending"
    else:
        expected_items_text = str(expected_items)

    return f"{name} arrives {arrival}; status {status}; expected zone {expected_zone}; expected items {expected_items_text}"


def _extract_item_id(text: str | None) -> str | None:
    if not text:
        return None

    match = re.search(r"\b[A-Z]{2,5}-\d{2,5}\b", text.upper())
    if match:
        return match.group(0)
    return None


def _condition_from_vision(description: str | None) -> str:
    if not description:
        return "Unknown condition"

    lowered = description.lower()
    abnormal_terms = ["damage", "damaged", "leak", "wet", "crush", "crushed", "puncture", "broken", "tear", "torn"]
    if any(term in lowered for term in abnormal_terms):
        return description
    return "No visible abnormal signs"


def _unknown_reference(item_id: str):
    return {
        "item_id": item_id,
        "item_label": "Known item label required",
        "expected_package_size": "Known package size required",
        "product_description": "No item-master match was found for the uploaded image.",
        "shipment_info": "Shipment context requires review",
        "expected_zone": "Known zone required",
        "responsible_contact": "Receiving Supervisor",
    }


def _inferred_reference(request: ProductRecognitionRequest):
    item_id = request.item_id if request.item_id != "UNKNOWN" else _extract_item_id(request.detected_label) or "UNKNOWN"
    label = _label_from_detected_text(request.detected_label, item_id)
    if item_id.startswith("FG-"):
        zone = "Finished Goods"
        contact = "Finished Goods Lead"
    elif item_id.startswith("PKG-"):
        zone = "Packaging Supply"
        contact = "Packaging Supply Lead"
    elif item_id.startswith("CHEM-"):
        zone = "Chemical Storage"
        contact = "Chemical Storage Supervisor"
    else:
        return _unknown_reference(item_id)

    return {
        "item_id": item_id,
        "item_label": label,
        "expected_package_size": request.detected_package_size or "Package type from image",
        "product_description": f"Inferred item-master candidate for {label}.",
        "shipment_info": f"Inbound shipment #{request.shipment_id} arriving at 3:00 PM",
        "expected_zone": zone,
        "responsible_contact": contact,
    }


def _label_from_detected_text(text: str | None, item_id: str) -> str:
    if not text:
        return item_id

    cleaned = text.replace(item_id, " ")
    cleaned = re.sub(r"\b(FINISHED PRODUCT|PACKAGING SUPPLY|HAZARDOUS CHEMICAL|RETAIL CASE)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or item_id


def _matches(actual: str, expected: str) -> bool:
    if not actual or not expected:
        return False
    expected_lower = expected.strip().lower()
    actual_lower = actual.strip().lower()
    if expected_lower.startswith("known "):
        return False
    return actual_lower == expected_lower or expected_lower in actual_lower or actual_lower in expected_lower


def _check(name: str, passed: bool, detected: str, expected: str):
    return {
        "name": name,
        "status": "pass" if passed else "exception",
        "detected": detected,
        "expected": expected,
    }

from collections import defaultdict
from html import escape

from services.bigquery_service import fetch_inventory_map, fetch_rack_master


FALLBACK_INVENTORY = [
    {
        "item_id": "CHEM-102",
        "item_name": "Solvent Drum",
        "item_type": "Hazardous Chemical",
        "zone": "Chemical Storage",
        "rack": "A03",
        "bin_location": "A03-B2",
        "quantity": 12,
        "shipment_id": "IN-7782",
        "status": "active",
        "risk_level": "High",
        "last_updated": "2026-05-08T10:00:00Z",
    },
    {
        "item_id": "FG-220",
        "item_name": "Product Box",
        "item_type": "Finished Product",
        "zone": "Finished Goods",
        "rack": "B12",
        "bin_location": "B12-C1",
        "quantity": 40,
        "shipment_id": "OUT-5521",
        "status": "ready_to_ship",
        "risk_level": "Low",
        "last_updated": "2026-05-08T10:00:00Z",
    },
    {
        "item_id": "RAW-118",
        "item_name": "Steel Coil",
        "item_type": "Production Material",
        "zone": "Raw Materials",
        "rack": "C06",
        "bin_location": "C06-A1",
        "quantity": 18,
        "shipment_id": "IN-7798",
        "status": "active",
        "risk_level": "Medium",
        "last_updated": "2026-05-08T10:00:00Z",
    },
    {
        "item_id": "PKG-134",
        "item_name": "Label Roll",
        "item_type": "Packaging Supply",
        "zone": "Packaging",
        "rack": "D09",
        "bin_location": "D09-C4",
        "quantity": 64,
        "shipment_id": "IN-7814",
        "status": "active",
        "risk_level": "Low",
        "last_updated": "2026-05-08T10:00:00Z",
    },
    {
        "item_id": "MRO-141",
        "item_name": "Pump Seal Kit",
        "item_type": "Maintenance Spare Part",
        "zone": "Maintenance",
        "rack": "E04",
        "bin_location": "E04-B3",
        "quantity": 8,
        "shipment_id": "IN-7821",
        "status": "reserved",
        "risk_level": "Medium",
        "last_updated": "2026-05-08T10:00:00Z",
    },
]

FALLBACK_RACKS = [
    {
        "rack_id": "A03",
        "zone": "Chemical Storage",
        "aisle": "CHEM-1",
        "rack_label": "Chemical Rack A03",
        "x_position": 538,
        "y_position": 96,
        "capacity_slots": 16,
        "allowed_item_types": ["Hazardous Chemical"],
        "risk_zone": "High",
        "is_active": True,
        "last_updated": "2026-05-08T10:00:00Z",
    },
    {
        "rack_id": "B12",
        "zone": "Finished Goods",
        "aisle": "FG-3",
        "rack_label": "Finished Goods Rack B12",
        "x_position": 488,
        "y_position": 318,
        "capacity_slots": 24,
        "allowed_item_types": ["Finished Product"],
        "risk_zone": "Low",
        "is_active": True,
        "last_updated": "2026-05-08T10:00:00Z",
    },
    {
        "rack_id": "C06",
        "zone": "Raw Materials",
        "aisle": "RAW-2",
        "rack_label": "Raw Material Rack C06",
        "x_position": 318,
        "y_position": 112,
        "capacity_slots": 18,
        "allowed_item_types": ["Production Material"],
        "risk_zone": "Medium",
        "is_active": True,
        "last_updated": "2026-05-08T10:00:00Z",
    },
    {
        "rack_id": "D09",
        "zone": "Packaging",
        "aisle": "PKG-3",
        "rack_label": "Packaging Rack D09",
        "x_position": 838,
        "y_position": 112,
        "capacity_slots": 20,
        "allowed_item_types": ["Packaging Supply"],
        "risk_zone": "Low",
        "is_active": True,
        "last_updated": "2026-05-08T10:00:00Z",
    },
    {
        "rack_id": "E04",
        "zone": "Maintenance",
        "aisle": "MRO-1",
        "rack_label": "Maintenance Rack E04",
        "x_position": 82,
        "y_position": 512,
        "capacity_slots": 10,
        "allowed_item_types": ["Maintenance Spare Part"],
        "risk_zone": "Medium",
        "is_active": True,
        "last_updated": "2026-05-08T10:00:00Z",
    },
]

ZONE_LAYOUT = {
    "Receiving": (40, 92, 300, 220),
    "Raw Materials": (370, 92, 300, 220),
    "Chemical Storage": (700, 92, 300, 220),
    "Packaging": (1030, 92, 300, 220),
    "Production": (40, 374, 420, 240),
    "Finished Goods": (490, 374, 420, 240),
    "Shipping": (940, 374, 390, 240),
    "Maintenance": (40, 676, 300, 170),
}

ZONE_ORDER = [
    "Receiving",
    "Raw Materials",
    "Chemical Storage",
    "Packaging",
    "Production",
    "Finished Goods",
    "Shipping",
    "Maintenance",
]

RISK_COLORS = {
    "High": "#b42318",
    "Medium": "#a16207",
    "Low": "#15803d",
}

OCCUPANCY_COLORS = {
    "occupied": "#245bdb",
    "empty": "#15803d",
    "inactive": "#667085",
}


def _risk_color(risk_level: str | None) -> str:
    return RISK_COLORS.get(str(risk_level or "").title(), "#667085")


def _rack_occupancy(inventory: list[dict], racks: list[dict]) -> list[dict]:
    items_by_rack = defaultdict(list)
    for item in inventory:
        if item.get("rack"):
            items_by_rack[item["rack"]].append(item)

    enriched_racks = []
    known_racks = set()

    for rack in racks:
        rack_id = rack.get("rack_id")
        rack_items = items_by_rack.get(rack_id, [])
        capacity = int(rack.get("capacity_slots") or 0)
        occupied_slots = len(rack_items)
        known_racks.add(rack_id)

        enriched_racks.append(
            {
                **rack,
                "occupied_slots": occupied_slots,
                "open_slots": max(capacity - occupied_slots, 0),
                "is_occupied": occupied_slots > 0,
                "utilization": occupied_slots / capacity if capacity else 0,
                "items": rack_items[:8],
            }
        )

    for rack_id, rack_items in sorted(items_by_rack.items()):
        if rack_id in known_racks:
            continue

        zone = rack_items[0].get("zone") or "Unassigned"
        enriched_racks.append(
            {
                "rack_id": rack_id,
                "zone": zone,
                "aisle": "Unmapped",
                "rack_label": f"Unmapped Rack {rack_id}",
                "x_position": 0,
                "y_position": 0,
                "capacity_slots": len(rack_items),
                "allowed_item_types": [],
                "risk_zone": "Unknown",
                "is_active": False,
                "last_updated": None,
                "occupied_slots": len(rack_items),
                "open_slots": 0,
                "is_occupied": True,
                "utilization": 1,
                "items": rack_items[:8],
            }
        )

    return enriched_racks


def _group_inventory(inventory: list[dict], racks: list[dict] | None = None) -> list[dict]:
    grouped = defaultdict(list)
    for row in inventory:
        grouped[row.get("zone") or "Unassigned"].append(row)

    racks_by_zone = defaultdict(list)
    for rack in racks or []:
        racks_by_zone[rack.get("zone") or "Unassigned"].append(rack)

    zones = []
    seen = set()
    ordered_zone_names = ZONE_ORDER + sorted(set(grouped) - set(ZONE_ORDER))

    for zone_name in ordered_zone_names:
        records = grouped.get(zone_name, [])
        if not records and zone_name not in ZONE_LAYOUT:
            continue

        seen.add(zone_name)
        total_quantity = sum(int(item.get("quantity") or 0) for item in records)
        high_risk_count = sum(1 for item in records if str(item.get("risk_level")).lower() == "high")
        ready_count = sum(1 for item in records if item.get("status") == "ready_to_ship")
        zone_racks = racks_by_zone.get(zone_name, [])

        zones.append(
            {
                "name": zone_name,
                "item_count": len(records),
                "quantity": total_quantity,
                "high_risk_count": high_risk_count,
                "ready_to_ship_count": ready_count,
                "rack_count": len(zone_racks),
                "occupied_rack_count": sum(1 for rack in zone_racks if rack.get("is_occupied")),
                "open_slot_count": sum(int(rack.get("open_slots") or 0) for rack in zone_racks),
                "items": records[:6],
            }
        )

    for zone_name in sorted(set(grouped) - seen):
        records = grouped[zone_name]
        zone_racks = racks_by_zone.get(zone_name, [])
        zones.append(
            {
                "name": zone_name,
                "item_count": len(records),
                "quantity": sum(int(item.get("quantity") or 0) for item in records),
                "high_risk_count": sum(1 for item in records if str(item.get("risk_level")).lower() == "high"),
                "ready_to_ship_count": sum(1 for item in records if item.get("status") == "ready_to_ship"),
                "rack_count": len(zone_racks),
                "occupied_rack_count": sum(1 for rack in zone_racks if rack.get("is_occupied")),
                "open_slot_count": sum(int(rack.get("open_slots") or 0) for rack in zone_racks),
                "items": records[:6],
            }
        )

    return zones


def _rack_fill(rack: dict) -> str:
    if not rack.get("is_active", True):
        return OCCUPANCY_COLORS["inactive"]
    if rack.get("is_occupied"):
        return OCCUPANCY_COLORS["occupied"]
    return OCCUPANCY_COLORS["empty"]


def _build_rack_markers(racks: list[dict]) -> str:
    markers = []
    racks_by_zone = defaultdict(list)

    for rack in racks:
        zone_name = rack.get("zone")
        if zone_name in ZONE_LAYOUT:
            racks_by_zone[zone_name].append(rack)

    for zone_name in ZONE_ORDER:
        zone_racks = sorted(
            racks_by_zone.get(zone_name, []),
            key=lambda rack: (str(rack.get("aisle") or ""), str(rack.get("rack_label") or ""), str(rack.get("rack_id") or "")),
        )
        zone_x, zone_y, zone_width, zone_height = ZONE_LAYOUT[zone_name]
        tile_width = 52
        tile_height = 30
        gap = 10
        columns = max(1, int((zone_width - 34) // (tile_width + gap)))
        start_x = zone_x + 17
        start_y = zone_y + 78

        for rack_index, rack in enumerate(zone_racks[:24]):
            column = rack_index % columns
            row = rack_index // columns
            x = start_x + column * (tile_width + gap)
            y = start_y + row * (tile_height + gap)
            if y + tile_height > zone_y + zone_height - 16:
                continue

            fill = _rack_fill(rack)
            opacity = "0.42" if not rack.get("is_active", True) else "1"
            label = escape(str(rack.get("rack_id") or "Rack"))
            title = escape(
                f"{rack.get('rack_label') or rack.get('rack_id')} | "
                f"{rack.get('occupied_slots', 0)}/{rack.get('capacity_slots', 0)} slots"
            )

            markers.append(
                f'<g class="rack-marker" role="listitem" aria-label="{title}">'
                f'<title>{title}</title>'
                f'<rect x="{x}" y="{y}" width="{tile_width}" height="{tile_height}" rx="6" fill="{fill}" opacity="{opacity}" />'
                f'<text x="{x + tile_width / 2}" y="{y + 20}" text-anchor="middle" class="rack-text">{label}</text>'
                f'</g>'
            )

    return "".join(markers)


def _build_svg(zones: list[dict], racks: list[dict]) -> str:
    zone_by_name = {zone["name"]: zone for zone in zones}
    zone_blocks = []
    rack_markers = _build_rack_markers(racks)

    for index, zone_name in enumerate(ZONE_ORDER):
        x, y, width, height = ZONE_LAYOUT[zone_name]
        zone = zone_by_name.get(zone_name, {"name": zone_name, "item_count": 0, "quantity": 0, "items": []})
        fill = "#fff7df" if zone.get("high_risk_count") else "#ffffff"
        stroke = "#f4d38b" if zone.get("high_risk_count") else "#d9e0ea"

        zone_blocks.append(
            f'<g role="listitem" aria-label="{escape(zone_name)}">'
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{fill}" stroke="{stroke}" />'
            f'<text x="{x + 16}" y="{y + 28}" class="map-zone">{escape(zone_name)}</text>'
            f'<text x="{x + 16}" y="{y + 52}" class="map-count">{zone.get("occupied_rack_count", 0)}/{zone.get("rack_count", 0)} racks occupied · {zone.get("open_slot_count", 0)} open slots</text>'
            f'<text x="{x + width - 16}" y="{y + 28}" text-anchor="end" class="map-index">{index + 1:02d}</text>'
            f'</g>'
        )

    return f"""
<svg class="warehouse-svg" viewBox="0 0 1370 900" role="img" aria-label="Warehouse rack occupancy map" xmlns="http://www.w3.org/2000/svg">
  <style>
    .warehouse-svg {{ background: #f8fafc; border-radius: 8px; }}
    .map-title {{ fill: #172033; font: 850 28px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .map-subtitle {{ fill: #667085; font: 760 15px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .map-zone {{ fill: #172033; font: 850 20px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .map-count, .map-bin {{ fill: #667085; font: 760 14px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .map-index {{ fill: #245bdb; font: 900 15px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .rack-text {{ fill: #ffffff; font: 900 12px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; pointer-events: none; }}
    .aisle {{ fill: none; stroke: #b9c4d4; stroke-width: 2; stroke-dasharray: 8 9; }}
    .door {{ fill: #dce8ff; stroke: #9db7ef; }}
    .legend {{ fill: #ffffff; stroke: #d9e0ea; }}
  </style>
  <rect x="18" y="18" width="1334" height="864" rx="10" fill="#f8fafc" stroke="#d9e0ea" />
  <text x="40" y="52" class="map-title">OpsPilot Warehouse Map</text>
  <text x="40" y="78" class="map-subtitle">Rack occupancy by zone. Blue occupied, green empty, gray inactive.</text>
  <path class="aisle" d="M40 342 H1330" />
  <path class="aisle" d="M40 646 H1330" />
  <rect class="door" x="1030" y="796" width="160" height="38" rx="7" />
  <text x="1110" y="820" text-anchor="middle" class="map-count">Outbound dock</text>
  {"".join(zone_blocks)}
  {rack_markers}
  <g aria-label="Rack occupancy legend">
    <rect class="legend" x="1030" y="676" width="300" height="94" rx="8" />
    <circle cx="1054" cy="704" r="8" fill="{OCCUPANCY_COLORS["occupied"]}" />
    <text x="1076" y="709" class="map-count">Occupied rack</text>
    <circle cx="1054" cy="734" r="8" fill="{OCCUPANCY_COLORS["empty"]}" />
    <text x="1076" y="739" class="map-count">Empty rack</text>
    <circle cx="1202" cy="734" r="8" fill="{OCCUPANCY_COLORS["inactive"]}" />
    <text x="1224" y="739" class="map-count">Inactive</text>
  </g>
</svg>
""".strip()


def generate_warehouse_map() -> dict:
    inventory = fetch_inventory_map(100) or FALLBACK_INVENTORY
    rack_source = fetch_rack_master(200) or FALLBACK_RACKS
    racks = _rack_occupancy(inventory, rack_source)
    zones = _group_inventory(inventory, racks)
    total_items = len(inventory)
    high_risk_items = sum(1 for item in inventory if str(item.get("risk_level")).lower() == "high")
    ready_to_ship = sum(1 for item in inventory if item.get("status") == "ready_to_ship")
    active_zones = sum(1 for zone in zones if zone["item_count"])
    occupied_racks = sum(1 for rack in racks if rack["is_occupied"])
    total_racks = len(racks)
    svg = _build_svg(zones, racks)

    return {
        "map_type": "warehouse_inventory",
        "source": "bigquery_inventory_map" if inventory != FALLBACK_INVENTORY else "fallback_inventory",
        "svg": svg,
        "html": f'<div class="warehouse-map">{svg}</div>',
        "metrics": {
            "total_items": total_items,
            "high_risk_items": high_risk_items,
            "ready_to_ship": ready_to_ship,
            "active_zones": active_zones,
            "total_racks": total_racks,
            "occupied_racks": occupied_racks,
            "open_racks": max(total_racks - occupied_racks, 0),
        },
        "zones": zones,
        "racks": racks,
        "inventory": inventory,
    }

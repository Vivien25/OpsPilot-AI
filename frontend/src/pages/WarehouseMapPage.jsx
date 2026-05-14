import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./UploadPage.css";
import "./WarehouseMapPage.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const navItems = [
  { id: "map", label: "Warehouse Map" },
  { id: "analysis", label: "Image Analysis" },
];

const fallbackMap = {
  metrics: {
    total_items: 0,
    high_risk_items: 0,
    ready_to_ship: 0,
    active_zones: 0,
    total_racks: 0,
    occupied_racks: 0,
    open_racks: 0,
  },
  zones: [],
  racks: [],
  inventory: [],
  svg: "",
};

function riskClass(riskLevel) {
  const level = String(riskLevel || "").toLowerCase();
  if (level === "high") return "risk high";
  if (level === "medium") return "risk medium";
  if (level === "low") return "risk low";
  return "risk unknown";
}

function statusLabel(status) {
  return String(status || "unknown").replaceAll("_", " ");
}

export default function WarehouseMapPage({ activePage = "map", onNavigate = () => {} }) {
  const [mapData, setMapData] = useState(fallbackMap);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    axios
      .get(`${API_BASE}/api/map`, { timeout: 8000 })
      .then((response) => {
        if (!isMounted) return;
        setMapData(response.data || fallbackMap);
        setError("");
      })
      .catch((err) => {
        console.error(err);
        if (isMounted) setError("Warehouse map is unavailable. Confirm the backend is running and BigQuery is configured.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const metrics = mapData.metrics || fallbackMap.metrics;
  const inventory = useMemo(() => mapData.inventory || [], [mapData.inventory]);
  const racks = useMemo(() => mapData.racks || [], [mapData.racks]);
  const zones = useMemo(() => mapData.zones || [], [mapData.zones]);
  const highRiskItems = inventory.filter((item) => String(item.risk_level).toLowerCase() === "high").slice(0, 5);

  return (
    <div className="layout">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">
          <div className="logo">OP</div>
          <div>
            <strong>OpsPilot AI</strong>
            <span>Incident console</span>
          </div>
        </div>

        <nav>
          {navItems.map((item) => (
            <button
              className={activePage === item.id ? "active" : ""}
              key={item.id}
              onClick={() => onNavigate(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="app-shell map-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">Warehouse Operations Map</p>
            <h1>Inventory location overview</h1>
          </div>

          <div className={`status-pill ${error ? "offline" : "online"}`}>
            <span className="pulse" />
            {loading ? "Map Agent working" : error ? "Map offline" : "Map Agent complete"}
          </div>
        </header>

        <section className="overview">
          <div>
            <span>Total Items</span>
            <strong>{metrics.total_items}</strong>
          </div>
          <div>
            <span>High Risk</span>
            <strong>{metrics.high_risk_items}</strong>
          </div>
          <div>
            <span>Ready To Ship</span>
            <strong>{metrics.ready_to_ship}</strong>
          </div>
          <div>
            <span>Occupied Racks</span>
            <strong>{metrics.occupied_racks || 0}/{metrics.total_racks || 0}</strong>
          </div>
        </section>

        <section className="map-grid">
          <div className="panel map-panel">
            <div className="panel-heading">
              <div>
                <h2>Warehouse Map</h2>
                <p>Blue racks are occupied. Green racks are empty. Gray racks are inactive.</p>
              </div>
              <span className="panel-token">{mapData.source || "pending"}</span>
            </div>

            {loading ? (
              <div className="map-agent-state">
                <span />
                <div>
                  <strong>Map Agent is creating the warehouse map now</strong>
                  <p>Reading rack master, calculating occupancy, and generating the SVG layout.</p>
                </div>
              </div>
            ) : error ? (
              <div className="empty-state">{error}</div>
            ) : (
              <div className="map-canvas" dangerouslySetInnerHTML={{ __html: mapData.svg || "" }} />
            )}
          </div>

          <div className="panel zone-summary-panel">
            <div className="panel-heading">
              <div>
                <h2>Zone Load</h2>
                <p>Item and risk distribution by warehouse zone.</p>
              </div>
            </div>

            <div className="zone-summary-list">
              {zones.map((zone) => (
                <div key={zone.name}>
                  <div>
                    <strong>{zone.name}</strong>
                    <span>{zone.quantity} units</span>
                  </div>
                  <small>
                    {zone.item_count} items · {zone.occupied_rack_count || 0}/{zone.rack_count || 0} racks occupied · {zone.open_slot_count || 0} open slots
                  </small>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="detail-grid map-detail-grid">
          <div className="panel inventory-panel">
            <div className="panel-heading">
              <div>
                <h2>Inventory Map Records</h2>
                <p>First 100 item locations from BigQuery.</p>
              </div>
            </div>

            <div className="inventory-table-wrap">
              <table className="inventory-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Type</th>
                    <th>Zone</th>
                    <th>Rack</th>
                    <th>Bin</th>
                    <th>Qty</th>
                    <th>Status</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {inventory.slice(0, 12).map((item) => (
                    <tr key={`${item.item_id}-${item.bin_location}`}>
                      <td>
                        <strong>{item.item_id}</strong>
                        <span>{item.item_name}</span>
                      </td>
                      <td>{item.item_type}</td>
                      <td>{item.zone}</td>
                      <td>{item.rack}</td>
                      <td>{item.bin_location}</td>
                      <td>{item.quantity}</td>
                      <td>{statusLabel(item.status)}</td>
                      <td>
                        <span className={riskClass(item.risk_level)}>{item.risk_level || "Unknown"}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel risk-watch-panel">
            <div className="panel-heading">
              <div>
                <h2>Rack Occupancy</h2>
                <p>Physical rack slots from BigQuery rack master.</p>
              </div>
            </div>

            <div className="rack-list">
              {racks.slice(0, 10).map((rack) => (
                <div key={rack.rack_id}>
                  <div>
                    <strong>{rack.rack_id}</strong>
                    <span className={rack.is_occupied ? "occupancy occupied" : "occupancy open"}>
                      {rack.is_occupied ? "Occupied" : "Open"}
                    </span>
                  </div>
                  <span>{rack.rack_label}</span>
                  <small>
                    {rack.zone} · {rack.occupied_slots || 0}/{rack.capacity_slots || 0} slots · {rack.risk_zone} risk zone
                  </small>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="panel high-risk-panel">
          <div className="panel-heading">
            <div>
              <h2>High-Risk Watch</h2>
              <p>Items that need tighter location control.</p>
            </div>
          </div>

          <div className="watch-list horizontal">
            {highRiskItems.length ? (
              highRiskItems.map((item) => (
                <div key={`${item.item_id}-${item.bin_location}`}>
                  <strong>{item.item_id}</strong>
                  <span>{item.item_name}</span>
                  <small>{item.zone} · {item.bin_location}</small>
                </div>
              ))
            ) : (
              <div className="empty-state compact">No high-risk items returned.</div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

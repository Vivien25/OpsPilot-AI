import { useEffect, useState } from "react";
import axios from "axios";
import { productNavItems as navItems } from "../navigation";
import "./UploadPage.css";
import "./ProductPages.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function statusClass(status) {
  return `agent-status ${String(status || "idle").toLowerCase()}`;
}

export default function OperationsDashboardPage({ activePage = "dashboard", onNavigate = () => {} }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;
    axios
      .get(`${API_BASE}/api/orchestration/daily`, { timeout: 8000 })
      .then((response) => {
        if (!isMounted) return;
        setData(response.data);
        setError("");
      })
      .catch((err) => {
        console.error(err);
        if (isMounted) setError("Orchestration data is unavailable. Confirm the backend is running.");
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const metrics = data?.metrics || {};
  const shipments = data?.shipments || [];
  const incidents = data?.incidents || [];
  const reasoningEvents = [
    ["08:30", "Validation started for Shipment A."],
    ["08:32", "Rack mismatch detected in Receiving Dock."],
    ["08:33", "Misload probability elevated to 91%."],
    ["08:35", "Incident workflow triggered for Chemical Storage owner."],
  ];
  const miniZones = ["Receiving", "Chemical", "Finished", "Outbound"];

  return (
    <div className="layout">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">
          <div className="logo">OP</div>
          <div>
            <strong>OpsPilot AI</strong>
            <span>Agent console</span>
          </div>
        </div>
        <nav>
          {navItems.map((item) => (
            <button className={activePage === item.id ? "active" : ""} key={item.id} onClick={() => onNavigate(item.id)} type="button">
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="app-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">Live AI Orchestration</p>
            <h1>Operations dashboard</h1>
          </div>
          <div className={`status-pill ${error ? "offline" : "online"}`}>
            <span className="pulse" />
            {error ? "Offline" : "Autonomous monitoring"}
          </div>
        </header>

        <section className="overview">
          <div>
            <span>Shipments Today</span>
            <strong>{metrics.shipments_today ?? "..."}</strong>
          </div>
          <div>
            <span>Agents Active</span>
            <strong>{metrics.agents_active ?? "..."}</strong>
          </div>
          <div>
            <span>Map Records</span>
            <strong>{metrics.map_records ?? "..."}</strong>
          </div>
          <div>
            <span>Open Incidents</span>
            <strong>{metrics.open_incidents ?? "..."}</strong>
          </div>
        </section>

        {error && <div className="error-box">{error}</div>}

        <section className="dashboard-intelligence-grid">
          <div className="panel ai-insight-panel">
            <div className="panel-heading">
              <div>
                <h2>AI Operational Insight</h2>
                <p>The AI noticed a warehouse mismatch that needs attention.</p>
              </div>
            </div>
            <div className="insight-alert">
              <span>⚠</span>
              <div>
                <strong>Chemical pallet mismatch detected</strong>
                <p>Detected in Receiving Dock, expected in Chemical Storage.</p>
              </div>
            </div>
            <div className="insight-metrics">
              <div>
                <span>Confidence</span>
                <strong>94%</strong>
              </div>
              <div>
                <span>Severity</span>
                <strong>High</strong>
              </div>
              <div>
                <span>Action</span>
                <strong>Ticket ready</strong>
              </div>
            </div>
          </div>

          <div className="panel mini-warehouse-panel">
            <div className="panel-heading">
              <div>
                <h2>Live Warehouse View</h2>
                <p>Map evidence from current rack and zone validation.</p>
              </div>
            </div>
            <div className="dashboard-mini-map">
              {miniZones.map((zone, zoneIndex) => (
                <div className={zone === "Receiving" ? "alert-zone" : ""} key={zone}>
                  <span>{zone}</span>
                  <div>
                    {Array.from({ length: 4 }).map((_, rackIndex) => (
                      <i
                        className={zone === "Receiving" && rackIndex === 1 ? "mismatch" : (rackIndex + zoneIndex) % 2 ? "occupied" : "empty"}
                        key={`${zone}-${rackIndex}`}
                      />
                    ))}
                  </div>
                </div>
              ))}
              <b className="shipment-flow" />
            </div>
          </div>

          <div className="panel reasoning-feed-panel">
            <div className="panel-heading">
              <div>
                <h2>Live AI Reasoning</h2>
                <p>Compact trace of the latest autonomous decision.</p>
              </div>
            </div>
            <div className="reasoning-feed">
              {reasoningEvents.map(([time, message], index) => (
                <div className={index >= 1 ? "warning" : ""} key={`${time}-${message}`}>
                  <strong>{time}</strong>
                  <span>{message}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="detail-grid">
          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Inbound Shipments</h2>
                <p>Found by Warehouse Status Check Agent.</p>
              </div>
            </div>
            <div className="shipment-list compact">
              {shipments.map((shipment) => (
                <article key={shipment.shipment_id}>
                  <strong>{shipment.shipment_name}</strong>
                  <span>{shipment.arrival_time} · {shipment.expected_zone}</span>
                  <span>{shipment.expected_items?.join(", ")}</span>
                </article>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Validation Result</h2>
                <p>Map update status and wrong-zone evidence.</p>
              </div>
              <span className={statusClass(data?.validation?.status)}>{data?.validation?.status || "pending"}</span>
            </div>
            <p className="recommendation-copy">{data?.validation?.message || "Waiting for orchestration run."}</p>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Incident Queue</h2>
                <p>Tickets created by the Incident Agent.</p>
              </div>
              <span className="panel-token">{incidents.length} open</span>
            </div>
            <div className="ticket-list">
              {incidents.length ? incidents.map((incident) => (
                <div className="ticket-row" key={incident.ticket_id}>
                  <strong>{incident.ticket_id}</strong>
                  <span>{incident.summary}</span>
                  <span>{incident.owner} · {incident.severity}</span>
                </div>
              )) : <div className="empty-state">No active incident tickets.</div>}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

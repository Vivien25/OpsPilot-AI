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
  const agents = data?.agent_chain || [];
  const shipments = data?.shipments || [];
  const incidents = data?.incidents || [];

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

        <section className="orchestration-grid">
          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Agent Collaboration</h2>
                <p>Warehouse status, orchestration, map validation, misload detection, ticketing, and notification.</p>
              </div>
            </div>
            <div className="agent-flow">
              {agents.map((agent) => (
                <div className="agent-row" key={agent.name}>
                  <strong>{agent.name}</strong>
                  <span className={statusClass(agent.status)}>{agent.status}</span>
                  <span>{agent.message}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Inbound Shipments</h2>
                <p>Found by Warehouse Status Check Agent.</p>
              </div>
            </div>
            <div className="shipment-list">
              {shipments.map((shipment) => (
                <article key={shipment.shipment_id}>
                  <strong>{shipment.shipment_name}</strong>
                  <span>{shipment.arrival_time} · {shipment.expected_zone}</span>
                  <span>{shipment.expected_items?.join(", ")}</span>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="detail-grid">
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

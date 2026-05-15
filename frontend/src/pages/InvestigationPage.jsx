import { useEffect, useState } from "react";
import axios from "axios";
import { productNavItems as navItems } from "../navigation";
import "./UploadPage.css";
import "./ProductPages.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export default function InvestigationPage({ activePage = "investigation", onNavigate = () => {} }) {
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
        if (isMounted) setError("Investigation trace is unavailable. Confirm the backend is running.");
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const validation = data?.validation || {};
  const timeline = data?.timeline || [];
  const incidents = data?.incidents || [];
  const notifications = data?.notifications || [];

  return (
    <div className="layout">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">
          <div className="logo">OP</div>
          <div>
            <strong>OpsPilot AI</strong>
            <span>Investigation console</span>
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
            <p className="eyebrow">Workflow Trace</p>
            <h1>Incident investigation</h1>
          </div>
          <div className={`status-pill ${error ? "offline" : "online"}`}>
            <span className="pulse" />
            {error ? "Trace offline" : "Trace live"}
          </div>
        </header>

        {error && <div className="error-box">{error}</div>}

        <section className="overview">
          <div>
            <span>Validation</span>
            <strong>{validation.status || "Pending"}</strong>
          </div>
          <div>
            <span>Missing Items</span>
            <strong>{validation.missing_items?.length || 0}</strong>
          </div>
          <div>
            <span>Wrong Zone</span>
            <strong>{validation.wrong_zone_items?.length || 0}</strong>
          </div>
          <div>
            <span>Notifications</span>
            <strong>{notifications.length}</strong>
          </div>
        </section>

        <section className="orchestration-grid">
          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Agent Timeline</h2>
                <p>Every step from warehouse status check to owner notification.</p>
              </div>
            </div>
            <div className="agent-flow">
              {timeline.map((event) => (
                <div className="event-row" key={`${event.time}-${event.agent}`}>
                  <strong>{event.time}</strong>
                  <span>{event.agent}</span>
                  <span>{event.event}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Ticket Generation</h2>
                <p>Incident Agent output and routing state.</p>
              </div>
            </div>
            <div className="ticket-list">
              {incidents.length ? incidents.map((incident) => (
                <div className="ticket-row" key={incident.ticket_id}>
                  <strong>{incident.ticket_id}</strong>
                  <span>{incident.summary}</span>
                  <span>{incident.owner} · {incident.status}</span>
                </div>
              )) : <div className="empty-state">No ticket was required by this orchestration run.</div>}
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Map Validation Evidence</h2>
              <p>Evidence used by Validation and Misload Detection agents.</p>
            </div>
          </div>
          <div className="evidence-grid">
            <div className="event-row">
              <strong>Missing</strong>
              <span>{validation.missing_items?.join(", ") || "None"}</span>
            </div>
            <div className="event-row">
              <strong>Wrong zone</strong>
              <span>
                {validation.wrong_zone_items?.length
                  ? validation.wrong_zone_items.map((item) => `${item.item_id}: ${item.detected_zone} vs ${item.expected_zone}`).join(", ")
                  : "None"}
              </span>
            </div>
            <div className="event-row">
              <strong>Root cause</strong>
              <span>Map update validation compares inbound expected items with active inventory and rack state before ticket creation.</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

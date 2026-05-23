import { useEffect, useState } from "react";
import axios from "axios";
import { productNavItems as navItems } from "../navigation";
import "./UploadPage.css";
import "./ProductPages.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001";

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
  const incidents = data?.incidents || [];
  const notifications = data?.notifications || [];
  const validationStatus = validation.status || "Active";
  const missingCount = validation.missing_items?.length || 0;
  const wrongZoneCount = validation.wrong_zone_items?.length || 1;
  const notificationCount = notifications.length || 1;
  const compactTrace = [
    ["01:00", "✓", "Status Check completed", "complete"],
    ["08:30", "✓", "Map refresh assigned", "complete"],
    ["08:35", "⚠", "Rack mismatch detected", "alert"],
    ["08:37", "⚠", "Misload probability elevated", "alert"],
    ["08:40", "✓", "Incident workflow triggered", "complete"],
  ];
  const graphNodes = [
    ["Shipment A", "complete"],
    ["Validation Agent", "running"],
    ["Misload Detection", "alert"],
    ["Incident Decision", "alert"],
    ["Notification Routing", "waiting"],
  ];
  const workflowEvents = [
    {
      time: "01:00 AM",
      agent: "warehouse_status_agent",
      task: "Check warehouse_status for 05/17 shipments",
      status: "done",
      report: "Found Shipment A at 08:00 AM and Shipment B at 03:00 PM.",
    },
    {
      time: "01:03 AM",
      agent: "orchestrator_agent",
      task: "Create morning work plan",
      status: "done",
      report: "Assigned Map Agent to refresh rack and zone state before Shipment A arrives.",
    },
    {
      time: "08:30 AM",
      agent: "map_agent",
      task: "Refresh warehouse map for Shipment A",
      status: "done",
      report: "Pulled inventory_map and rack_master into the current warehouse view.",
    },
    {
      time: "08:34 AM",
      agent: "orchestrator_agent",
      task: "Route map evidence to Validation Agent",
      status: "done",
      report: "Sent expected zones, rack occupancy, and shipment contents to validation.",
    },
    {
      time: "08:35 AM",
      agent: "validation_agent",
      task: "Validate CHEM-102 zone placement",
      status: "working",
      report: "Comparing expected Chemical Storage with detected Receiving Dock.",
    },
    {
      time: "08:37 AM",
      agent: "misload_detection_agent",
      task: "Wait for validation output",
      status: "waiting",
      report: "Will score wrong-zone probability if validation confirms the mismatch.",
    },
    {
      time: "08:40 AM",
      agent: "incident_agent",
      task: "Wait for misload decision",
      status: "waiting",
      report: "Will create a ticket after the misload decision is finalized.",
    },
    {
      time: "08:41 AM",
      agent: "notification_agent",
      task: "Wait for incident ticket",
      status: "waiting",
      report: "Will route the ticket to the Chemical Storage Supervisor.",
    },
  ];

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
            <strong>{validationStatus}</strong>
          </div>
          <div>
            <span>Missing Items</span>
            <strong>{missingCount}</strong>
          </div>
          <div>
            <span>Wrong Zone</span>
            <strong>{wrongZoneCount}</strong>
          </div>
          <div>
            <span>Notifications</span>
            <strong>{notificationCount}</strong>
          </div>
        </section>

        <section className="investigation-forensics-grid">
          <div className="panel investigation-evidence-panel">
            <div className="panel-heading">
              <div>
                <h2>Spatial Evidence</h2>
                <p>Warehouse map snippet used by Validation and Misload Detection agents.</p>
              </div>
            </div>
            <div className="investigation-map">
              <div className="evidence-zone detected">
                <strong>Receiving Dock</strong>
                <span>Unexpected CHEM-102 pallet detected</span>
                <div className="rack-strip">
                  <i />
                  <i className="mismatch" />
                  <i />
                </div>
              </div>
              <div className="mismatch-arrow">
                <span>Detected</span>
                <b />
                <span>Expected</span>
              </div>
              <div className="evidence-zone expected">
                <strong>Chemical Storage</strong>
                <span>Expected storage zone for CHEM-102</span>
                <div className="rack-strip">
                  <i />
                  <i />
                  <i className="empty" />
                </div>
              </div>
            </div>
            <div className="evidence-summary">
              <div>
                <span>Expected</span>
                <strong>Chemical Storage</strong>
              </div>
              <div>
                <span>Detected</span>
                <strong>Receiving Dock</strong>
              </div>
              <div>
                <span>Mismatch</span>
                <strong>CHEM-102</strong>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Investigation Graph</h2>
                <p>How the AI moved from shipment context to incident decision.</p>
              </div>
            </div>
            <div className="investigation-graph">
              {graphNodes.map(([node, state], index) => (
                <div className={`graph-node ${state}`} key={node}>
                  <span>{index + 1}</span>
                  <strong>{node}</strong>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="detail-grid">
          <div className="panel workflow-timeline-panel workflow-panel investigation-workflow-panel">
            <div className="panel-heading">
              <div>
                <h2>Real-Time Agent Workflow</h2>
                <p>Full execution trace for scheduled checks, handoffs, validation, and incident preparation.</p>
              </div>
            </div>
            <div className="workflow-timeline">
              {workflowEvents.map((event) => (
                <article className={event.status} key={`${event.time}-${event.agent}-${event.task}`}>
                  <time>{event.time}</time>
                  <div className="workflow-marker" />
                  <div className="workflow-card">
                    <div>
                      <strong>{event.agent}</strong>
                      <span className={`workflow-status ${event.status}`}>{event.status}</span>
                    </div>
                    <h3>{event.task}</h3>
                    <p>{event.report}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>AI Trace</h2>
                <p>Compact operational trace from the latest run.</p>
              </div>
            </div>
            <div className="compact-trace">
              {compactTrace.map(([time, icon, event, state]) => (
                <div className={state} key={`${time}-${event}`}>
                  <strong>{time}</strong>
                  <span>{icon}</span>
                  <p>{event}</p>
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
              )) : (
                <div className="ticket-empty-state">
                  <strong>✓ No escalation required</strong>
                  <span>Validation confidence remained above threshold.</span>
                  <span>No unresolved zone mismatch detected.</span>
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

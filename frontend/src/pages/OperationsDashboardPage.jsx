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
  const dashboardWorkflowEvents = workflowEvents.slice(0, 4);
  const architectureNodes = [
    { id: "warehouse_status_agent", label: "Warehouse Status", status: "done", summary: "Find inbound shipments" },
    { id: "map_agent", label: "Map Agent", status: "done", summary: "Refresh warehouse map" },
    { id: "validation_agent", label: "Validation", status: "working", summary: "Check expected zones" },
    { id: "misload_detection_agent", label: "Misload Detection", status: "pending", summary: "Score wrong-zone risk" },
    { id: "incident_agent", label: "Incident", status: "pending", summary: "Create ticket" },
    { id: "notification_agent", label: "Notification", status: "pending", summary: "Route to owner" },
  ];

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

        <section className="dashboard-workflow-grid">
          <div className="dashboard-stack">
            <div className="panel ai-insight-panel dashboard-incident-summary">
              <div className="panel-heading">
                <div>
                  <h2>AI Operational Insight</h2>
                  <p>The system is validating a shipment-map mismatch in real time.</p>
                </div>
              </div>
              <div className="insight-alert">
                <span>!</span>
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
                  <span>Active agent</span>
                  <strong>Validation</strong>
                </div>
                <div>
                  <span>Next handoff</span>
                  <strong>Misload Detection</strong>
                </div>
              </div>
            </div>

            <div className="panel dashboard-inbound-panel">
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
          </div>

          <div className="dashboard-stack dashboard-stack-wide">
            <div className="panel collaboration-diagram-panel">
              <div className="panel-heading">
                <div>
                  <h2>Agent Collaboration Diagram</h2>
                  <p>Autonomous agents coordinate through the Orchestrator Agent.</p>
                </div>
              </div>
              <div className="agent-architecture-diagram" aria-label="Agent collaboration architecture">
                <div className="architecture-node orchestrator-node done">
                  <span>OP</span>
                  <strong>Orchestrator Agent</strong>
                  <small>Assigns work and manages handoffs</small>
                  <em>done</em>
                </div>
                <div className="architecture-branch-grid">
                  {architectureNodes.map((agent) => (
                    <div className={`architecture-node ${agent.status}`} key={agent.id}>
                      <span>{agent.label.slice(0, 2).toUpperCase()}</span>
                      <strong>{agent.label}</strong>
                      <small>{agent.summary}</small>
                      <em>{agent.status}</em>
                    </div>
                  ))}
                </div>
                <div className="diagram-legend">
                  <span className="done">Done</span>
                  <span className="working">Working now</span>
                  <span className="pending">Pending</span>
                </div>
              </div>
            </div>

            <div className="panel dashboard-validation-panel">
              <div className="panel-heading">
                <div>
                  <h2>Validation Result</h2>
                  <p>Map update status and wrong-zone evidence.</p>
                </div>
                <span className={statusClass(data?.validation?.status)}>{data?.validation?.status || "pending"}</span>
              </div>
              <p className="recommendation-copy">{data?.validation?.message || "Waiting for orchestration run."}</p>
            </div>
          </div>

          <div className="dashboard-stack">
            <div className="panel workflow-timeline-panel workflow-panel">
              <div className="panel-heading">
                <div>
                  <h2>Live Workflow</h2>
                  <p>Latest agent handoffs from the active orchestration run.</p>
                </div>
              </div>
              <div className="workflow-timeline">
                {dashboardWorkflowEvents.map((event) => (
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

            <div className="panel dashboard-incident-panel">
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
          </div>
        </section>
      </main>
    </div>
  );
}

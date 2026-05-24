import { useEffect, useState } from "react";
import axios from "axios";
import { productNavItems as navItems } from "../navigation";
import "./UploadPage.css";
import "./ProductPages.css";

const API_BASES = [
  import.meta.env.VITE_API_BASE,
  "http://127.0.0.1:8001",
  "http://127.0.0.1:8000",
].filter(Boolean).filter((base, index, list) => list.indexOf(base) === index);

function statusClass(status) {
  return `agent-status ${String(status || "idle").toLowerCase()}`;
}

function workflowStatus(status) {
  const value = String(status || "").toLowerCase();
  if (value === "completed") return "done";
  if (value === "running" || value === "needs_attention") return "working";
  if (value === "idle") return "waiting";
  return value || "waiting";
}

export default function OperationsDashboardPage({ activePage = "dashboard", onNavigate = () => {} }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;
    async function loadDailyOrchestration() {
      const failures = [];
      for (const baseUrl of API_BASES) {
        try {
          const response = await axios.get(`${baseUrl}/api/orchestration/daily`, { timeout: 12000 });
          if (!isMounted) return;
          setData(response.data);
          setError("");
          return;
        } catch (err) {
          failures.push({ baseUrl, message: err.message });
        }
      }
      console.error("Unable to load orchestration data", failures);
      if (isMounted) setError("Orchestration data is unavailable. Confirm the backend is running.");
    }
    loadDailyOrchestration();
    return () => {
      isMounted = false;
    };
  }, []);

  const metrics = data?.metrics || {};
  const shipments = data?.shipments || [];
  const incidents = data?.incidents || [];
  const productIntake = data?.product_intake || {};
  const agentStatusByName = Object.fromEntries((data?.agent_chain || []).map((agent) => [agent.name, agent.status]));
  const fallbackWorkflowEvents = [
    {
      time: "01:00 AM",
      agent: "Warehouse Status Check Agent",
      task: "Check warehouse_status for 05/17 shipments",
      status: "done",
      report: "Found Shipment A at 08:00 AM and Shipment B at 03:00 PM.",
    },
    {
      time: "01:03 AM",
      agent: "Orchestrator Agent",
      task: "Create product intake plan",
      status: "done",
      report: "Prepared the 3:00 PM Shipment B intake workflow.",
    },
    {
      time: "03:00 PM",
      agent: "Warehouse Status Check Agent",
      task: "Shipment B arrives",
      status: "done",
      report: "Inbound product intake checkpoint opened.",
    },
    {
      time: "03:02 PM",
      agent: "Worker Upload",
      task: "Upload product photo",
      status: "done",
      report: "Worker photo is ready for Product Recognition Agent.",
    },
    {
      time: "03:03 PM",
      agent: "Product Recognition Agent",
      task: "Analyze product photo",
      status: "done",
      report: "Detected FG-220 from the uploaded image.",
    },
    {
      time: "03:04 PM",
      agent: "Item Master RAG Agent",
      task: "Retrieve item reference data",
      status: "done",
      report: "Checked label, package size, description, shipment info, and expected zone.",
    },
    {
      time: "03:05 PM",
      agent: "Validation Agent",
      task: "Compare image result against RAG data",
      status: "done",
      report: "Validated product photo against item master and shipment reference data.",
    },
    {
      time: "03:06 PM",
      agent: "Incident Agent",
      task: "Resolve intake decision",
      status: "done",
      report: "Approved product intake.",
    },
    {
      time: "03:07 PM",
      agent: "Contact / Notification Agent",
      task: "Route exception only if needed",
      status: "done",
      report: "No notification required.",
    },
  ];
  const workflowEvents = (data?.timeline?.length ? data.timeline : fallbackWorkflowEvents).map((event) => ({
    time: event.time,
    agent: event.agent,
    task: event.task || event.event,
    report: event.report || event.event,
    status: event.status
      || (event.agent === "Worker Upload" ? "done" : "")
      || (productIntake.approved && ["Incident Agent", "Contact / Notification Agent"].includes(event.agent) ? "done" : "")
      || workflowStatus(agentStatusByName[event.agent])
      || "done",
  }));
  const dashboardWorkflowEvents = workflowEvents.slice(-6);
  const architectureNodes = [
    { id: "warehouse_status_agent", label: "Warehouse Status", status: "done", summary: "Find inbound shipments" },
    { id: "product_recognition_agent", label: "Product Recognition", status: "done", summary: "Analyze worker photo" },
    { id: "item_master_rag_agent", label: "Item Master RAG", status: "done", summary: "Retrieve reference data" },
    { id: "validation_agent", label: "Validation", status: "done", summary: "Compare photo vs RAG" },
    { id: "incident_agent", label: "Incident", status: productIntake.approved === false ? "done" : "pending", summary: "Create ticket if abnormal" },
    { id: "notification_agent", label: "Notification", status: productIntake.approved === false ? "done" : "pending", summary: "Route to owner" },
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
                  <p>The system is validating product intake photos and shipment-map evidence in real time.</p>
                </div>
              </div>
              <div className="insight-alert">
                <span>!</span>
                <div>
                  <strong>Product Recognition Agent active at intake</strong>
                  <p>Uploaded photos are checked against BigQuery item data and GCS reference images before approval.</p>
                </div>
              </div>
              <div className="insight-metrics">
                <div>
                  <span>Confidence</span>
                  <strong>94%</strong>
                </div>
                <div>
                  <span>Active agent</span>
                  <strong>Product Recognition</strong>
                </div>
                <div>
                  <span>Next handoff</span>
                  <strong>Validation</strong>
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

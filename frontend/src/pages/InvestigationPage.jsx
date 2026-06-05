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

export default function InvestigationPage({ activePage = "investigation", onNavigate = () => {} }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadInvestigationTrace() {
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

      console.error("Unable to load investigation trace", failures);
      if (isMounted) setError("Incident center data is unavailable. Confirm the backend is running.");
    }

    loadInvestigationTrace();
    return () => {
      isMounted = false;
    };
  }, []);

  const validation = data?.validation || {};
  const incidents = data?.incidents || [];
  const notifications = data?.notifications || [];
  const productIntake = data?.product_intake || {};
  const timelineByAgent = Object.fromEntries((data?.timeline || []).map((event) => [event.agent, event]));
  const activeTickets = incidents.map((incident, index) => {
    const status = ["open", "created", "pending"].includes(String(incident.status || "").toLowerCase()) ? "pending" : "fixed";
    return {
      id: incident.ticket_id || `INC-${index + 1}`,
      timestamp: timelineByAgent["Incident Agent"]?.time || "03:06 PM",
      issue: incident.summary || "Incident requires investigation.",
      evidence: productIntake.image_gcs_uri
        ? `Product photo saved at ${productIntake.image_gcs_uri}`
        : "AI validation found unresolved intake or map evidence.",
      contact: incident.owner || "Warehouse Supervisor",
      suggestion: "Review the evidence, correct the item location or intake record, then close the ticket after supervisor confirmation.",
      urgency: incident.severity || "Medium",
      status,
    };
  });
  const resolvedTickets = [
    {
      id: productIntake.shipment_id ? `INTAKE-${productIntake.shipment_id}` : "INTAKE-SHIP-B-1500",
      timestamp: productIntake.uploaded_at || "03:02 PM",
      issue: productIntake.detected_item_id
        ? `Product intake validation for ${productIntake.detected_item_id}`
        : "Product intake validation",
      evidence: productIntake.image_gcs_uri
        ? `Worker image stored in GCS: ${productIntake.image_gcs_uri}`
        : "Product photo, item-master data, shipment context, and expected zone were compared.",
      contact: "Finished Goods Lead",
      suggestion: productIntake.decision || "Approve product intake after validation passes.",
      urgency: productIntake.approved === false ? "Medium" : "Low",
      status: productIntake.approved === false ? "pending" : "fixed",
    },
    {
      id: "MAP-VALIDATION-DAILY",
      timestamp: "01:03 AM",
      issue: "Daily shipment map validation",
      evidence: validation.message || "Warehouse status, inventory map, and rack master were checked.",
      contact: "Operations Supervisor",
      suggestion: validation.status === "completed" ? "No action needed. Keep monitoring scheduled shipment intake." : "Review missing or wrong-zone items.",
      urgency: validation.status === "completed" ? "Low" : "High",
      status: validation.status === "completed" ? "fixed" : "pending",
    },
  ];
  const tickets = [...activeTickets, ...resolvedTickets].filter(
    (ticket, index, list) => list.findIndex((item) => item.id === ticket.id) === index,
  );
  const pendingCount = tickets.filter((ticket) => ticket.status === "pending").length;
  const fixedCount = tickets.filter((ticket) => ticket.status === "fixed").length;
  const urgentCount = tickets.filter((ticket) => ["high", "critical"].includes(String(ticket.urgency).toLowerCase()) && ticket.status === "pending").length;
  const latestTicket = tickets.find((ticket) => ticket.status === "pending") || tickets[0];

  return (
    <div className="layout">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">
          <div className="logo">OP</div>
          <div>
            <strong>OpsPilot AI</strong>
            <span>Incident center</span>
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
            <p className="eyebrow">Incident Command Center</p>
            <h1>Incident Center</h1>
          </div>
          <div className={`status-pill ${error ? "offline" : "online"}`}>
            <span className="pulse" />
            {error ? "Tickets offline" : "Tickets live"}
          </div>
        </header>

        {error && <div className="error-box">{error}</div>}

        <section className="overview">
          <div>
            <span>Open Tickets</span>
            <strong>{pendingCount}</strong>
          </div>
          <div>
            <span>Urgent Now</span>
            <strong>{urgentCount}</strong>
          </div>
          <div>
            <span>Resolved</span>
            <strong>{fixedCount}</strong>
          </div>
          <div>
            <span>Contacts Routed</span>
            <strong>{notifications.length}</strong>
          </div>
        </section>

        <section className="incident-command-grid">
          <div className={`panel incident-priority-card ${urgentCount ? "urgent" : "clear"}`}>
            <div className="panel-heading">
              <div>
                <h2>{pendingCount ? "Action Required" : "No Urgent Issues"}</h2>
                <p>{pendingCount ? "OpsPilot found tickets that still need owner action." : "All current investigation tickets are fixed or informational."}</p>
              </div>
            </div>
            <div className="priority-issue">
              <span className={`ticket-state ${latestTicket.status}`}>{latestTicket.status}</span>
              <strong>{latestTicket.issue}</strong>
              <p>{latestTicket.evidence}</p>
            </div>
            <div className="ticket-meta-grid">
              <div>
                <span>Urgency</span>
                <strong>{latestTicket.urgency}</strong>
              </div>
              <div>
                <span>Owner</span>
                <strong>{latestTicket.contact}</strong>
              </div>
              <div>
                <span>Timestamp</span>
                <strong>{latestTicket.timestamp}</strong>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Resolution Mix</h2>
                <p>Current incident ticket status across the latest orchestration run.</p>
              </div>
            </div>
            <div className="resolution-bars">
              <div>
                <span>Pending</span>
                <b style={{ width: `${Math.max(8, (pendingCount / Math.max(tickets.length, 1)) * 100)}%` }} />
                <strong>{pendingCount}</strong>
              </div>
              <div>
                <span>Fixed</span>
                <b className="fixed" style={{ width: `${Math.max(8, (fixedCount / Math.max(tickets.length, 1)) * 100)}%` }} />
                <strong>{fixedCount}</strong>
              </div>
              <div>
                <span>Urgent</span>
                <b className="urgent" style={{ width: `${Math.max(8, (urgentCount / Math.max(tickets.length, 1)) * 100)}%` }} />
                <strong>{urgentCount}</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Incident Tickets</h2>
              <p>Timestamp, issue, evidence, owner, urgency, AI recommendation, and resolution state.</p>
            </div>
          </div>
          <div className="incident-ticket-grid">
            {tickets.map((ticket) => (
              <article className={`incident-ticket-card ${ticket.status}`} key={ticket.id}>
                <div className="ticket-card-topline">
                  <strong>{ticket.id}</strong>
                  <span className={`ticket-state ${ticket.status}`}>{ticket.status}</span>
                </div>
                <h3>{ticket.issue}</h3>
                <div className="ticket-meta-grid">
                  <div>
                    <span>Timestamp</span>
                    <strong>{ticket.timestamp}</strong>
                  </div>
                  <div>
                    <span>Urgency</span>
                    <strong>{ticket.urgency}</strong>
                  </div>
                  <div>
                    <span>Owner</span>
                    <strong>{ticket.contact}</strong>
                  </div>
                </div>
                <div className="ticket-field">
                  <span>Evidence</span>
                  <p>{ticket.evidence}</p>
                </div>
                <div className="ticket-field">
                  <span>AI Suggested Solution</span>
                  <p>{ticket.suggestion}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="detail-grid compact-investigation-grid">
          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Latest Evidence</h2>
                <p>Operational facts the AI used while deciding ticket state.</p>
              </div>
            </div>
            <div className="evidence-list">
              <div>
                <span>Product image</span>
                <strong>{productIntake.image_gcs_uri || "No daily image URI returned"}</strong>
              </div>
              <div>
                <span>Detected item</span>
                <strong>{productIntake.detected_item_id || "Pending"}</strong>
              </div>
              <div>
                <span>Expected zone</span>
                <strong>{productIntake.expected_zone || "Pending"}</strong>
              </div>
              <div>
                <span>Decision</span>
                <strong>{productIntake.decision || validation.message || "Waiting for validation"}</strong>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Recent Activity</h2>
                <p>Ticket-related events from the latest run.</p>
              </div>
            </div>
            <div className="compact-trace">
              {(data?.timeline || []).slice(-5).map((event) => (
                <div className="complete" key={`${event.time}-${event.agent}`}>
                  <strong>{event.time}</strong>
                  <span>{event.agent}</span>
                  <p>{event.event}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

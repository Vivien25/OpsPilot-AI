import "./UploadPage.css";
import "./ProductPages.css";

export default function LandingPage({ onNavigate = () => {} }) {
  const agents = [
    ["Status Check", "COMPLETE", "✓"],
    ["Map Agent", "COMPLETE", "✓"],
    ["Validation", "RUNNING", "●"],
    ["Incident", "ALERT", "⚠"],
  ];
  const zones = ["Receiving Dock", "Chemical Storage", "Finished Goods", "Outbound Shipping"];
  const events = [
    ["08:35:04", "Validation mismatch detected", "warning"],
    ["08:35:09", "Chemical pallet detected in Receiving Dock", "incident"],
    ["08:35:12", "Incident workflow triggered", "incident"],
  ];
  const health = [
    ["Shipment Sync", "Healthy", "healthy"],
    ["Map Validation", "Active", "warning"],
    ["Incident Queue", "1 Incident", "incident"],
    ["Agent System", "Operational", "healthy"],
  ];

  return (
    <main className="landing-page">
      <section className="landing-hero">
        <nav className="landing-nav" aria-label="Primary">
          <div className="landing-brand">
            <div className="logo">OP</div>
            <span>OpsPilot AI</span>
          </div>
        </nav>

        <div className="landing-hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">AI operations nerve center</p>
            <h1>OpsPilot AI keeps warehouse maps, shipments, and incidents in sync.</h1>
            <p>
              Multi-agent orchestration watches inbound shipments, validates map updates,
              detects misplaced inventory, creates incident tickets, and routes work to the right owner.
            </p>
            <div className="hero-command">
              <button className="solid-btn" onClick={() => onNavigate("dashboard")} type="button">
                See Live Orchestration
              </button>
              <button className="text-btn" onClick={() => onNavigate("map")} type="button">
                Inspect Warehouse Map
              </button>
              <button className="text-btn" onClick={() => onNavigate("investigation")} type="button">
                View Investigation
              </button>
            </div>
          </div>

          <div className="ops-visual" aria-label="Live warehouse orchestration visualization">
            <div className="incident-hero">
              <span className="incident-kicker">Live incident detected</span>
              <h2>Validation Mismatch Detected</h2>
              <div className="incident-chain">
                <span>Validation mismatch detected</span>
                <i />
                <span>Chemical pallet detected in Receiving Dock</span>
                <i />
                <span>Incident workflow triggered</span>
              </div>
              <div className="incident-meta">
                <div>
                  <span>AI Confidence</span>
                  <strong>94%</strong>
                </div>
                <div>
                  <span>Incident Severity</span>
                  <strong>HIGH</strong>
                </div>
              </div>
            </div>

            <div className="mini-map">
              {zones.map((zone, zoneIndex) => (
                <div className="mini-zone" key={zone}>
                  <span>{zone}</span>
                  <div className="mini-racks">
                    {Array.from({ length: 5 }).map((_, rackIndex) => (
                      <i
                        className={zoneIndex === 0 && rackIndex === 1 ? "warning" : (rackIndex + zoneIndex) % 2 === 0 ? "occupied" : "open"}
                        key={`${zone}-${rackIndex}`}
                      />
                    ))}
                  </div>
                </div>
              ))}
              <div className="scan-line" />
            </div>

            <div className="ops-details">
              <div className="agent-strip" aria-label="Agent orchestration state">
                {agents.map(([agent, status, icon], index) => (
                  <div
                    className={`agent-node ${status.toLowerCase()}`}
                    style={{ "--delay": `${index * 0.32}s` }}
                    key={agent}
                  >
                    <span>{icon}</span>
                    <strong>{agent}</strong>
                    <em>{status}</em>
                  </div>
                ))}
              </div>
              <div className="event-log">
                {events.map(([time, event, severity]) => (
                  <div className={severity} key={`${time}-${event}`}>
                    <strong>{time}</strong>
                    <span>{event}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="warehouse-health" aria-label="Warehouse health indicators">
        {health.map(([metric, status, severity]) => (
          <div className={severity} key={metric}>
            <span>{metric}</span>
            <strong>{status}</strong>
          </div>
        ))}
      </section>

    </main>
  );
}

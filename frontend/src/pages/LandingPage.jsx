import "./UploadPage.css";
import "./ProductPages.css";

export default function LandingPage({ onNavigate = () => {} }) {
  return (
    <main className="landing-page">
      <section className="landing-hero">
        <nav className="landing-nav" aria-label="Primary">
          <div className="landing-brand">
            <div className="logo">OP</div>
            <span>OpsPilot AI</span>
          </div>
          <div className="landing-actions">
            <button className="text-btn" onClick={() => onNavigate("investigation")} type="button">
              View Investigation
            </button>
            <button className="solid-btn" onClick={() => onNavigate("dashboard")} type="button">
              Open Dashboard
            </button>
          </div>
        </nav>

        <div className="hero-copy">
          <p className="eyebrow">Autonomous warehouse operations agent system</p>
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
          </div>
        </div>
      </section>

      <section className="landing-proof">
        <div>
          <span>Daily readiness</span>
          <strong>01:00 status checks</strong>
        </div>
        <div>
          <span>Map intelligence</span>
          <strong>Rack-level validation</strong>
        </div>
        <div>
          <span>Incident response</span>
          <strong>Auto-routed tickets</strong>
        </div>
        <div>
          <span>Agent system</span>
          <strong>7 collaborating agents</strong>
        </div>
      </section>
    </main>
  );
}

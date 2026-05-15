import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./UploadPage.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const navItems = [
  { id: "map", label: "Warehouse Map" },
  { id: "analysis", label: "Package Recognition" },
  { id: "incident", label: "Incident Ticket" },
];

const initialTimeline = [
  "Awaiting damaged item photo",
  "Damage vision extraction pending",
  "SOP retrieval pending",
];

function severityClass(severity) {
  const level = String(severity || "").toLowerCase();
  if (level === "high") return "severity high";
  if (level === "medium") return "severity medium";
  if (level === "low") return "severity low";
  return "severity unknown";
}

function formatBytes(bytes) {
  if (!bytes) return "0 KB";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** index;
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatConfidence(confidence) {
  if (typeof confidence !== "number") return "Pending";
  const normalized = confidence > 1 ? confidence : confidence * 100;
  return `${Math.round(normalized)}%`;
}

function normalizeList(value, fallback = []) {
  if (Array.isArray(value)) return value.filter(Boolean);
  return fallback;
}

function formatContact(contact) {
  if (!contact) return "No contact returned.";
  return [contact.name, contact.position, contact.email, contact.phone].filter(Boolean).join(" · ");
}

export default function IncidentTicketPage({ activePage = "incident", onNavigate = () => {} }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState("checking");

  useEffect(() => {
    let isMounted = true;
    axios
      .get(`${API_BASE}/health/`, { timeout: 3000 })
      .then(() => {
        if (isMounted) setHealth("online");
      })
      .catch(() => {
        if (isMounted) setHealth("offline");
      });
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const uploadMeta = useMemo(() => {
    if (!file) return "PNG, JPG, or JPEG";
    return `${file.type || "image"} · ${formatBytes(file.size)}`;
  }, [file]);
  const timeline = result ? normalizeList(result.agent_trace, initialTimeline) : initialTimeline;
  const sopSteps = normalizeList(result?.sop_steps);
  const confidenceLabel = formatConfidence(result?.vision_confidence);
  const healthLabel = {
    checking: "Checking backend",
    online: "Backend online",
    offline: "Backend offline",
  }[health];

  const handleFileChange = (event) => {
    const selected = event.target.files?.[0];
    if (preview) URL.revokeObjectURL(preview);
    setFile(selected || null);
    setResult(null);
    setError("");
    setPreview(selected ? URL.createObjectURL(selected) : "");
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please choose a damaged item photo first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setError("");
      const response = await axios.post(`${API_BASE}/api/incident-ticket/create`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(response.data);
      setHealth("online");
    } catch (err) {
      console.error(err);
      setHealth("offline");
      setError("Incident ticket creation failed. Confirm the backend, Gemini key, MongoDB, and GCS are available.");
    } finally {
      setLoading(false);
    }
  };

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

      <main className="app-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">Damage Response Workflow</p>
            <h1>Incident ticket workspace</h1>
          </div>

          <div className={`status-pill ${health}`}>
            <span className="pulse" />
            {healthLabel}
          </div>
        </header>

        <section className="overview">
          <div>
            <span>Ticket</span>
            <strong>{result ? result.ticket_id?.slice(-8) || "Open" : "None"}</strong>
          </div>
          <div>
            <span>Severity</span>
            <strong>
              <span className={severityClass(result?.severity)}>{result?.severity || "N/A"}</span>
            </strong>
          </div>
          <div>
            <span>Item Type</span>
            <strong>{result?.item_type || "Pending"}</strong>
          </div>
          <div>
            <span>Vision Confidence</span>
            <strong>{confidenceLabel}</strong>
          </div>
        </section>

        <section className="workspace-grid">
          <div className="panel upload-panel">
            <div className="panel-heading">
              <div>
                <h2>Damaged Item Photo</h2>
                <p>Upload a photo so the incident ticket agent can detect damage and retrieve the right SOP.</p>
              </div>
              <span className="panel-token">{file ? "Ready" : "Waiting"}</span>
            </div>

            <label className={`drop-zone ${preview ? "has-preview" : ""}`}>
              <input type="file" accept="image/*" onChange={handleFileChange} />
              {preview ? (
                <img src={preview} alt="Damaged item preview" className="preview-img" />
              ) : (
                <div className="drop-placeholder">
                  <div className="upload-mark">IT</div>
                  <strong>Choose a damaged item photo</strong>
                  <span>{uploadMeta}</span>
                </div>
              )}
            </label>

            <div className="upload-footer">
              <div>
                <span>Selected file</span>
                <strong>{file?.name || "No file selected"}</strong>
                <small>{uploadMeta}</small>
              </div>
              <button className="primary-btn" onClick={handleUpload} disabled={loading} type="button">
                {loading ? "Creating" : "Create Ticket"}
              </button>
            </div>

            {loading && (
              <div className="agent-progress">
                <span />
                <div>
                  <strong>Incident Ticket Agent is reviewing the damage</strong>
                  <p>Vision, item lookup, SOP retrieval, and contact routing are running.</p>
                </div>
              </div>
            )}

            {error && <div className="error-box">{error}</div>}
          </div>

          <div className="panel summary-panel">
            <div className="panel-heading">
              <div>
                <h2>Ticket Summary</h2>
                <p>Damage classification and response guidance.</p>
              </div>
            </div>

            {result ? (
              <div className="summary-list">
                <div>
                  <span>Damage detected</span>
                  <strong>{[result.item_id, result.item_name].filter(Boolean).join(" ") || "Unidentified item"}</strong>
                </div>
                <div>
                  <span>Damage type</span>
                  <strong>{result.damage_type || "Not returned"}</strong>
                </div>
                <div>
                  <span>Damage summary</span>
                  <strong>{result.damage_summary || "No summary returned."}</strong>
                </div>
                <div>
                  <span>Recommended SOP</span>
                  <strong>{result.sop_title || "No SOP returned"}</strong>
                </div>
                <div>
                  <span>Contact</span>
                  <strong>{formatContact(result.responsible_contact)}</strong>
                </div>
              </div>
            ) : (
              <div className="empty-state">Upload a damaged item photo to create an incident ticket.</div>
            )}
          </div>
        </section>

        <section className="detail-grid">
          <div className="panel recommendation-panel">
            <div className="panel-heading">
              <div>
                <h2>Immediate SOP Steps</h2>
                <p>Retrieved from the SOP collection for the detected item type.</p>
              </div>
              <span className="panel-token">{sopSteps.length} steps</span>
            </div>

            {sopSteps.length ? (
              <div className="action-list">
                {sopSteps.map((step, index) => (
                  <div key={step}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    {step}
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">SOP steps will appear after ticket creation.</div>
            )}
          </div>

          <div className="panel analysis-panel">
            <div className="panel-heading">
              <div>
                <h2>Next Action</h2>
                <p>Agent recommendation for the worker.</p>
              </div>
            </div>
            <p className="recommendation-copy">
              {result?.next_action || "Create a ticket to generate the next action."}
            </p>
          </div>

          <div className="panel timeline-panel">
            <div className="panel-heading">
              <div>
                <h2>Agent Trace</h2>
                <p>Current response path.</p>
              </div>
            </div>
            <div className="timeline">
              {timeline.map((item) => (
                <div key={item}>
                  <span />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

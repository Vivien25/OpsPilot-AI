import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./UploadPage.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const navItems = ["Dashboard", "Incidents", "AI Analysis", "Historical Cases", "Settings"];
const actionStepsFallback = [
  "Review detected issue",
  "Compare historical cases",
  "Assign operator remediation",
];
const initialTimeline = ["Awaiting image", "AI analysis pending", "Memory lookup pending"];
const completeTimeline = [
  "Vision agent analyzed image",
  "Risk classifier detected severity",
  "Retrieval agent searched memory",
  "Recommendation agent generated next action",
];

function severityClass(severity) {
  if (severity === "high") return "severity high";
  if (severity === "medium") return "severity medium";
  if (severity === "low") return "severity low";
  return "severity unknown";
}

function cleanText(text) {
  if (!text) return "No analysis available.";
  return text.replace(/\*\*/g, "");
}

function extractRootCause(text) {
  if (!text) return "Potential operational process gap or incomplete staging workflow.";

  const cleaned = cleanText(text);
  const match = cleaned.match(/possible root cause[:\s]*([\s\S]*?)(recommended next action|next action|$)/i);
  return match ? match[1].trim() : "Potential operational process gap or incomplete staging workflow.";
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
  if (typeof value === "string" && value.trim()) return [value.trim()];
  return fallback;
}

function validationLabel(validation) {
  if (!validation) return "Not checked";
  return validation.is_valid ? "Valid" : "Needs review";
}

function zoneStatusLabel(isWrongZone) {
  if (isWrongZone === true) return "Wrong zone";
  if (isWrongZone === false) return "Correct zone";
  return "Unknown";
}

function formatContact(contact) {
  if (!contact) return "No contact returned.";

  const parts = [
    contact.name,
    contact.position,
    contact.email,
    contact.phone,
  ].filter(Boolean);

  return parts.length ? parts.join(" · ") : "Contact details unavailable.";
}

export default function UploadPage() {
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

  const similarIncidents = normalizeList(result?.similar_incidents);
  const historicalMatches = similarIncidents.length;
  const timeline = result ? normalizeList(result.agent_trace, completeTimeline) : initialTimeline;
  const actionSteps = normalizeList(result?.action_steps, actionStepsFallback);
  const confidenceLabel = formatConfidence(result?.confidence);
  const riskNotes = result?.risk || result?.risk_notes || "No additional risk notes returned.";
  const hasZoneResult = Boolean(
    result?.detected_item ||
    result?.detected_zone ||
    result?.expected_zone ||
    result?.responsible_contact ||
    typeof result?.is_wrong_zone === "boolean",
  );
  const validationSummary =
    result?.validation?.validation_summary ||
    (result?.validation ? "The report was checked by the validation agent." : "Validation has not run yet.");
  const healthLabel = {
    checking: "Checking backend",
    online: "Backend online",
    offline: "Backend offline",
  }[health];

  const uploadMeta = useMemo(() => {
    if (!file) return "PNG, JPG, or JPEG";
    return `${file.type || "image"} · ${formatBytes(file.size)}`;
  }, [file]);

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
      setError("Please choose an image first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setError("");

      const response = await axios.post(`${API_BASE}/api/analyze`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setResult(response.data);
      setHealth("online");
    } catch (err) {
      console.error(err);
      setHealth("offline");
      setError("Analysis failed. Confirm the backend, Gemini key, and MongoDB connection are available.");
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
            <button className={item === "Dashboard" ? "active" : ""} key={item} type="button">
              {item}
            </button>
          ))}
        </nav>
      </aside>

      <main className="app-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">AI Operations Command Center</p>
            <h1>Incident review workspace</h1>
          </div>

          <div className={`status-pill ${health}`}>
            <span className="pulse" />
            {healthLabel}
          </div>
        </header>

        <section className="overview">
          <div>
            <span>Active Incident</span>
            <strong>{result ? result.incident_id?.slice(-8) || "Open" : "None"}</strong>
          </div>
          <div>
            <span>Severity</span>
            <strong>
              <span className={severityClass(result?.severity)}>{result?.severity || "N/A"}</span>
            </strong>
          </div>
          <div>
            <span>Historical Matches</span>
            <strong>{historicalMatches}</strong>
          </div>
          <div>
            <span>AI Confidence</span>
            <strong>{confidenceLabel}</strong>
          </div>
        </section>

        <section className="workspace-grid">
          <div className="panel upload-panel">
            <div className="panel-heading">
              <div>
                <h2>Incident Image</h2>
                <p>Upload a warehouse or operations image for analysis.</p>
              </div>
              <span className="panel-token">{file ? "Ready" : "Waiting"}</span>
            </div>

            <label className={`drop-zone ${preview ? "has-preview" : ""}`}>
              <input type="file" accept="image/*" onChange={handleFileChange} />
              {preview ? (
                <img src={preview} alt="Uploaded incident preview" className="preview-img" />
              ) : (
                <div className="drop-placeholder">
                  <div className="upload-mark">UP</div>
                  <strong>Choose an incident image</strong>
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
                {loading ? "Analyzing" : "Analyze"}
              </button>
            </div>

            {loading && (
              <div className="agent-progress">
                <span />
                <div>
                  <strong>Agents are reviewing the image</strong>
                  <p>Vision, severity, memory, and recommendation steps are running.</p>
                </div>
              </div>
            )}

            {error && <div className="error-box">{error}</div>}
          </div>

          <div className="panel summary-panel">
            <div className="panel-heading">
              <div>
                <h2>Incident Summary</h2>
                <p>Operational classification from the latest run.</p>
              </div>
            </div>

            {result ? (
              <div className="summary-list">
                <div>
                  <span>Issue type</span>
                  <strong>{result.issue_type || "Unknown"}</strong>
                </div>
                <div>
                  <span>Severity</span>
                  <strong>
                    <span className={severityClass(result.severity)}>{result.severity || "unknown"}</span>
                  </strong>
                </div>
                <div>
                  <span>Root cause</span>
                  <strong>{result.root_cause || extractRootCause(result.vision_summary)}</strong>
                </div>
                <div>
                  <span>Detected item</span>
                  <strong>{result.item_id || result.detected_item || "Not returned"}</strong>
                </div>
                <div>
                  <span>Detected zone</span>
                  <strong>{result.detected_zone || "Not returned"}</strong>
                </div>
                <div>
                  <span>Expected zone</span>
                  <strong>{result.expected_zone || "Not returned"}</strong>
                </div>
                <div>
                  <span>Wrong zone</span>
                  <strong>{zoneStatusLabel(result.is_wrong_zone)}</strong>
                </div>
                <div>
                  <span>Responsible contact</span>
                  <strong>{formatContact(result.responsible_contact)}</strong>
                </div>
                <div>
                  <span>GCS image</span>
                  <strong>{result.image_gcs_uri || "Not stored"}</strong>
                </div>
              </div>
            ) : (
              <div className="empty-state">Upload an image to generate an incident report.</div>
            )}
          </div>
        </section>

        <section className="panel zone-panel">
          <div className="panel-heading">
            <div>
              <h2>Vision Observation</h2>
              <p>Facts extracted from the image before agent reasoning.</p>
            </div>
            <span className={`zone-badge ${result?.is_wrong_zone ? "wrong" : "ok"}`}>
              {zoneStatusLabel(result?.is_wrong_zone)}
            </span>
          </div>

          {result && hasZoneResult ? (
            <>
              <div className="zone-grid">
                <div>
                  <span>Detected item</span>
                  <strong>{result.item_id || result.detected_item || "Not detected"}</strong>
                </div>
                <div>
                  <span>Visible label</span>
                  <strong>{result.visible_label || "Not detected"}</strong>
                </div>
                <div>
                  <span>Item type</span>
                  <strong>{result.item_type || "Not detected"}</strong>
                </div>
                <div>
                  <span>Detected zone</span>
                  <strong>{result.detected_zone || "Not detected"}</strong>
                </div>
                <div>
                  <span>Expected zone</span>
                  <strong>{result.expected_zone || "Not found"}</strong>
                </div>
                <div>
                  <span>Wrong zone</span>
                  <strong>{zoneStatusLabel(result.is_wrong_zone)}</strong>
                </div>
                <div>
                  <span>Vision confidence</span>
                  <strong>{formatConfidence(result.vision_confidence)}</strong>
                </div>
              </div>

              <div className="contact-strip">
                <span>Visual evidence</span>
                <strong>{result.visual_evidence || result.vision_summary || "No visual evidence returned."}</strong>
              </div>

              <div className="contact-strip">
                <span>Agent reason</span>
                <strong>{result.reason || "No agent reason returned."}</strong>
              </div>

              <div className="contact-strip">
                <span>Responsible contact</span>
                <strong>{formatContact(result.responsible_contact)}</strong>
              </div>
            </>
          ) : (
            <div className="empty-state">
              No zone fields returned yet. Confirm the backend response includes detected_item, detected_zone,
              expected_zone, is_wrong_zone, responsible_contact, and recommendation.
            </div>
          )}
        </section>

        <section className="detail-grid">
          <div className="panel analysis-panel">
            <div className="panel-heading">
              <div>
                <h2>AI Operational Analysis</h2>
                <p>Concise reading from the vision model.</p>
              </div>
            </div>
            <pre>{cleanText(result?.vision_summary)}</pre>
          </div>

          <div className="panel timeline-panel">
            <div className="panel-heading">
              <div>
                <h2>Activity Timeline</h2>
                <p>Current review path.</p>
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

          <div className="panel recommendation-panel">
            <div className="panel-heading">
              <div>
                <h2>Recommended Action</h2>
                <p>Next operational move.</p>
              </div>
            </div>
            <p className="recommendation-copy">
              {result?.recommendation ||
                "Run an analysis to generate a recommendation from the incident context."}
            </p>
            <div className="action-list">
              {actionSteps.map((step, index) => (
                <div key={step}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  {step}
                </div>
              ))}
            </div>
          </div>

          <div className="panel validation-panel">
            <div className="panel-heading">
              <div>
                <h2>Validation</h2>
                <p>Completeness check from the validation agent.</p>
              </div>
              <span className={`validation-badge ${result?.validation?.is_valid ? "valid" : "review"}`}>
                {validationLabel(result?.validation)}
              </span>
            </div>
            <p className="recommendation-copy">{validationSummary}</p>
          </div>

          <div className="panel risk-panel">
            <div className="panel-heading">
              <div>
                <h2>Risk Notes</h2>
                <p>Operational risk returned by the recommendation agent.</p>
              </div>
            </div>
            <p className="recommendation-copy">{riskNotes}</p>
          </div>
        </section>

        <section className="panel history-panel">
          <div className="panel-heading">
            <div>
              <h2>Similar Historical Incidents</h2>
              <p>Retrieved from operational memory.</p>
            </div>
            <span className="panel-token">{historicalMatches} matches</span>
          </div>

          {historicalMatches ? (
            <div className="incident-list">
              {similarIncidents.map((incident, index) => (
                <article className="incident-item" key={`${incident.created_at || "incident"}-${index}`}>
                  <div className="incident-item-header">
                    <strong>{incident.issue_type || "Unknown issue"}</strong>
                    <span className={severityClass(incident.severity)}>
                      {incident.severity || "unknown"}
                    </span>
                  </div>

                  <p className="incident-date">
                    {incident.created_at ? new Date(incident.created_at).toLocaleString() : "No timestamp"}
                  </p>

                  <pre>{cleanText(incident.vision_summary)}</pre>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              No similar incidents found yet. Completed analyses will become memory for future reviews.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

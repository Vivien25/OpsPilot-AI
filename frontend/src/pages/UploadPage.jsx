import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./UploadPage.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const navItems = [
  { id: "map", label: "Warehouse Map" },
  { id: "analysis", label: "Package Recognition" },
];
const actionStepsFallback = [
  "Check visible package label",
  "Match against box master",
  "Route package to expected rack",
];
const initialTimeline = ["Awaiting package photo", "Vision label check pending", "Box master lookup pending"];
const completeTimeline = [
  "Gemini Vision checked the package label",
  "Box Master lookup matched package context",
  "Zone and contact context were retrieved",
  "Package Recognition Agent generated recommendation",
];

function severityClass(severity) {
  const level = String(severity || "").toLowerCase();
  if (level === "high") return "severity high";
  if (level === "medium") return "severity medium";
  if (level === "low") return "severity low";
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

export default function UploadPage({ activePage = "analysis", onNavigate = () => {} }) {
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
    result?.needs_manual_review ||
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

      const response = await axios.post(`${API_BASE}/api/package/recognize`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setResult(response.data);
      setHealth("online");
    } catch (err) {
      console.error(err);
      setHealth("offline");
      setError("Package recognition failed. Confirm the backend, Gemini key, and BigQuery connection are available.");
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
            <p className="eyebrow">AI Operations Command Center</p>
            <h1>Package recognition workspace</h1>
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
                <p>Upload a box photo so the package recognition agent can identify and route it.</p>
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
                  <strong>Package Recognition Agent is reviewing the photo</strong>
                  <p>Gemini Vision, box master lookup, and routing recommendation steps are running.</p>
                </div>
              </div>
            )}

            {error && <div className="error-box">{error}</div>}
          </div>

          <div className="panel summary-panel">
            <div className="panel-heading">
              <div>
                <h2>Package Summary</h2>
                <p>Recognition and routing result from the latest run.</p>
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
                  <strong>{result.box_id || result.item_id || result.detected_item || "Not observed"}</strong>
                </div>
                <div>
                  <span>Detected zone</span>
                  <strong>{result.detected_zone || "Not applicable"}</strong>
                </div>
                <div>
                  <span>Expected zone</span>
                  <strong>{result.expected_zone || "Unavailable until item is matched"}</strong>
                </div>
                <div>
                  <span>Expected rack</span>
                  <strong>{result.expected_rack || "Unavailable until package is matched"}</strong>
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
              <div className="empty-state">Upload a box photo to generate a package recognition report.</div>
            )}
          </div>
        </section>

        <section className="panel zone-panel">
          <div className="panel-heading">
            <div>
              <h2>Vision Observation</h2>
              <p>Facts extracted from the package photo before routing logic.</p>
            </div>
            <span className={`zone-badge ${result?.needs_manual_review ? "review" : result?.is_wrong_zone ? "wrong" : "ok"}`}>
              {result?.needs_manual_review ? "Manual review" : zoneStatusLabel(result?.is_wrong_zone)}
            </span>
          </div>

          {result && hasZoneResult ? (
            <>
              <div className="zone-grid">
                <div>
                  <span>Detected item</span>
                  <strong>{result.box_id || result.item_id || result.detected_item || "Not detected"}</strong>
                </div>
                <div>
                  <span>Visible label</span>
                  <strong>{result.visible_label || "Not detected"}</strong>
                </div>
                <div>
                  <span>Item type</span>
                  <strong>{result.package_type || result.item_type || "Not detected"}</strong>
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
                  <span>Expected rack</span>
                  <strong>{result.expected_rack || "Not found"}</strong>
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

              {result.needs_manual_review && (
                <div className="manual-review">
                  <span>Manual review needed</span>
                  <strong>
                    Retake the photo with the box label visible, or add a manual box ID entry step.
                  </strong>
                  <small>
                    Missing: {normalizeList(result.missing_observations).join(", ") || "required observations"}
                  </small>
                </div>
              )}

              <div className="contact-strip">
                <span>Responsible contact</span>
                <strong>{formatContact(result.responsible_contact)}</strong>
              </div>
            </>
          ) : (
            <div className="empty-state">
                No package fields returned yet. Confirm the backend response includes box_id, item_id,
              expected_zone, expected_rack, responsible_contact, and recommendation.
            </div>
          )}
        </section>

        <section className="detail-grid">
          <div className="panel analysis-panel">
            <div className="panel-heading">
              <div>
                <h2>Package Vision Analysis</h2>
                <p>Concise reading from Gemini Vision.</p>
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
                "Run package recognition to generate a routing recommendation."}
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
              <h2>Visual Match Candidates</h2>
              <p>Best guesses returned when the package label is missing.</p>
            </div>
            <span className="panel-token">{historicalMatches} matches</span>
          </div>

          {historicalMatches ? (
            <div className="incident-list">
              {similarIncidents.map((incident, index) => (
                <article className="incident-item" key={`${incident.box_id || incident.created_at || "candidate"}-${index}`}>
                  <div className="incident-item-header">
                    <strong>{incident.box_id || incident.item_id || incident.issue_type || "Unknown package"}</strong>
                    <span className={severityClass(incident.severity)}>
                      {incident.risk_level || incident.severity || "unknown"}
                    </span>
                  </div>

                  <p className="incident-date">
                    {[incident.item_name, incident.expected_zone, incident.expected_rack].filter(Boolean).join(" · ") ||
                      (incident.created_at ? new Date(incident.created_at).toLocaleString() : "No package context")}
                  </p>

                  <pre>{cleanText(incident.visual_description || incident.vision_summary || incident.box_description)}</pre>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              No visual match candidates returned. A clear package label is enough for direct box master lookup.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

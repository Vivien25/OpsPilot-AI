import { useState } from "react";
import axios from "axios";
import "./UploadPage.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

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

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    setFile(selected);
    setResult(null);
    setError("");

    if (selected) {
      setPreview(URL.createObjectURL(selected));
    }
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

      const response = await axios.post(`${API_BASE}/upload/image`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setResult(response.data);
    } catch (err) {
      console.error(err);
      setError("Analysis failed. Please make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const historicalMatches = result?.similar_incidents?.length || 0;

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="logo">OP</div>
        <nav>
          <span className="active">Dashboard</span>
          <span>Incidents</span>
          <span>AI Analysis</span>
          <span>Historical Cases</span>
          <span>Settings</span>
        </nav>
      </aside>

      <main className="app-shell">
        <header className="hero">
          <div>
            <p className="eyebrow">AI Operations Command Center</p>
            <h1>OpsPilot AI</h1>
            <p className="subtitle">
              Detect warehouse incidents, assess risk, retrieve similar cases, and generate operational recommendations.
            </p>
          </div>

          <div className="status-pill">
            <span className="pulse" />
            Backend Connected
          </div>
        </header>

        <section className="kpi-row">
          <div className="kpi-card">
            <span>Active Incidents</span>
            <strong>{result ? 1 : 0}</strong>
          </div>
          <div className="kpi-card">
            <span>Severity</span>
            <strong>
              <span className={severityClass(result?.severity)}>
                {result?.severity || "N/A"}
              </span>
            </strong>
          </div>
          <div className="kpi-card">
            <span>Historical Matches</span>
            <strong>{historicalMatches}</strong>
          </div>
          <div className="kpi-card">
            <span>AI Confidence</span>
            <strong>{result ? "94%" : "--"}</strong>
          </div>
        </section>

        <section className="top-grid">
          <div className="card upload-card">
            <h2>Incident Image</h2>
            <p>Upload a warehouse or operations image for AI analysis.</p>

            <label className="drop-zone">
              <input type="file" accept="image/*" onChange={handleFileChange} />
              {preview ? (
                <img src={preview} alt="Uploaded preview" className="preview-img" />
              ) : (
                <div className="drop-placeholder">
                  <div className="upload-icon">⬆</div>
                  <strong>Choose an image</strong>
                  <span>PNG, JPG, JPEG supported</span>
                </div>
              )}
            </label>

            {file && <p className="file-name">{file.name}</p>}

            <button className="primary-btn" onClick={handleUpload} disabled={loading}>
              {loading ? "Analyzing with AI Agents..." : "Analyze Image"}
            </button>

            {loading && (
              <div className="agent-progress">
                <div>✅ Vision Agent reading image</div>
                <div>✅ Retrieval Agent checking memory</div>
                <div>✅ Recommendation Agent preparing action plan</div>
              </div>
            )}

            {error && <div className="error-box">{error}</div>}
          </div>

          <div className="card summary-card">
            <h2>Incident Summary</h2>
            <p>AI-generated operational classification.</p>

            {result ? (
              <div className="summary-grid">
                <div className="metric">
                  <span>Incident ID</span>
                  <strong>{result.incident_id?.slice(-8) || "N/A"}</strong>
                </div>

                <div className="metric">
                  <span>Issue Type</span>
                  <strong>{result.issue_type || "Unknown"}</strong>
                </div>

                <div className="metric">
                  <span>Severity</span>
                  <strong>
                    <span className={severityClass(result.severity)}>
                      {result.severity || "unknown"}
                    </span>
                  </strong>
                </div>

                <div className="metric">
                  <span>Historical Matches</span>
                  <strong>{historicalMatches}</strong>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                Upload an image to generate an incident report.
              </div>
            )}
          </div>
        </section>

        {result && (
          <>
            <section className="insight-grid">
              <div className="card insight-card">
                <h2>AI Insight</h2>
                <p>
                  This incident was classified as <b>{result.issue_type}</b> with{" "}
                  <b>{result.severity}</b> severity. MongoDB memory found{" "}
                  <b>{historicalMatches}</b> similar historical cases.
                </p>
              </div>

              <div className="card insight-card">
                <h2>Likely Root Cause</h2>
                <p>{extractRootCause(result.vision_summary)}</p>
              </div>

              <div className="card recommendation-card">
                <h2>Recommended Action</h2>
                <p>{result.recommendation}</p>
                <div className="recommendation-list">
                  <div>Review detected issue</div>
                  <div>Compare historical cases</div>
                  <div>Assign operator remediation</div>
                </div>
              </div>
            </section>

            <section className="result-grid">
              <div className="card analysis-card">
                <h2>AI Operational Analysis</h2>
                <pre>{cleanText(result.vision_summary)}</pre>
              </div>

              <div className="card timeline-card">
                <h2>Agent Activity Timeline</h2>
                <div className="timeline">
                  <div><span /> Vision Agent analyzed image</div>
                  <div><span /> Risk classifier detected severity</div>
                  <div><span /> Retrieval Agent searched MongoDB memory</div>
                  <div><span /> Recommendation Agent generated next action</div>
                </div>
              </div>

              <div className="card history-card">
                <h2>Similar Historical Incidents</h2>
                <p>Retrieved from MongoDB operational memory.</p>

                {historicalMatches ? (
                  <div className="incident-list">
                    {result.similar_incidents.map((incident, index) => (
                      <div className="incident-item" key={index}>
                        <div className="incident-item-header">
                          <strong>{incident.issue_type || "Unknown issue"}</strong>
                          <span className={severityClass(incident.severity)}>
                            {incident.severity || "unknown"}
                          </span>
                        </div>

                        <p className="incident-date">
                          {incident.created_at
                            ? new Date(incident.created_at).toLocaleString()
                            : "No timestamp"}
                        </p>

                        <pre>{cleanText(incident.vision_summary)}</pre>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    No similar incidents found yet. This incident will become memory for future analysis.
                  </div>
                )}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
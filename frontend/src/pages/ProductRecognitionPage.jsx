import { useEffect, useState } from "react";
import axios from "axios";
import { productNavItems as navItems } from "../navigation";
import "./UploadPage.css";
import "./ProductRecognitionPage.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001";

const sampleRequest = {
  item_id: "CHEM-102",
  shipment_id: "IN-7782",
  detected_label: "Solvent Drum",
  detected_package_size: "55 gallon drum",
  detected_condition: "minor carton deformation",
  detected_zone: "Chemical Storage",
};

const fallbackResult = {
  decision: "Approve product intake",
  approved: true,
  image_result: {
    detected_label: "Solvent Drum",
    detected_package_size: "55 gallon drum",
    detected_condition: "minor carton deformation",
    detected_zone: "Chemical Storage",
    confidence: 0.94,
  },
  reference_data: {
    item_label: "Solvent Drum",
    expected_package_size: "55 gallon drum",
    product_description: "Flammable solvent used in production line cleaning.",
    shipment_info: "Inbound shipment #IN-7782 arriving at 3:00 PM",
    expected_zone: "Chemical Storage",
    responsible_contact: "Chemical Storage Supervisor",
  },
  checks: [
    { name: "Label correctness", status: "pass", detected: "Solvent Drum", expected: "Solvent Drum" },
    { name: "Package size", status: "pass", detected: "55 gallon drum", expected: "55 gallon drum" },
    { name: "Product condition", status: "pass", detected: "minor carton deformation", expected: "No damage, leakage, or abnormal signs" },
    { name: "Expected zone match", status: "pass", detected: "Chemical Storage", expected: "Chemical Storage" },
  ],
  exceptions: [],
  trace_spans: [
    "product_recognition_agent",
    "item_master_rag_lookup",
    "package_validation_agent",
    "label_validation_agent",
    "intake_approval_agent",
    "incident_agent",
  ],
};

const workflowSteps = [
  "3:00 PM shipment arrives",
  "Worker uploads product photo",
  "Product Recognition Agent analyzes image",
  "RAG checks item master data",
  "Validation Agent compares image vs reference",
  "Approve intake or create exception",
  "Notification Agent routes the outcome",
];

function checkClass(status) {
  return `recognition-check ${String(status || "pending").toLowerCase()}`;
}

export default function ProductRecognitionPage({ activePage = "product-recognition", onNavigate = () => {} }) {
  const [result, setResult] = useState(fallbackResult);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("sample-product-photo.jpg");
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl("");
      return undefined;
    }

    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedFile]);

  function handleFileChange(event) {
    const file = event.target.files?.[0] || null;
    setSelectedFile(file);
    setFileName(file?.name || "sample-product-photo.jpg");
  }

  function runAnalysis() {
    setLoading(true);

    const request = selectedFile
      ? (() => {
          const formData = new FormData();
          formData.append("image", selectedFile);
          formData.append("shipment_id", sampleRequest.shipment_id);
          return axios.post(`${API_BASE}/api/product-recognition/image`, formData, { timeout: 20000 });
        })()
      : axios.post(`${API_BASE}/api/product-recognition`, sampleRequest, { timeout: 8000 });

    request
      .then((response) => {
        setResult(response.data || fallbackResult);
        setError("");
      })
      .catch((err) => {
        console.error(err);
        setResult(fallbackResult);
        setError("Using demo result. Connect the backend to emit live Arize traces.");
      })
      .finally(() => setLoading(false));
  }

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

      <main className="app-shell product-recognition-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">Image + RAG Agent</p>
            <h1>Product Recognition Agent</h1>
          </div>
          <div className={`status-pill ${error ? "offline" : "online"}`}>
            <span className="pulse" />
            {loading ? "Analyzing product" : error ? "Demo mode" : "Ready for 3:00 PM intake"}
          </div>
        </header>

        <section className="recognition-hero panel">
          <div>
            <span className="panel-token">POST /api/product-recognition</span>
            <h2>Validate shipment photos before intake</h2>
            <p>
              Workers upload a product photo. OpsPilot checks label correctness, package size, condition, and expected zone
              against shipment and item-master data before approving intake or creating an incident.
            </p>
          </div>
          <div className="decision-card">
            <span>{result.approved ? "Approved" : "Exception"}</span>
            <strong>{result.decision}</strong>
            <small>{result.reference_data?.responsible_contact || "Responsible contact pending"}</small>
          </div>
        </section>

        {error && <div className="error-box">{error}</div>}

        <section className="recognition-grid">
          <div className="panel upload-panel">
            <div className="panel-heading">
              <div>
                <h2>Photo Intake</h2>
                <p>Upload or run the sample shipment photo.</p>
              </div>
              <span className="panel-token">3:00 PM arrival</span>
            </div>

            <label className="recognition-upload">
              <input
                accept="image/*"
                type="file"
                onChange={handleFileChange}
              />
              {previewUrl ? <img alt="Uploaded product preview" src={previewUrl} /> : <span>IMG</span>}
              <strong>{fileName}</strong>
              <small>{selectedFile ? "Selected image will be analyzed by the Product Recognition Agent." : "Image analysis feeds RAG validation and agent handoffs."}</small>
            </label>

            <div className="recognition-actions">
              <button className="solid-btn" disabled={loading} onClick={runAnalysis} type="button">
                {loading ? "Analyzing..." : "Analyze Product"}
              </button>
              <button
                className="text-btn"
                onClick={() => {
                  setSelectedFile(null);
                  setFileName("sample-product-photo.jpg");
                }}
                type="button"
              >
                Use Sample
              </button>
            </div>
          </div>

          <div className="panel rag-panel">
            <div className="panel-heading">
              <div>
                <h2>BigQuery Item Master + GCS Reference</h2>
                <p>Reference data and sample image retrieved for validation.</p>
              </div>
            </div>
            <div className="reference-list">
              <div><span>Item label</span><strong>{result.reference_data?.item_label}</strong></div>
              <div><span>Expected package size</span><strong>{result.reference_data?.expected_package_size}</strong></div>
              <div><span>Product description</span><strong>{result.reference_data?.product_description}</strong></div>
              <div><span>Shipment info</span><strong>{result.reference_data?.shipment_info}</strong></div>
              <div><span>Expected zone</span><strong>{result.reference_data?.expected_zone}</strong></div>
              {result.reference_data?.sample_image_gcs_uri && (
                <div><span>GCS reference image</span><strong>{result.reference_data.sample_image_gcs_uri}</strong></div>
              )}
              {result.image_result?.comparison_summary && (
                <div><span>Image comparison</span><strong>{result.image_result.comparison_summary}</strong></div>
              )}
            </div>
          </div>

          <div className="panel validation-panel">
            <div className="panel-heading">
              <div>
                <h2>Validation Agent</h2>
                <p>Image result compared with reference data.</p>
              </div>
            </div>
            <div className="recognition-checks">
              {result.checks?.map((check) => (
                <article className={checkClass(check.status)} key={check.name}>
                  <span />
                  <div>
                    <strong>{check.name}</strong>
                    <small>Detected: {check.detected}</small>
                    <small>Expected: {check.expected}</small>
                  </div>
                  <em>{check.status}</em>
                </article>
              ))}
            </div>
          </div>

          <div className="panel trace-panel">
            <div className="panel-heading">
              <div>
                <h2>Arize Trace</h2>
                <p>Expected span tree for the product-recognition endpoint.</p>
              </div>
            </div>
            <div className="trace-list">
              {result.trace_spans?.map((span) => <code key={span}>{span}</code>)}
            </div>
          </div>
        </section>

        <section className="panel workflow-panel recognition-workflow-panel">
          <div className="panel-heading">
            <div>
              <h2>Recommended Workflow</h2>
              <p>From arrival to approval, exception, and notification routing.</p>
            </div>
          </div>
          <div className="recognition-workflow">
            {workflowSteps.map((step, index) => (
              <div key={step}>
                <span>{index + 1}</span>
                <strong>{step}</strong>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

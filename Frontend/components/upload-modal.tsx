"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  uploadAndAnalyze,
  getSampleTemplates,
  UploadAnalysisResponse,
  SampleTemplate,
  AnalyzedTransaction,
  downloadTransactionPdf,
} from "../lib/api";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPlotOnGlobe?: (txs: AnalyzedTransaction[]) => void;
}

export function UploadModal({ isOpen, onClose, onPlotOnGlobe }: UploadModalProps) {
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [templates, setTemplates] = useState<SampleTemplate[]>([]);
  const [analysisResult, setAnalysisResult] = useState<UploadAnalysisResponse | null>(null);
  const [selectedPattern, setSelectedPattern] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [expandedTxid, setExpandedTxid] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      getSampleTemplates()
        .then((res) => setTemplates(res.templates || []))
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const processFile = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const text = await file.text();
      const res = await uploadAndAnalyze(file.name, text);
      setAnalysisResult(res);
    } catch (err: any) {
      setError(err?.message || "Failed to process and analyze file.");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleSelectTemplate = async (tmpl: SampleTemplate) => {
    setLoading(true);
    setError(null);
    try {
      const res = await uploadAndAnalyze(tmpl.filename, tmpl.content);
      setAnalysisResult(res);
    } catch (err: any) {
      setError(err?.message || "Failed to analyze template.");
    } finally {
      setLoading(false);
    }
  };

  const handleExportJson = () => {
    if (!analysisResult) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(analysisResult, null, 2));
    const dlAnchor = document.createElement("a");
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `analysis_${analysisResult.filename}.json`);
    dlAnchor.click();
  };

  const handlePlot = () => {
    if (analysisResult && onPlotOnGlobe) {
      onPlotOnGlobe(analysisResult.analysis.analyzed_transactions);
      onClose();
    }
  };

  // Filter transactions
  const txs = analysisResult?.analysis.analyzed_transactions || [];
  const filteredTxs = txs.filter((t) => {
    const matchesPattern =
      selectedPattern === "all" ||
      t.detected_pattern.toLowerCase().includes(selectedPattern.toLowerCase()) ||
      (selectedPattern === "anomaly" && t.is_anomaly);
    const matchesSearch =
      !searchQuery ||
      t.txid.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.explanation.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.src_country.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.dst_country.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesPattern && matchesSearch;
  });

  return (
    <div className="dataset-modal-backdrop" onClick={onClose}>
      <div
        className="dataset-modal upload-modal-container"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: "920px", maxHeight: "90vh" }}
      >
        <div className="dataset-modal-header">
          <div className="header-title-group">
            <span className="dataset-badge">UNIVERSAL INGESTION & AI SCORING</span>
            <h3>Upload Dataset & Run Forensic Analysis</h3>
          </div>
          <button className="dataset-modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="dataset-modal-body" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Top description & Sample Template quick-clicks */}
          <div className="upload-top-bar">
            <p style={{ margin: 0, fontSize: "12px", color: "var(--muted)" }}>
              Upload any raw transaction or telemetry file (<b>CSV, JSON, XML, TSV</b>). Our universal parser auto-normalizes the schema and executes the Module C AI/ML detection pipeline.
            </p>
            {templates.length > 0 && (
              <div className="sample-chips-row">
                <span style={{ fontSize: "11px", color: "var(--ink)", fontWeight: 600 }}>Quick Test Templates:</span>
                {templates.map((t) => (
                  <button
                    key={t.id}
                    className="template-chip-btn"
                    onClick={() => handleSelectTemplate(t)}
                    disabled={loading}
                  >
                    ⚡ {t.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Drag & Drop Zone */}
          <div
            className={`upload-dropzone ${dragActive ? "active" : ""}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json,.jsonl,.xml,.tsv,.txt"
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
            <div className="dropzone-content">
              <span style={{ fontSize: "28px" }}>📤</span>
              <p style={{ margin: "6px 0 2px", fontWeight: 700, color: "var(--ink)", fontSize: "13px" }}>
                Click to browse or drag & drop files here
              </p>
              <span style={{ fontSize: "11px", color: "var(--muted)" }}>
                Supports <b>.csv</b>, <b>.json</b>, <b>.xml</b>, <b>.tsv</b> (comma, semicolon, or tab delimited)
              </span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="upload-error-box">
              <span>⚠ <b>Analysis Failed:</b> {error}</span>
            </div>
          )}

          {/* Loading Indicator */}
          {loading && (
            <div className="upload-loading-box">
              <div className="spinner" />
              <span>Normalizing schema & executing AI/ML detection pipeline...</span>
            </div>
          )}

          {/* Analysis Dashboard Result */}
          {analysisResult && !loading && (
            <div className="analysis-dashboard">
              {/* Status banner */}
              <div className="analysis-header-banner">
                <div>
                  <span style={{ fontSize: "12px", color: "var(--cyan)", fontWeight: 700 }}>
                    FILE ANALYZED: {analysisResult.filename}
                  </span>
                  <span className="file-format-badge">{analysisResult.format}</span>
                  <span style={{ fontSize: "11px", color: "var(--muted)", marginLeft: "8px" }}>
                    {analysisResult.records_count} records processed
                  </span>
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button className="download-btn" onClick={handleExportJson}>
                    ⬇ Export JSON
                  </button>
                  <button
                    className="download-btn"
                    style={{ background: "rgba(255, 75, 75, 0.2)", borderColor: "rgba(255, 100, 100, 0.5)", color: "#ff8282" }}
                    onClick={() => {
                      if (filteredTxs.length > 0) {
                        downloadTransactionPdf(filteredTxs[0], `Forensic_Report_${filteredTxs[0].txid.slice(0, 10)}.pdf`);
                      }
                    }}
                    title="Generate and download Forensic PDF Dossier for the active transaction"
                  >
                    📄 Export Forensic PDF
                  </button>
                  {onPlotOnGlobe && (
                    <button
                      className="download-btn"
                      style={{ background: "rgba(0, 240, 255, 0.25)", borderColor: "var(--cyan)", color: "#fff" }}
                      onClick={handlePlot}
                    >
                      🌐 Plot on 3D Globe
                    </button>
                  )}
                </div>
              </div>

              {/* KPI Cards */}
              <div className="analysis-kpis-grid">
                <div className="analysis-kpi-card">
                  <span className="kpi-title">Total Records</span>
                  <span className="kpi-num">{analysisResult.analysis.total_records}</span>
                </div>
                <div className="analysis-kpi-card danger">
                  <span className="kpi-title">Anomalies Detected</span>
                  <span className="kpi-num">{analysisResult.analysis.anomalies_detected}</span>
                  <small style={{ color: "#ff6b6b" }}>
                    {Math.round((analysisResult.analysis.anomalies_detected / Math.max(1, analysisResult.analysis.total_records)) * 100)}% anomalous
                  </small>
                </div>
                <div className="analysis-kpi-card critical">
                  <span className="kpi-title">Critical Threats</span>
                  <span className="kpi-num">{analysisResult.analysis.critical_count}</span>
                  <small style={{ color: "#ff5267" }}>Score &ge; 0.80</small>
                </div>
                <div className="analysis-kpi-card">
                  <span className="kpi-title">Total BTC Volume</span>
                  <span className="kpi-num">{analysisResult.analysis.total_volume_btc.toFixed(2)}</span>
                  <small style={{ color: "var(--muted)" }}>BTC</small>
                </div>
                <div className="analysis-kpi-card">
                  <span className="kpi-title">Avg Risk Score</span>
                  <span className="kpi-num">{(analysisResult.analysis.avg_risk_score * 100).toFixed(0)}%</span>
                  <small style={{ color: "var(--muted)" }}>Composite</small>
                </div>
              </div>

              {/* Pattern breakdown pills */}
              <div className="pattern-tags-row">
                <span style={{ fontSize: "11px", color: "var(--muted)", fontWeight: 600 }}>Detected Topologies:</span>
                {Object.entries(analysisResult.analysis.pattern_distribution).map(([pat, count]) => (
                  <span
                    key={pat}
                    className={`pattern-pill ${pat.toLowerCase().includes("peel") ? "peeling" : pat.toLowerCase().includes("coinjoin") ? "coinjoin" : pat.toLowerCase().includes("smurf") ? "smurfing" : pat.toLowerCase().includes("tor") ? "tor" : "normal"}`}
                    style={{ cursor: "pointer" }}
                    onClick={() => setSelectedPattern(pat)}
                  >
                    {pat.replace(/_/g, " ")}: <b>{count}</b>
                  </span>
                ))}
              </div>

              {/* Filter and Search Bar */}
              <div className="table-controls-bar">
                <input
                  type="text"
                  placeholder="Search TxID, address, country, explanation..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="training-select"
                  style={{ flex: 1, padding: "6px 10px" }}
                />
                <select
                  value={selectedPattern}
                  onChange={(e) => setSelectedPattern(e.target.value)}
                  className="training-select"
                  style={{ padding: "6px 10px" }}
                >
                  <option value="all">All Patterns &amp; Normal</option>
                  <option value="anomaly">Anomalies Only</option>
                  <option value="peeling_chain">Peeling Chain</option>
                  <option value="coinjoin_mixing">CoinJoin Mixer</option>
                  <option value="smurfing_consolidation">Smurfing Consolidation</option>
                  <option value="tor_relay">Tor Onion Relay</option>
                  <option value="high_volume_whale">High-Volume Whale</option>
                  <option value="normal">Normal</option>
                </select>
              </div>

              {/* Analyzed Transactions Table */}
              <div className="training-table-container" style={{ maxHeight: "300px" }}>
                <table className="modal-table">
                  <thead>
                    <tr>
                      <th>TxID</th>
                      <th>Route</th>
                      <th>Amount (BTC)</th>
                      <th>Risk Score</th>
                      <th>Pattern</th>
                      <th>Forensic Attribution</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTxs.length > 0 ? (
                      filteredTxs.map((t) => {
                        const isExpanded = expandedTxid === t.txid;
                        return (
                          <React.Fragment key={t.txid}>
                            <tr>
                              <td>
                                <code style={{ color: "var(--cyan)", fontSize: "10px" }} title={t.txid}>
                                  {t.txid.slice(0, 14)}…
                                </code>
                              </td>
                              <td style={{ fontSize: "11px", fontWeight: 600 }}>
                                {t.src_country} → {t.dst_country}
                              </td>
                              <td style={{ fontSize: "11px", fontFamily: "monospace" }}>
                                {t.amount_btc.toFixed(4)}
                              </td>
                              <td>
                                <span
                                  className={`pill ${t.risk_score >= 0.8 ? "high" : t.risk_score >= 0.65 ? "high" : t.risk_score >= 0.4 ? "medium" : "low"}`}
                                  style={{ fontSize: "10px", padding: "2px 7px" }}
                                >
                                  {(t.risk_score * 100).toFixed(0)}% {t.risk_level}
                                </span>
                              </td>
                              <td>
                                <span
                                  className={`pattern-pill ${t.detected_pattern.toLowerCase().includes("peel") ? "peeling" : t.detected_pattern.toLowerCase().includes("coinjoin") ? "coinjoin" : t.detected_pattern.toLowerCase().includes("smurf") ? "smurfing" : t.detected_pattern.toLowerCase().includes("tor") ? "tor" : "normal"}`}
                                >
                                  {t.detected_pattern.replace(/_/g, " ")}
                                </span>
                              </td>
                              <td style={{ fontSize: "10px", color: "var(--muted)", maxWidth: "260px" }}>
                                {t.explanation}
                              </td>
                              <td>
                                <div style={{ display: "flex", gap: "4px" }}>
                                  <button
                                    className="inspect-toggle-btn"
                                    onClick={() => setExpandedTxid(isExpanded ? null : t.txid)}
                                  >
                                    {isExpanded ? "Close" : "Inspect"}
                                  </button>
                                  <button
                                    className="inspect-toggle-btn"
                                    style={{ background: "rgba(255, 75, 75, 0.15)", borderColor: "#ff4b4b", color: "#ff8282" }}
                                    title="Download Forensic PDF Report for this transaction"
                                    onClick={() => downloadTransactionPdf(t, `Forensic_Report_${t.txid.slice(0, 10)}.pdf`)}
                                  >
                                    📄 PDF
                                  </button>
                                </div>
                              </td>
                            </tr>
                            {isExpanded && (
                              <tr className="expanded-row" key={`${t.txid}_exp`}>
                                <td colSpan={7}>
                                  <div className="raw-json-box">
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                                      <span style={{ fontSize: "10px", color: "var(--muted)" }}>
                                        Extracted Forensic Features &amp; Addresses
                                      </span>
                                      <span style={{ fontSize: "10px", color: t.is_anomaly ? "#ff6b6b" : "#48f2a0" }}>
                                        ML Isolation Forest + AE Score: <b>{(t.ml_anomaly_score * 100).toFixed(1)}%</b>
                                      </span>
                                    </div>
                                    <pre style={{ margin: 0, fontSize: "10px", color: "#e2e8f0", overflowX: "auto" }}>
                                      {JSON.stringify(t, null, 2)}
                                    </pre>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={7} style={{ textAlign: "center", padding: "20px", color: "var(--muted)" }}>
                          No transactions match the selected filter.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

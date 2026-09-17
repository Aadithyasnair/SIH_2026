"use client";

import { useState, useEffect } from "react";
import { getTrainingSamples, TrainingSampleItem, TrainingSamplesResponse } from "@/lib/api";

interface DatasetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DatasetModal({ isOpen, onClose }: DatasetModalProps) {
  const [activeTab, setActiveTab] = useState<"training" | "summary" | "realtime" | "benchmark" | "entities" | "ml">("training");
  const [copied, setCopied] = useState(false);
  const [samplesData, setSamplesData] = useState<TrainingSamplesResponse | null>(null);
  const [selectedPattern, setSelectedPattern] = useState<string>("all");
  const [expandedTxid, setExpandedTxid] = useState<string | null>(null);
  const [loadingSamples, setLoadingSamples] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setLoadingSamples(true);
    getTrainingSamples(selectedPattern, 50)
      .then((data) => {
        setSamplesData(data);
      })
      .catch((e) => {
        console.error("Failed to load training samples:", e);
      })
      .finally(() => {
        setLoadingSamples(false);
      });
  }, [isOpen, selectedPattern]);

  if (!isOpen) return null;

  const handleCopySummary = () => {
    const summaryText = `SIH26146 Dataset Architecture Summary:
1. Physical Training & Benchmark Data: 5,000+ P2P network telemetry events, 3,000+ blockchain transactions with 360 injected ground-truth anomalies (Peeling Chains, CoinJoin/mixing, Smurfing, Rapid IP bursts, Tor exit routing) located at shared/sample_data/.
2. Live Bitcoin Mainnet Telemetry: Direct Port 8333 P2P wire handshakes across 8+ global nodes (US, Germany, Finland, UK, Netherlands, Canada, Australia) + Blockchain.com WebSocket mempool stream.
3. Entity Intelligence: Curated database of major exchange clusters (Coinbase, Binance, Bitfinex, Kraken, Robinhood, Mining pools) + Blockstream live on-chain history inspection.
4. ML Performance: 28 engineered graph & temporal features, Isolation Forest ensemble, 1.0000 Recall on ground-truth anomalies at 0.5 decision threshold.`;
    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleDownload = (fileKey: string) => {
    window.open(`/api/dataset/download/${fileKey}`, "_blank");
  };

  return (
    <div className="dataset-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="dataset-modal-card glass" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "22px" }}>📁</span>
            <div>
              <h2 style={{ margin: 0, fontSize: "17px", color: "var(--ink)" }}>Dataset & Training Data Inspector</h2>
              <p style={{ margin: "2px 0 0", fontSize: "11px", color: "var(--muted)" }}>
                Authoritative physical training records, benchmark provenance, and live ML verification metrics.
              </p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button className="copy-btn" onClick={handleCopySummary} title="Copy executive summary for presentation">
              {copied ? "✓ Copied!" : "📋 Copy Summary"}
            </button>
            <button className="close-btn" onClick={onClose} aria-label="Close modal">
              ×
            </button>
          </div>
        </div>

        <nav className="modal-tabs">
          <button
            className={`modal-tab ${activeTab === "training" ? "active" : ""}`}
            onClick={() => setActiveTab("training")}
          >
            📁 Physical Training Data
          </button>
          <button
            className={`modal-tab ${activeTab === "summary" ? "active" : ""}`}
            onClick={() => setActiveTab("summary")}
          >
            📊 Architecture Overview
          </button>
          <button
            className={`modal-tab ${activeTab === "realtime" ? "active" : ""}`}
            onClick={() => setActiveTab("realtime")}
          >
            🔴 Live Mainnet P2P
          </button>
          <button
            className={`modal-tab ${activeTab === "benchmark" ? "active" : ""}`}
            onClick={() => setActiveTab("benchmark")}
          >
            ⚡ Anomaly Benchmark
          </button>
          <button
            className={`modal-tab ${activeTab === "entities" ? "active" : ""}`}
            onClick={() => setActiveTab("entities")}
          >
            🏛 Entity Intelligence
          </button>
          <button
            className={`modal-tab ${activeTab === "ml" ? "active" : ""}`}
            onClick={() => setActiveTab("ml")}
          >
            🧠 ML Features & Metrics
          </button>
        </nav>

        <div className="modal-body">
          {activeTab === "training" && (
            <div className="tab-pane">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px", marginBottom: "12px" }}>
                <div>
                  <h4 style={{ margin: "0 0 4px", color: "var(--ink)" }}>Physical Training Datasets & Files on Disk</h4>
                  <p style={{ margin: 0, fontSize: "11px", color: "var(--muted)" }}>
                    Inspect real training rows, download physical JSON files, and review ground-truth topology annotations.
                  </p>
                </div>
                <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                  <button className="download-btn" onClick={() => handleDownload("blockchain_txns")} title="Download blockchain_txns.json">
                    ⬇ Transactions (JSON)
                  </button>
                  <button className="download-btn" onClick={() => handleDownload("labels")} title="Download labels.json">
                    ⬇ Labels (JSON)
                  </button>
                  <button className="download-btn" onClick={() => handleDownload("network_events")} title="Download network_events.json">
                    ⬇ P2P Events (JSON)
                  </button>
                  <button className="download-btn" onClick={() => handleDownload("evaluation_report")} title="Download evaluation_report.md">
                    ⬇ ML Report (MD)
                  </button>
                </div>
              </div>

              {/* Physical Repo File Paths */}
              <div className="repo-paths-box">
                <div className="repo-path-row">
                  <span className="repo-path-tag">TRANSACTIONS</span>
                  <code>shared/sample_data/blockchain_txns.json</code>
                  <span className="repo-path-desc">3,000 multi-input/output transactions</span>
                </div>
                <div className="repo-path-row">
                  <span className="repo-path-tag">LABELS</span>
                  <code>shared/sample_data/labels.json</code>
                  <span className="repo-path-desc">360 ground-truth injected money laundering anomalies</span>
                </div>
                <div className="repo-path-row">
                  <span className="repo-path-tag">NETWORK</span>
                  <code>shared/sample_data/network_events.json</code>
                  <span className="repo-path-desc">5,000 P2P network telemetry records (Port 8333 / 9050)</span>
                </div>
                <div className="repo-path-row">
                  <span className="repo-path-tag">ML MODEL</span>
                  <code>ml_detection/models/isolation_forest.joblib</code>
                  <span className="repo-path-desc">150-tree Isolation Forest + winsorized calibration</span>
                </div>
              </div>

              {/* Filter bar */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "14px 0 8px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "11px", color: "var(--muted)", fontWeight: 700 }}>Filter by Topology:</span>
                  <select
                    value={selectedPattern}
                    onChange={(e) => setSelectedPattern(e.target.value)}
                    className="training-select"
                  >
                    <option value="all">All Topologies ({samplesData?.total_records_in_dataset || 2000})</option>
                    <option value="peeling_chain">Peeling Chain (5 Hops)</option>
                    <option value="coinjoin_mixing">CoinJoin / Mixing Pool</option>
                    <option value="smurfing_consolidation">Smurfing / Structuring</option>
                    <option value="rapid_ip_burst">Rapid IP Burst (Sybil)</option>
                    <option value="tor_exit_relay">Tor Onion Relay</option>
                    <option value="normal">Normal Benign Transactions</option>
                  </select>
                </div>
                <span style={{ fontSize: "11px", color: "var(--cyan)" }}>
                  Showing {samplesData?.samples.length || 0} sample rows
                </span>
              </div>

              {/* Interactive Training Samples Table */}
              <div className="table-scroll" style={{ maxHeight: "310px" }}>
                <table className="modal-table">
                  <thead>
                    <tr>
                      <th>TXID</th>
                      <th>Ground-Truth Topology</th>
                      <th>BTC Amount</th>
                      <th>Inputs / Outputs</th>
                      <th>Script</th>
                      <th>Inspect</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loadingSamples ? (
                      <tr>
                        <td colSpan={6} style={{ textAlign: "center", padding: "20px", color: "var(--muted)" }}>
                          Loading physical training records from disk...
                        </td>
                      </tr>
                    ) : samplesData && samplesData.samples.length > 0 ? (
                      samplesData.samples.map((s) => {
                        const isExpanded = expandedTxid === s.txid;
                        const patBadge =
                          s.pattern === "peeling_chain"
                            ? "badge-peeling"
                            : s.pattern === "coinjoin_mixing"
                            ? "badge-coinjoin"
                            : s.pattern === "smurfing_consolidation"
                            ? "badge-smurf"
                            : s.pattern === "rapid_ip_burst"
                            ? "badge-burst"
                            : s.pattern === "tor_exit_relay"
                            ? "badge-tor"
                            : "badge-normal";

                        return (
                          <>
                            <tr key={s.txid} className="training-row">
                              <td>
                                <code style={{ color: "var(--ink)", fontWeight: 700 }}>
                                  {s.txid.slice(0, 10)}…{s.txid.slice(-6)}
                                </code>
                              </td>
                              <td>
                                <span className={`pattern-pill ${patBadge}`}>
                                  {s.pattern.replace(/_/g, " ")}
                                </span>
                              </td>
                              <td style={{ color: "#48f2a0", fontWeight: 700 }}>
                                {s.total_btc.toFixed(4)} BTC
                              </td>
                              <td>
                                {s.input_count} in → {s.output_count} out
                              </td>
                              <td>
                                <code style={{ fontSize: "9px" }}>{s.script_type}</code>
                              </td>
                              <td>
                                <button
                                  className="inspect-toggle-btn"
                                  onClick={() => setExpandedTxid(isExpanded ? null : s.txid)}
                                >
                                  {isExpanded ? "▲ Hide" : "▼ Raw JSON"}
                                </button>
                              </td>
                            </tr>
                            {isExpanded && (
                              <tr className="expanded-row" key={`${s.txid}_expanded`}>
                                <td colSpan={6}>
                                  <div className="raw-json-box">
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                                      <span style={{ fontSize: "10px", color: "var(--muted)" }}>
                                        Raw Record from <code>shared/sample_data/blockchain_txns.json</code>
                                      </span>
                                      <span style={{ fontSize: "10px", color: s.is_anomaly ? "#ff6b6b" : "#48f2a0" }}>
                                        Label: <b>{s.pattern}</b> ({s.is_anomaly ? "ANOMALOUS" : "BENIGN"})
                                      </span>
                                    </div>
                                    <pre style={{ margin: 0, fontSize: "10px", color: "#e2e8f0", overflowX: "auto" }}>
                                      {JSON.stringify(s, null, 2)}
                                    </pre>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={6} style={{ textAlign: "center", padding: "20px", color: "var(--muted)" }}>
                          No records match the selected pattern filter.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "summary" && (
            <div className="tab-pane">
              <div className="dataset-grid">
                <div className="dataset-kpi-card">
                  <span className="dataset-kpi-val">Live Wire</span>
                  <span className="dataset-kpi-lbl">Bitcoin Mainnet Port 8333</span>
                  <p>Real-time P2P INV telemetry across 8+ countries + Blockchain.com WebSocket mempool feed.</p>
                </div>
                <div className="dataset-kpi-card">
                  <span className="dataset-kpi-val">5,000+</span>
                  <span className="dataset-kpi-lbl">Network Telemetry Events</span>
                  <p>Standardized P2P network records conforming to <code>NetworkEvent</code> schema.</p>
                </div>
                <div className="dataset-kpi-card">
                  <span className="dataset-kpi-val">3,000+</span>
                  <span className="dataset-kpi-lbl">Blockchain Transactions</span>
                  <p>Multi-input / multi-output UTXO transactions with realistic fee profiles.</p>
                </div>
                <div className="dataset-kpi-card">
                  <span className="dataset-kpi-val">360</span>
                  <span className="dataset-kpi-lbl">Ground-Truth Anomalies</span>
                  <p>Peeling chains, CoinJoin mixers, smurfing structures, rapid IP bursts, and Tor routing.</p>
                </div>
              </div>

              <h4 style={{ margin: "16px 0 8px", color: "var(--ink)" }}>Operating Modes Available:</h4>
              <div className="modes-overview">
                <div className="mode-desc-box">
                  <b>📊 Batch Mode:</b> Historical static evaluation over ground-truth peeling chains and entity clusters from <code>alerts.json</code> and <code>clusters.json</code>.
                </div>
                <div className="mode-desc-box">
                  <b>⚡ Simulation Mode:</b> Dynamic replay of high-throughput P2P packet streams from Module A (<code>network_events.json</code>) with Sybil burst and smurf indicators.
                </div>
                <div className="mode-desc-box">
                  <b>🔴 Live Real Data Mode:</b> Instant streaming from the global Bitcoin mempool, estimating source country via multi-vantage propagation timing and destination country via entity intelligence.
                </div>
              </div>
            </div>
          )}

          {activeTab === "realtime" && (
            <div className="tab-pane">
              <h4 style={{ margin: "0 0 8px", color: "var(--ink)" }}>Real-World Bitcoin Mainnet P2P Telemetry</h4>
              <p style={{ fontSize: "12px", color: "var(--muted)", marginBottom: "14px" }}>
                Unlike demonstration mocks that generate synthetic random strings, Live Real Data Mode opens active TCP sockets to genuine Bitcoin Core listening nodes across the world on port 8333.
              </p>

              <div className="code-spec-box">
                <div className="spec-row">
                  <b>Protocol Handshake:</b>
                  <span>Bitcoin Mainnet magic bytes (<code>0xf9beb4d9</code>), version 70015, relay=True</span>
                </div>
                <div className="spec-row">
                  <b>Node Discovery:</b>
                  <span>DNS Seeds: <code>seed.bitcoin.sipa.be</code>, <code>dnsseed.bluematt.me</code>, <code>seed.bitcoinstats.com</code></span>
                </div>
                <div className="spec-row">
                  <b>Vantage Node Locations:</b>
                  <span>🇺🇸 US (East/Central), 🇩🇪 Germany (Hetzner), 🇫🇮 Finland (Helsinki), 🇬🇧 UK (London), 🇳🇱 Netherlands, 🇦🇺 Australia, 🇨🇦 Canada</span>
                </div>
                <div className="spec-row">
                  <b>Live Mempool Streaming:</b>
                  <span>Blockchain.com real-time WebSocket (<code>wss://ws.blockchain.info/inv</code>) with fallback to Blockstream API</span>
                </div>
                <div className="spec-row">
                  <b>Source Country Math:</b>
                  <span>Earliest <code>inv</code> arrival latency delta with confidence scoring: C = Base + Gap + Nodes</span>
                </div>
              </div>

              <h4 style={{ margin: "14px 0 6px", color: "var(--ink)" }}>Origin Confidence Formula</h4>
              <div className="math-box">
                <code>C = Base(0.20) + Gap_Score(0.15 - 0.45) + Node_Count_Weight(min(0.35, N * 0.08))</code>
                <p style={{ fontSize: "11px", color: "var(--muted)", margin: "4px 0 0" }}>
                  A clear gap (&gt;100ms) between the 1st and 2nd observing nodes indicates proximity to the origin relay node; ambiguity (&lt;25ms) lowers confidence defensibly.
                </p>
              </div>
            </div>
          )}

          {activeTab === "benchmark" && (
            <div className="tab-pane">
              <h4 style={{ margin: "0 0 8px", color: "var(--ink)" }}>Ground-Truth Injected Anomaly Benchmark</h4>
              <p style={{ fontSize: "12px", color: "var(--muted)", marginBottom: "12px" }}>
                Conforms strictly to official data contracts in <code>shared/schemas/records.py</code>. Contains 360 injected ground-truth anomalies representing classic money laundering topologies:
              </p>

              <table className="modal-table">
                <thead>
                  <tr>
                    <th>Topology</th>
                    <th>Count</th>
                    <th>Behavioral Pattern Description</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><b>Peeling Chain</b></td>
                    <td>120 txs</td>
                    <td>5-hop sequential forwarding. Small amounts peeled off to change addresses while forwarding bulk funds.</td>
                  </tr>
                  <tr>
                    <td><b>CoinJoin / Mixing</b></td>
                    <td>80 txs</td>
                    <td>Multi-party transaction with 5 equal input amounts (1.0 BTC) and 5 equal output amounts (0.999 BTC) breaking UTXO lineage.</td>
                  </tr>
                  <tr>
                    <td><b>Smurfing / Consolidation</b></td>
                    <td>60 txs</td>
                    <td>10-sender fan-in followed by rapid single-destination sweep consolidation into a target wallet.</td>
                  </tr>
                  <tr>
                    <td><b>Rapid IP Burst (Sybil)</b></td>
                    <td>50 events</td>
                    <td>Single peer IP broadcasting transactions for 6+ distinct wallets within a 5-second window.</td>
                  </tr>
                  <tr>
                    <td><b>Tor Onion Relay</b></td>
                    <td>50 events</td>
                    <td>Port 9050 P2P packets originating from Tor exit routers with darknet market nexus.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "entities" && (
            <div className="tab-pane">
              <h4 style={{ margin: "0 0 8px", color: "var(--ink)" }}>Entity Intelligence & Destination Resolution</h4>
              <p style={{ fontSize: "12px", color: "var(--muted)", marginBottom: "12px" }}>
                Outputs are resolved using a two-tier identification pipeline combining exact-match cluster databases and live on-chain history inspection:
              </p>

              <div className="entity-cards-grid">
                <div className="entity-mini-card">
                  <b>Coinbase Prime Custody</b>
                  <span>Region: United States</span>
                  <code>bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh</code>
                </div>
                <div className="entity-mini-card">
                  <b>Binance Cold Storage</b>
                  <span>Region: Cayman Islands</span>
                  <code>34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo</code>
                </div>
                <div className="entity-mini-card">
                  <b>Bitfinex Cold Storage</b>
                  <span>Region: British Virgin Islands</span>
                  <code>bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv...</code>
                </div>
                <div className="entity-mini-card">
                  <b>Kraken Exchange</b>
                  <span>Region: United States</span>
                  <code>bc1qjasf9z3gah8fwdyt722umfvcr2phnk4w3jhx0p</code>
                </div>
                <div className="entity-mini-card">
                  <b>Robinhood Crypto Custody</b>
                  <span>Region: United States</span>
                  <code>1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ</code>
                </div>
                <div className="entity-mini-card">
                  <b>Foundry USA Mining Pool</b>
                  <span>Region: United States</span>
                  <code>bc1q7cyrfmck2ffu2ud3rn5l5a8yv6f0chkp0zpemf</code>
                </div>
              </div>

              <div className="callout-card" style={{ marginTop: "12px" }}>
                <b>Live On-Chain Profiling:</b> Unlabeled addresses are checked via Blockstream API for <code>tx_count</code> and <code>funded_txo_sum</code>. High volume (&gt;10,000 txs) classifies as Custodial Hot Wallet, moderate volume (&gt;150 txs) as Payment Gateway, and low volume as Non-Custodial Personal Wallet.
              </div>
            </div>
          )}

          {activeTab === "ml" && (
            <div className="tab-pane">
              <h4 style={{ margin: "0 0 8px", color: "var(--ink)" }}>Machine Learning Validation & Metrics</h4>
              <p style={{ fontSize: "12px", color: "var(--muted)", marginBottom: "12px" }}>
                Evaluated against 3,000 ground-truth transactions using an unsupervised dual-model ensemble (Isolation Forest with 150 trees + robust winsorized calibration):
              </p>

              <table className="modal-table">
                <thead>
                  <tr>
                    <th>Decision Threshold</th>
                    <th>True Positives</th>
                    <th>False Positives</th>
                    <th>False Negatives</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1-Score</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>0.30</td>
                    <td>360</td>
                    <td>2,640</td>
                    <td>0</td>
                    <td>0.1200</td>
                    <td><b>1.0000</b></td>
                    <td>0.2143</td>
                  </tr>
                  <tr style={{ background: "rgba(0, 240, 255, 0.08)", fontWeight: 700 }}>
                    <td>0.50 (Primary)</td>
                    <td>360</td>
                    <td>1,537</td>
                    <td>0</td>
                    <td>0.1898</td>
                    <td><b>1.0000</b></td>
                    <td>0.3190</td>
                  </tr>
                  <tr>
                    <td>0.70</td>
                    <td>291</td>
                    <td>197</td>
                    <td>69</td>
                    <td>0.5963</td>
                    <td>0.8083</td>
                    <td>0.6863</td>
                  </tr>
                </tbody>
              </table>

              <div className="dataset-grid" style={{ marginTop: "14px" }}>
                <div className="dataset-kpi-card">
                  <span className="dataset-kpi-val" style={{ color: "#48f2a0" }}>100%</span>
                  <span className="dataset-kpi-lbl">Recall on Injected Money Laundering</span>
                  <p>Zero false negatives (FN = 0) across all peeling chains and CoinJoin mixers.</p>
                </div>
                <div className="dataset-kpi-card">
                  <span className="dataset-kpi-val" style={{ color: "var(--cyan)" }}>+0.2917</span>
                  <span className="dataset-kpi-lbl">Mean Anomaly Score Separation (Δ)</span>
                  <p>Mean anomaly score = 0.8225 vs Normal = 0.5309.</p>
                </div>
                <div className="dataset-kpi-card">
                  <span className="dataset-kpi-val">28</span>
                  <span className="dataset-kpi-lbl">Engineered Features</span>
                  <p>Structural, graph topological, temporal latency, and transport features.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

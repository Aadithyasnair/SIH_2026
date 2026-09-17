"use client";

import { RealtimeAnalysis, downloadTransactionPdf } from "@/lib/api";
import { getRisk, getRiskColor } from "@/lib/data";

interface RealtimeCardPanelProps {
  analysis: RealtimeAnalysis;
  onClose: () => void;
}

export function RealtimeCardPanel({ analysis, onClose }: RealtimeCardPanelProps) {
  const risk = Math.round(analysis.risk_score * 100);
  const color = getRiskColor(analysis.risk_score);
  const shortTxid = analysis.txid.length > 20 ? `${analysis.txid.slice(0, 10)}…${analysis.txid.slice(-8)}` : analysis.txid;

  return (
    <aside className="detail glass realtime-card-panel">
      <button onClick={onClose} aria-label="Close panel" className="detail-close-btn">
        ×
      </button>

      <div className="panel-header-section">
        <div style={{ display: "flex", gap: "6px", alignItems: "center", marginBottom: "8px" }}>
          <span className="pill" style={{ background: "rgba(255, 75, 75, 0.2)", borderColor: "#ff4b4b", color: "#ff8282" }}>
            ● LIVE MAINNET WIRE
          </span>
          <span className="pill" style={{ background: "rgba(0, 240, 255, 0.15)", borderColor: "var(--cyan)", color: "var(--cyan)" }}>
            Port 8333 P2P
          </span>
        </div>

        <div
          className="risk-ring"
          style={{
            "--score": `${risk * 3.6}deg`,
            "--risk-color": color,
          } as React.CSSProperties}
        >
          <b style={{ color }}>{risk}</b>
          <small>Risk score</small>
        </div>

        <h2 style={{ margin: "10px 0 4px", fontSize: "16px", color: "var(--ink)" }}>
          {analysis.primary_dest_entity}
        </h2>
        <p style={{ margin: 0, fontSize: "11px", color: "var(--muted)" }}>
          {analysis.explanation}
        </p>
      </div>

      {/* Transaction Overview Box */}
      <div className="card-box" style={{ marginTop: "12px" }}>
        <div className="box-title">BITCOIN TRANSACTION METRICS</div>
        <div className="box-grid">
          <div>
            <span className="meta-label">TXID:</span>
            <span className="meta-value mono" title={analysis.txid}>
              <a
                href={`https://blockstream.info/tx/${analysis.txid}`}
                target="_blank"
                rel="noreferrer"
                style={{ color: "var(--cyan)", textDecoration: "underline" }}
              >
                {shortTxid} ↗
              </a>
            </span>
          </div>
          <div>
            <span className="meta-label">Amount:</span>
            <span className="meta-value bold">{analysis.amount_btc.toFixed(8)} BTC</span>
          </div>
          <div>
            <span className="meta-label">Fee:</span>
            <span className="meta-value">{analysis.fee_btc.toFixed(8)} BTC</span>
          </div>
          <div>
            <span className="meta-label">Mempool Status:</span>
            <span className="meta-value" style={{ color: analysis.confirmed ? "#48f2a0" : "#ffb703" }}>
              {analysis.confirmed ? "● Confirmed" : "⏳ Pending Mempool"}
            </span>
          </div>
        </div>
      </div>

      {/* Estimated Network Origin Box */}
      <div className="card-box origin-box" style={{ marginTop: "10px" }}>
        <div className="box-title" style={{ color: "var(--cyan)" }}>
          ESTIMATED NETWORK ORIGIN
        </div>
        <div className="origin-highlight">
          <span className="origin-country">{analysis.origin.estimated_country}</span>
          <span className={`confidence-badge ${analysis.origin.confidence_level.toLowerCase()}`}>
            {analysis.origin.confidence_level} Confidence ({(analysis.origin.confidence_score * 100).toFixed(0)}%)
          </span>
        </div>
        <p className="evidence-text">
          <b>Evidence:</b> {analysis.origin.evidence}
        </p>
        <div className="warning-banner">
          ⚠️ {analysis.origin.warning}
        </div>
      </div>

      {/* Propagation Timing Breakdown */}
      <div className="card-box" style={{ marginTop: "10px" }}>
        <div className="box-title">OBSERVED P2P PROPAGATION (PORT 8333 WIRE)</div>
        <div className="propagation-table">
          {analysis.propagation_hops.map((hop, i) => (
            <div key={`${hop.peer_ip}-${i}`} className={`hop-row ${hop.is_first_seen ? "first-seen" : ""}`}>
              <div className="hop-left">
                <span className="hop-marker">{hop.is_first_seen ? "★" : "→"}</span>
                <span className="hop-label">{hop.node_label}</span>
              </div>
              <div className="hop-right">
                <span className="hop-country">{hop.country}</span>
                <span className="hop-delta">
                  +{hop.delta_ms} ms {hop.is_first_seen && <b>(Earliest)</b>}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Destinations & Entity Resolution */}
      <div className="card-box" style={{ marginTop: "10px" }}>
        <div className="box-title">DESTINATION ENTITY RESOLUTION</div>
        <div className="destinations-list">
          {analysis.destinations.map((dest, i) => (
            <div key={`${dest.address}-${i}`} className="dest-item">
              <div className="dest-header">
                <span className="role-tag">{dest.role || "Recipient"}</span>
                <span className="dest-val">{dest.value_btc.toFixed(8)} BTC</span>
              </div>
              <div className="dest-entity-title">{dest.entity_name}</div>
              <div className="dest-details">
                <span><b>Type:</b> {dest.entity_type}</span>
                <span><b>Region:</b> {dest.region}</span>
                {dest.tx_count && dest.tx_count > 0 ? (
                  <span><b>On-Chain:</b> {dest.tx_count.toLocaleString()} txs ({dest.total_btc?.toFixed(2)} BTC)</span>
                ) : null}
                <span><b>Confidence:</b> {dest.confidence}</span>
              </div>
              <div className="dest-addr mono" title={dest.address}>
                {dest.address.slice(0, 16)}…{dest.address.slice(-10)}
              </div>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={() => downloadTransactionPdf(analysis, `Forensic_Report_${analysis.txid.slice(0, 12)}.pdf`)}
        className="download-report-btn"
        title="Download Law-Enforcement Forensic Intelligence PDF Dossier"
      >
        📄 Download Forensic PDF Report
      </button>
    </aside>
  );
}

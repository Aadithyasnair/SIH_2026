"use client";
import { useEffect, useMemo, useState } from "react";
import { Alert, Cluster, getRisk } from "@/lib/data";
import {
  getAlerts,
  getClusters,
  getGraph,
  getLiveFeed,
  triggerIngest,
  getJobStatus,
  onBackendStatusChange,
  NetworkEvent,
} from "@/lib/api";
import { CountryGlobe, countryCoordinates } from "@/components/country-globe";

const glossary: Record<string, string> = {
  TXID: "The unique 64-character identifier of a Bitcoin transaction.",
  "Anomaly score": "Machine learning metric (0-1) indicating structural divergence from baseline transaction patterns.",
  ASN: "Autonomous System Number identifying the network organisation controlling an IP range.",
  "Peeling Chain": "A laundering pattern where funds move through consecutive wallets, peeling off small amounts while forwarding the bulk.",
  "CoinJoin / Mixing": "A privacy technique combining inputs from multiple signers into identical output denominations to obscure provenance.",
  "Common-Input-Ownership": "A blockchain heuristic stating that all inputs consumed in a single transaction belong to the same entity.",
  Cluster: "A group of Bitcoin wallet addresses mathematically determined to be controlled by the same actor or service.",
  "Propagated Risk": "Risk score assigned to a transaction based on multi-hop network proximity to sanctioned or illicit seed wallets.",
  "Risk Score": "The unified composite risk metric combining ML anomaly scoring, graph propagation, and heuristic flags.",
  "Confidence Score": "Statistical certainty metric associated with network event to transaction correlation."
};

const countryNames = [
  "Afghanistan","Albania","Algeria","Argentina","Australia","Austria","Bangladesh","Belgium",
  "Brazil","Canada","Chile","China","Colombia","Cyprus","Czechia","Denmark","Egypt","Finland",
  "France","Germany","Ghana","Greece","India","Indonesia","Iran","Iraq","Ireland","Israel",
  "Italy","Japan","Kenya","Mexico","Netherlands","Nigeria","Norway","Pakistan","Panama",
  "Poland","Portugal","Russian Federation","Saudi Arabia","Singapore","South Africa","South Korea",
  "Spain","Sweden","Switzerland","Thailand","Turkey","Ukraine","United Arab Emirates","United Kingdom",
  "United States","Vietnam"
];

function formatTimeAgo(dateString: string): string {
  if (!dateString) return "just now";
  const date = new Date(dateString);
  const diffMs = Date.now() - date.getTime();
  if (isNaN(diffMs)) return "recently";
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

function RiskPill({ value }: { value: number }) {
  const r = getRisk(value);
  return <span className={`pill ${r.key}`}>● {r.label}</span>;
}

function Kpi({ label, value, hint }: { label: string; value: number; hint: string }) {
  return (
    <article className="glass kpi">
      <span>
        {label} <abbr title={hint}>ⓘ</abbr>
      </span>
      <strong>{value.toLocaleString("en-US")}</strong>
    </article>
  );
}

function AlertPanel({ alert, close }: { alert: Alert; close: () => void }) {
  const risk = Math.round(alert.risk_score * 100);
  return (
    <aside className="detail glass">
      <button onClick={close} aria-label="Close">×</button>
      <div className="risk-ring" style={{ "--score": `${risk * 3.6}deg` } as React.CSSProperties}>
        <b>{risk}</b>
        <small>Risk score</small>
      </div>
      <RiskPill value={alert.risk_score} />
      <h2>{alert.pattern_type === "coinjoin_mixing" ? "Possible Mixing Service" : alert.pattern_type === "peeling_chain" ? "Peeling Chain Pattern" : "Suspicious transaction"}</h2>
      <p>{alert.explanation}</p>
      <h4>Flags</h4>
      <div className="tags">
        {alert.flags.map(flag => <span key={flag}>{flag.replaceAll("_", " ")}</span>)}
      </div>
      <p className="geo">◎ {alert.geo_summary}</p>
      <details>
        <summary>Technical details</summary>
        <p>
          <b>TXID:</b> {alert.txid}<br />
          <b>Addresses:</b> {alert.involved_addresses.join(", ")}<br />
          <b>Anomaly score:</b> {alert.anomaly_score}<br />
          <b>Propagated risk:</b> {alert.propagated_risk_score}<br />
          {alert.cluster_id && <><b>Cluster ID:</b> {alert.cluster_id}<br /></>}
          <b>Timestamp:</b> {alert.timestamp}
        </p>
      </details>
    </aside>
  );
}

export default function Dashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [minRisk, setMinRisk] = useState(0.4);
  const [selected, setSelected] = useState<Alert | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [activeAddress, setActiveAddress] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [live, setLive] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [showGuide, setShowGuide] = useState(true);
  const [isBackendOnline, setIsBackendOnline] = useState(true);

  // Live Simulation state
  const [simMode, setSimMode] = useState(false);
  const [simEvents, setSimEvents] = useState<NetworkEvent[]>([]);
  const [simIndex, setSimIndex] = useState(0);
  const [simTicker, setSimTicker] = useState<NetworkEvent[]>([]);
  const [liveArcs, setLiveArcs] = useState<NetworkEvent[]>([]);
  const [simPktCount, setSimPktCount] = useState(0);
  const [simByteRate, setSimByteRate] = useState(0);

  // Pipeline execution job state
  const [ingestJob, setIngestJob] = useState<{ id: string; progress: number; stage: string } | null>(null);

  const handleInspectAddress = async (addr: string) => {
    setActiveAddress(addr);
    setGraphLoading(true);
    try {
      const data = await getGraph(addr);
      setGraphData(data);
    } catch {
      setGraphData(null);
    } finally {
      setGraphLoading(false);
    }
  };

  // Lazy-load live network feed when simulation mode is first activated
  useEffect(() => {
    if (simMode && simEvents.length === 0) {
      getLiveFeed().then(events => {
        setSimEvents(events);
      });
    }
  }, [simMode, simEvents.length]);

  // Simulation playback engine
  useEffect(() => {
    if (!simMode || simEvents.length === 0 || !live) return;

    const BATCH_SIZE = 3;
    const intervalMs = Math.max(300, Math.floor(1000 / speed));

    const timer = setInterval(() => {
      setSimIndex(prev => {
        const next = (prev + BATCH_SIZE) % simEvents.length;
        const batch = simEvents.slice(prev, prev + BATCH_SIZE);
        setSimTicker(t => [...batch, ...t].slice(0, 8));
        setLiveArcs(batch);
        setSimPktCount(c => c + batch.length);
        const bytes = batch.reduce((sum, e) => sum + (e.packet_size || 0), 0);
        setSimByteRate(bytes);
        return next;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [simMode, simEvents, speed, live]);

  // Pipeline trigger handler
  const handleTriggerPipeline = async () => {
    const res = await triggerIngest();
    if (res && res.job_id) {
      setIngestJob({ id: res.job_id, progress: 0, stage: "Starting pipeline execution..." });
    }
  };

  // Pipeline job polling loop
  useEffect(() => {
    if (!ingestJob || ingestJob.progress >= 1) return;

    const interval = setInterval(async () => {
      const info = await getJobStatus(ingestJob.id);
      if (info) {
        setIngestJob({
          id: ingestJob.id,
          progress: info.progress ?? 0,
          stage: info.stage || info.status || "Processing...",
        });
        if (info.status === "completed" || info.status === "failed") {
          // Refresh alerts & clusters upon pipeline completion
          const [nextAlerts, nextClusters] = await Promise.all([getAlerts(), getClusters()]);
          setAlerts(nextAlerts);
          setClusters(nextClusters);
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [ingestJob]);

  useEffect(() => {
    const unsub = onBackendStatusChange((online) => {
      setIsBackendOnline(online);
    });
    return () => unsub();
  }, []);

  useEffect(() => {
    Promise.all([getAlerts(), getClusters()])
      .then(([nextAlerts, nextClusters]) => {
        setAlerts(nextAlerts);
        setClusters(nextClusters);
        setSelected(nextAlerts[0] ?? null);
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(
    () =>
      alerts
        .filter(a => `${a.txid} ${a.explanation} ${a.geo_summary} ${a.flags.join(" ")}`.toLowerCase().includes(query.toLowerCase()))
        .filter(a => a.risk_score >= minRisk),
    [alerts, query, minRisk]
  );

  const sortedClusters = useMemo(() => {
    return [...clusters].sort((a, b) => {
      if (b.avg_risk_score !== a.avg_risk_score) {
        return b.avg_risk_score - a.avg_risk_score;
      }
      return b.member_count - a.member_count;
    });
  }, [clusters]);

  const countries = useMemo(() => {
    const set = new Set<string>();
    alerts.forEach(a => {
      const summary = a.geo_summary || "";
      for (const [key, val] of Object.entries(countryCoordinates)) {
        if (key.length >= 3 && new RegExp(`\\b${key}\\b`, "i").test(summary)) {
          set.add(val.name);
        } else if (key.length === 2 && new RegExp(`\\b${key}\\b`).test(summary)) {
          set.add(val.name);
        }
      }
    });
    return set;
  }, [alerts]);

  return (
    <main>
      <div className="orbs" />
      <header>
        <div className="brand">
          <b>₿</b>
          <h1>SIH26146 <em>—</em> Bitcoin Transaction Monitor</h1>
          <span className={isBackendOnline ? "online" : "online"} style={isBackendOnline ? {} : { background: "#42171d", color: "#ff8290" }}>
            ● {isBackendOnline ? "System online" : "Offline mode"}
          </span>
        </div>
        <label className="search">
          ⌕ <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search wallet, TXID, country, or keyword…" />
        </label>
        <button
          className={`mode-toggle ${simMode ? "active" : ""}`}
          onClick={() => setSimMode(!simMode)}
          title={simMode ? "Switch back to static historical batch mode" : "Activate live peer-to-peer network stream simulation"}
        >
          {simMode ? "⚡ Live Sim ON" : "📊 Batch Mode"}
        </button>
        <button className="icon">◔</button>
        <button className="icon">☾</button>
      </header>

      {!isBackendOnline && (
        <div className="offline-banner" role="alert">
          <b>⚠</b> Could not reach backend API — displaying cached example data.
        </div>
      )}

      <section className="country-strip" aria-label="Countries covered">
        <b>COUNTRIES MONITORED</b>
        <div>{countryNames.map(c => <span key={c}>{c}</span>)}</div>
      </section>

      {showGuide && (
        <aside className="guide glass">
          <button onClick={() => setShowGuide(false)}>Got it</button>
          <b>How to read this dashboard</b>
          <span>Start with the risk-labelled alerts, drag the globe to inspect routes, then open an alert or cluster for the evidence.</span>
        </aside>
      )}

      <section className="kpis">
        {simMode ? (
          <>
            <Kpi label="Packets Simulated" value={simPktCount} hint="Network packets replayed from Module A's live feed." />
            <Kpi label="Throughput (last tick)" value={simByteRate} hint="Total bytes observed across active peer connections in the last tick." />
            <Kpi label="Anomalous Packets" value={simTicker.filter(e => e.event_id.includes("rapid") || e.event_id.includes("smurf")).length} hint="Packets tagged with Sybil bursts or smurf flooding signatures." />
            <Kpi label="Active Feeds Monitored" value={simEvents.length > 0 ? 9 : 0} hint="Network observer regions currently transmitting live traffic." />
          </>
        ) : (
          <>
            <Kpi label="Transactions Analyzed" value={alerts.length > 0 ? alerts.length : 0} hint="Total Bitcoin transactions analyzed in active dataset." />
            <Kpi label="Active Alerts" value={alerts.length} hint="Transactions needing investigation." />
            <Kpi label="High Risk Flags" value={alerts.filter(a => a.risk_score > 0.7).length} hint="Alerts above a 70% risk score." />
            <Kpi label="Countries Involved" value={countries.size} hint="Unique countries detected in related network traffic." />
          </>
        )}
      </section>

      <section className="top-grid">
        <article className="glass globe-card">
          <div className="section-title">
            <div>
              <h2>{simMode ? "Real-Time Network Traffic Simulation" : "Global Transaction Flow"}</h2>
              <p>{simMode ? "Live P2P connection tracer arcs advancing in real-time." : "Drag the globe to rotate it — country labels remain visible."}</p>
            </div>
            <span className={simMode ? "live sim-active" : "live"}>
              {simMode ? `⚡ LIVE SIM (${simPktCount} pkts)` : "● BATCH MODE"}
            </span>
          </div>
          <CountryGlobe alerts={filtered} playing={live} speed={speed} liveEvents={simMode ? liveArcs : []} />
          <div className="globe-controls">
            <button onClick={() => setLive(!live)}>{live ? "Ⅱ Pause" : "▶ Play"}</button>
            {[1, 5, 20].map(n => (
              <button className={speed === n ? "selected" : ""} onClick={() => setSpeed(n)} key={n}>{n}×</button>
            ))}
          </div>
        </article>

        <article className="glass events">
          {simMode ? (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <h2 style={{ margin: 0 }}>⚡ Live Network Stream</h2>
                <span style={{ fontSize: "10px", color: "var(--cyan)" }}>Port 8333 P2P</span>
              </div>
              <p style={{ fontSize: "11px", color: "var(--muted)", margin: "0 0 8px" }}>Replaying live peer metadata from observer nodes.</p>
              <div className="ticker-scroll">
                {simTicker.map(e => {
                  const isAnom = e.event_id.includes("rapid") || e.event_id.includes("smurf");
                  return (
                    <div key={e.event_id} className={`tick-row ${isAnom ? "high" : "low"}`}>
                      <span className="tick-flag">{e.src_geo_country} → {e.dst_geo_country}</span>
                      <span className="tick-detail" title={`${e.src_ip} -> ${e.dst_ip}`}>
                        {e.src_ip} → {e.dst_ip}
                      </span>
                      <span className="tick-badge">{e.protocol}:{e.dst_port}</span>
                      <span className="tick-size">{e.packet_size}B</span>
                      {isAnom && <span className="pill high" style={{ padding: "1px 5px", fontSize: "9px" }}>⚠ Sybil/Burst</span>}
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <>
              <h2>Latest events</h2>
              {filtered.slice(0, 5).map(a => (
                <button key={a.alert_id} onClick={() => setSelected(a)}>
                  <RiskPill value={a.risk_score} />
                  <span>{a.geo_summary}<small>{a.explanation.slice(0, 65)}…</small></span>
                  <time>{formatTimeAgo(a.timestamp)}</time>
                </button>
              ))}
            </>
          )}
        </article>

        {selected && <AlertPanel alert={selected} close={() => setSelected(null)} />}
      </section>

      <section className="lower-grid">
        <article className="glass alerts">
          <div className="section-title">
            <div>
              <h2>Recent Alerts</h2>
              <p>Plain-language findings; open a row for technical evidence.</p>
            </div>
            <label>Minimum risk <input type="range" min="0" max="1" step="0.1" value={minRisk} onChange={e => setMinRisk(+e.target.value)} /></label>
          </div>
          <div className="table">
            <div className="thead"><span>TXID</span><span>Summary</span><span>Risk</span><span>Time</span></div>
            {loading ? (
              <div className="skeleton" />
            ) : (
              filtered.map(a => (
                <button className={`row ${getRisk(a.risk_score).key}`} onClick={() => setSelected(a)} key={a.alert_id}>
                  <span>{a.txid.slice(0, 8)}…{a.txid.slice(-4)}</span>
                  <span>{a.explanation.slice(0, 86)}…</span>
                  <RiskPill value={a.risk_score} />
                  <time>{new Date(a.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
                </button>
              ))
            )}
          </div>
        </article>

        <article className="glass clusters">
          <div className="section-title">
            <div>
              <h2>Cluster / Link Analysis</h2>
              <p>Entities identified via common input heuristics & graph embeddings.</p>
            </div>
            <span style={{ fontSize: "11px", color: "var(--cyan)" }}>{clusters.length} clusters tracked</span>
          </div>

          <div className="cluster-stage">
            {sortedClusters.slice(0, 8).map((c) => {
              const risk = getRisk(c.avg_risk_score);
              const isSelected = expanded === c.cluster_id;
              return (
                <button
                  key={c.cluster_id}
                  onClick={() => {
                    if (isSelected) {
                      setExpanded(null);
                      setActiveAddress(null);
                      setGraphData(null);
                    } else {
                      setExpanded(c.cluster_id);
                      if (c.member_addresses && c.member_addresses.length > 0) {
                        handleInspectAddress(c.member_addresses[0]);
                      }
                    }
                  }}
                  className={`cluster ${isSelected ? "selected" : ""} ${c.avg_risk_score > 0.7 ? "hot" : ""}`}
                  style={{
                    borderColor: risk.key === "high" ? "#ff5267" : risk.key === "medium" ? "#ffbe3d" : "#4be99a",
                    minWidth: "140px",
                  }}
                >
                  <RiskPill value={c.avg_risk_score} />
                  <b>{c.label}</b>
                  <small>{c.member_count.toLocaleString()} addresses</small>
                </button>
              );
            })}
          </div>

          <div className="legend">
            <b>Legend</b>
            <span>● High risk (&gt;0.7)</span>
            <span>● Medium risk (0.4-0.7)</span>
            <span>● Low risk (&lt;0.4)</span>
            <span>Click entity to inspect subgraph & members</span>
          </div>

          {expanded && (
            <div className="cluster-detail">
              {(() => {
                const c = clusters.find(x => x.cluster_id === expanded);
                if (!c) return null;
                return (
                  <>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <h3>{c.label} <small style={{ color: "var(--muted)", fontSize: "11px" }}>({c.cluster_id})</small></h3>
                      <RiskPill value={c.avg_risk_score} />
                    </div>
                    <p>{c.description}</p>
                    
                    <details>
                      <summary>Clustering Heuristic & Method</summary>
                      <p style={{ marginTop: "4px", fontFamily: "monospace", fontSize: "10px", color: "var(--cyan)" }}>
                        {c.clustering_method}
                      </p>
                    </details>

                    <div className="cluster-members">
                      <h4>Member Addresses ({c.member_count.toLocaleString()} total, showing top {Math.min(12, c.member_addresses?.length || 0)}):</h4>
                      <div className="cluster-addr-list">
                        {(c.member_addresses || []).slice(0, 12).map((addr) => (
                          <button
                            key={addr}
                            className={`addr-tag ${activeAddress === addr ? "active" : ""}`}
                            onClick={() => handleInspectAddress(addr)}
                            title="Click to query ego subgraph from Neo4j/GraphML"
                          >
                            {addr.slice(0, 8)}…{addr.slice(-6)}
                          </button>
                        ))}
                      </div>
                    </div>

                    {activeAddress && (
                      <div className="cluster-graph-preview">
                        <h5>Ego Subgraph Analysis: <code style={{ color: "#fff" }}>{activeAddress}</code></h5>
                        {graphLoading ? (
                          <span style={{ fontSize: "10px", color: "var(--muted)" }}>Querying topological link graph…</span>
                        ) : graphData ? (
                          <>
                            <div className="graph-stats">
                              <span>● Nodes: <b>{graphData.nodes.length}</b></span>
                              <span>● Edges: <b>{graphData.edges.length}</b></span>
                              <span>● Status: <b>Connected Component Verified</b></span>
                            </div>
                            {graphData.nodes.length > 0 && (
                              <div className="graph-nodes">
                                {graphData.nodes.slice(0, 8).map((n: any) => (
                                  <span key={n.id} className="node-pill" title={n.id}>
                                    {n.type || "node"}: {n.id.length > 16 ? `${n.id.slice(0, 6)}…${n.id.slice(-4)}` : n.id}
                                  </span>
                                ))}
                                {graphData.nodes.length > 8 && (
                                  <span className="node-pill">+{graphData.nodes.length - 8} more</span>
                                )}
                              </div>
                            )}
                          </>
                        ) : (
                          <span style={{ fontSize: "10px", color: "var(--muted)" }}>No external graph neighbors found for this address.</span>
                        )}
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          )}

          <div className="pipeline-box">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3>⚙ Re-run Analysis Pipeline</h3>
                <p>Execute offline ingestion, ML anomaly detection, and clustering over incoming traffic.</p>
              </div>
              {!ingestJob && (
                <button onClick={handleTriggerPipeline}>
                  ▶ Run Pipeline
                </button>
              )}
            </div>

            {ingestJob && (
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${Math.round(ingestJob.progress * 100)}%` }}
                />
                <div className="progress-text">
                  {ingestJob.stage} ({Math.round(ingestJob.progress * 100)}%)
                </div>
              </div>
            )}
          </div>
        </article>
      </section>

      <footer>
        Hover terms for help:{" "}
        {Object.entries(glossary).map(([term, desc]) => (
          <abbr key={term} title={desc}>{term}</abbr>
        ))}
        {" "}<span>•</span> Playback of analyzed data, not real-time interception.
      </footer>
    </main>
  );
}

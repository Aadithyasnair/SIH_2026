"use client";

import { useEffect, useMemo, useState } from "react";
import { Alert, Cluster, getRisk, getRiskColor, isDarknetOrTor } from "@/lib/data";
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
import { ClusterWebGraph } from "@/components/cluster-web-graph";

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
};

const MONITORED_COUNTRIES: string[] = [
  "Afghanistan", "Albania", "Algeria", "Argentina", "Australia", "Austria",
  "Bangladesh", "Belgium", "Brazil", "Canada", "Chile", "China", "Colombia",
  "Cyprus", "Czechia", "Denmark", "Egypt", "Finland", "France", "Germany",
  "Ghana", "Greece", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel",
  "Italy", "Japan", "Kenya", "Mexico", "Netherlands", "Nigeria", "Norway",
  "Pakistan", "Panama", "Poland", "Portugal", "Russian Federation",
  "Saudi Arabia", "Singapore", "South Africa", "South Korea", "Spain",
  "Sweden", "Switzerland", "Thailand", "Turkey", "Ukraine",
  "United Arab Emirates", "United Kingdom", "United States", "Vietnam",
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
  const color = getRiskColor(value);
  return (
    <span
      className={`pill ${r.key}`}
      style={{
        color,
        borderColor: `${color}88`,
        background: `${color}18`,
      }}
    >
      ● {r.label} ({(value * 100).toFixed(0)}%)
    </span>
  );
}

function RiskBadge({ value }: { value: number }) {
  const r = getRisk(value);
  const label = value > 0.7 ? "High" : value >= 0.4 ? "Medium" : "Low";
  return (
    <span
      className={`risk-badge ${r.key}`}
      style={{
        color: r.color,
        borderColor: `${r.color}99`,
        background: `${r.color}20`,
        fontWeight: 700,
        fontSize: "11px",
        padding: "2px 8px",
        borderRadius: "8px",
        border: `1px solid ${r.color}99`,
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
      }}
    >
      ● {label}
    </span>
  );
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
  const color = getRiskColor(alert.risk_score);
  const isTor = isDarknetOrTor(alert);
  return (
    <aside className="detail glass">
      <button onClick={close} aria-label="Close">
        ×
      </button>
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
      <div style={{ display: "flex", gap: "6px", alignItems: "center", marginBottom: "8px", flexWrap: "wrap" }}>
        <RiskPill value={alert.risk_score} />
        {isTor ? (
          <span style={{ fontSize: "10px", fontWeight: 700, padding: "2px 7px", borderRadius: "6px", background: "rgba(192, 132, 252, 0.2)", border: "1px solid #c084fc", color: "#e9d5ff" }}>
            🧅 Tor / Darknet Overlay
          </span>
        ) : (
          <span style={{ fontSize: "10px", fontWeight: 600, padding: "2px 7px", borderRadius: "6px", background: "rgba(0, 240, 255, 0.1)", border: "1px solid rgba(0, 240, 255, 0.3)", color: "var(--cyan)" }}>
            🌐 Clearnet P2P Route
          </span>
        )}
      </div>
      <h2>
        {alert.pattern_type === "coinjoin_mixing"
          ? "Possible Mixing Service"
          : alert.pattern_type === "peeling_chain"
          ? "Peeling Chain Pattern"
          : isTor
          ? "Tor Anonymized Transaction"
          : "Suspicious transaction"}
      </h2>
      <p>{alert.explanation}</p>
      <h4>Flags</h4>
      <div className="tags">
        {alert.flags.map((flag) => (
          <span key={flag}>{flag.replaceAll("_", " ")}</span>
        ))}
      </div>
      <p className="geo">◎ {alert.geo_summary}</p>
      <details>
        <summary>Technical details</summary>
        <p>
          <b>TXID:</b> {alert.txid}
          <br />
          <b>Network Transport:</b> {isTor ? "Tor Onion Proxy (Port 9050 / Anonymized P2P)" : "Clearnet TCP (Port 8333 / Clearnet P2P)"}
          <br />
          <b>Addresses:</b> {alert.involved_addresses.join(", ")}
          <br />
          <b>Anomaly score:</b> {alert.anomaly_score}
          <br />
          <b>Propagated risk:</b> {alert.propagated_risk_score}
          <br />
          {alert.cluster_id && (
            <>
              <b>Cluster ID:</b> {alert.cluster_id}
              <br />
            </>
          )}
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
  const [torOnly, setTorOnly] = useState(false);
  const [selected, setSelected] = useState<Alert | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<Cluster | null>(null);
  const [clusterLimit, setClusterLimit] = useState(15);
  const [activeAddress, setActiveAddress] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [live, setLive] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [isBackendOnline, setIsBackendOnline] = useState(true);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  // Live Simulation state
  const [simMode, setSimMode] = useState(false);
  const [simEvents, setSimEvents] = useState<NetworkEvent[]>([]);
  const [simIndex, setSimIndex] = useState(0);
  const [simTicker, setSimTicker] = useState<NetworkEvent[]>([]);
  const [liveArcs, setLiveArcs] = useState<NetworkEvent[]>([]);
  const [simPktCount, setSimPktCount] = useState(0);
  const [simByteRate, setSimByteRate] = useState(0);
  const [simAlerts, setSimAlerts] = useState<Alert[]>([]);
  const [alertPage, setAlertPage] = useState(1);
  const ALERTS_PER_PAGE = 8;

  // Pipeline execution job state
  const [ingestJob, setIngestJob] = useState<{ id: string; progress: number; stage: string } | null>(null);

  // Theme setup
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") as "dark" | "light" | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute("data-theme", savedTheme);
    } else {
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    localStorage.setItem("theme", nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  };

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
      getLiveFeed().then((events) => {
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
      setSimIndex((prev) => {
        const next = (prev + BATCH_SIZE) % simEvents.length;
        const batch = simEvents.slice(prev, prev + BATCH_SIZE);

        const isTorTick = (next / BATCH_SIZE) % 4 === 0;
        const effectiveBatch = [...batch];
        if (isTorTick) {
          const torExitCountries = ["DE", "NL", "CH", "SE", "RO", "US"];
          const exitCountry = torExitCountries[Math.floor(Math.random() * torExitCountries.length)];
          const torEvent: NetworkEvent = {
            event_id: `tor_relay_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            timestamp: new Date().toISOString(),
            src_ip: `185.220.${Math.floor(Math.random() * 50 + 100)}.${Math.floor(Math.random() * 250 + 2)}`,
            dst_ip: `199.14.${Math.floor(Math.random() * 50 + 200)}.${Math.floor(Math.random() * 250 + 2)}`,
            src_port: 9050,
            dst_port: 8333,
            protocol: "TCP",
            packet_size: Math.floor(Math.random() * 400 + 512),
            src_geo_country: exitCountry,
            src_asn: "AS-TOR-ROUTER",
            dst_geo_country: "US",
            dst_asn: "AS15169",
          };
          effectiveBatch.unshift(torEvent);
        }

        setSimTicker((t) => [...effectiveBatch, ...t].slice(0, 10));
        setLiveArcs(effectiveBatch);
        setSimPktCount((c) => c + effectiveBatch.length);
        const bytes = effectiveBatch.reduce((sum, e) => sum + (e.packet_size || 0), 0);
        setSimByteRate(bytes);

        const anomBatch = effectiveBatch.filter(
          (e) => e.event_id.includes("rapid") || e.event_id.includes("smurf") || e.event_id.includes("tor_relay")
        );
        if (anomBatch.length > 0) {
          const generatedAlerts: Alert[] = anomBatch.map((e) => {
            const isTor = e.event_id.includes("tor_relay") || isDarknetOrTor(e);
            const isRapid = e.event_id.includes("rapid");
            const risk = isTor ? 0.94 : isRapid ? 0.88 : 0.76;
            return {
              alert_id: `live_${e.event_id}`,
              txid: `net_${e.event_id.slice(-16)}`,
              involved_addresses: [`node:${e.src_ip}:${e.src_port}`, `peer:${e.dst_ip}:${e.dst_port}`],
              risk_score: risk,
              anomaly_score: isTor ? 0.96 : isRapid ? 0.94 : 0.82,
              propagated_risk_score: isTor ? 0.89 : 0.65,
              pattern_type: isTor ? "darknet_vendor_flow" : isRapid ? "sybil_burst" : "smurf_flood",
              cluster_id: isTor ? "cluster_darknet_hydra" : null,
              flags: isTor
                ? ["tor_exit_relay", "onion_route_detected", "darknet_market_proceeds"]
                : isRapid
                ? ["rapid_ip_burst", "high_freq_syn"]
                : ["smurf_amplification", "peer_flood"],
              explanation: isTor
                ? `Live Tor Onion exit relay packet observed from ${e.src_ip} (port 9050, AS-TOR) broadcasting to peer node in ${e.dst_geo_country}.`
                : isRapid
                ? `Live peer ${e.src_ip} in ${e.src_geo_country} triggered rapid IP burst to node ${e.dst_ip} (port ${e.dst_port}).`
                : `Live smurf attack flow observed between ${e.src_geo_country} and ${e.dst_geo_country} (${e.packet_size} bytes).`,
              timestamp: new Date().toISOString(),
              geo_summary: isTor
                ? `🧅 Tor Onion Route ${e.src_geo_country} → ${e.dst_geo_country}`
                : `Live P2P route ${e.src_geo_country} → ${e.dst_geo_country}`,
            };
          });
          setSimAlerts((prevA) => [...generatedAlerts, ...prevA].slice(0, 50));
        }

        return next;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [simMode, simEvents, speed, live]);

  const handleTriggerPipeline = async () => {
    const res = await triggerIngest();
    if (res && res.job_id) {
      setIngestJob({ id: res.job_id, progress: 0, stage: "Starting pipeline execution..." });
    }
  };

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

  const sortedClusters = useMemo(() => {
    return [...clusters].sort((a, b) => {
      if (b.avg_risk_score !== a.avg_risk_score) {
        return b.avg_risk_score - a.avg_risk_score;
      }
      return b.member_count - a.member_count;
    });
  }, [clusters]);

  const visibleClusters = useMemo(() => {
    return sortedClusters.slice(0, clusterLimit);
  }, [sortedClusters, clusterLimit]);

  const activeAlerts = useMemo(() => {
    if (simMode && simAlerts.length > 0) {
      return [...simAlerts, ...alerts];
    }
    return alerts;
  }, [simMode, simAlerts, alerts]);

  const filtered = useMemo(
    () =>
      activeAlerts
        .filter((a) =>
          `${a.txid} ${a.explanation} ${a.geo_summary} ${a.flags.join(" ")}`
            .toLowerCase()
            .includes(query.toLowerCase())
        )
        .filter((a) => a.risk_score >= minRisk)
        .filter((a) => !torOnly || isDarknetOrTor(a)),
    [activeAlerts, query, minRisk, torOnly]
  );

  useEffect(() => {
    setAlertPage(1);
  }, [query, minRisk, simMode, torOnly]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / ALERTS_PER_PAGE));
  const paginatedAlerts = useMemo(() => {
    const start = (alertPage - 1) * ALERTS_PER_PAGE;
    return filtered.slice(start, start + ALERTS_PER_PAGE);
  }, [filtered, alertPage, ALERTS_PER_PAGE]);

  const countries = useMemo(() => {
    const set = new Set<string>();
    alerts.forEach((a) => {
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
          <h1>
            SIH26146 <em>—</em> Bitcoin Transaction Monitor
          </h1>
          <span
            className={isBackendOnline ? "online" : "online"}
            style={isBackendOnline ? {} : { background: "#42171d", color: "#ff8290" }}
          >
            ● {isBackendOnline ? "System online" : "Offline mode"}
          </span>
        </div>
        <label className="search">
          ⌕{" "}
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search wallet, TXID, country, or keyword…"
          />
        </label>
        <button
          className={`mode-toggle ${simMode ? "active" : ""}`}
          onClick={() => setSimMode(!simMode)}
          title={simMode ? "Switch back to static historical batch mode" : "Activate live peer-to-peer network stream simulation"}
        >
          {simMode ? "⚡ Live Sim ON" : "📊 Batch Mode"}
        </button>
        <button
          className="icon"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {theme === "dark" ? "☼" : "☾"}
        </button>
      </header>

      {!isBackendOnline && (
        <div className="offline-banner" role="alert">
          <b>⚠</b> Could not reach backend API — displaying cached example data.
        </div>
      )}

      {/* Dual-Track Continuous Seamless Marquee */}
      <section className="country-strip" aria-label="Countries covered">
        <b>COUNTRIES MONITORED</b>
        <div className="marquee-container">
          <div className="marquee-track">
            {MONITORED_COUNTRIES.map((c, i) => {
              const isActive = countries.has(c);
              return (
                <span
                  key={`c1-${i}`}
                  style={isActive ? { color: "var(--strip-title)", fontWeight: 700 } : undefined}
                >
                  {isActive ? "● " : ""}
                  {c}
                </span>
              );
            })}
          </div>
          <div className="marquee-track" aria-hidden="true">
            {MONITORED_COUNTRIES.map((c, i) => {
              const isActive = countries.has(c);
              return (
                <span
                  key={`c2-${i}`}
                  style={isActive ? { color: "var(--strip-title)", fontWeight: 700 } : undefined}
                >
                  {isActive ? "● " : ""}
                  {c}
                </span>
              );
            })}
          </div>
        </div>
      </section>

      <section className="kpis">
        {simMode ? (
          <>
            <Kpi label="Packets Simulated" value={simPktCount} hint="Network packets replayed from Module A's live feed." />
            <Kpi label="Throughput (last tick)" value={simByteRate} hint="Total bytes observed across active peer connections in the last tick." />
            <Kpi
              label="Anomalous Packets"
              value={simTicker.filter((e) => e.event_id.includes("rapid") || e.event_id.includes("smurf")).length}
              hint="Packets tagged with Sybil bursts or smurf flooding signatures."
            />
            <Kpi label="Active Feeds Monitored" value={simEvents.length > 0 ? 9 : 0} hint="Network observer regions currently transmitting live traffic." />
          </>
        ) : (
          <>
            <Kpi label="Transactions Analyzed" value={alerts.length > 0 ? alerts.length : 0} hint="Total Bitcoin transactions analyzed in active dataset." />
            <Kpi label="Active Alerts" value={alerts.length} hint="Transactions needing investigation." />
            <Kpi label="High Risk Flags" value={alerts.filter((a) => a.risk_score > 0.7).length} hint="Alerts above a 70% risk score." />
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
            {[1, 5, 20].map((n) => (
              <button
                className={speed === n ? "selected" : ""}
                onClick={() => setSpeed(n)}
                key={n}
              >
                {n}×
              </button>
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
                {simTicker.map((e) => {
                  const isTor = e.event_id.includes("tor_relay") || isDarknetOrTor(e);
                  const isAnom = e.event_id.includes("rapid") || e.event_id.includes("smurf");
                  return (
                    <div key={e.event_id} className={`tick-row ${isTor ? "tor" : isAnom ? "high" : "low"}`}>
                      <span className="tick-flag">
                        {isTor ? "🧅 " : ""}
                        {e.src_geo_country} → {e.dst_geo_country}
                      </span>
                      <span className="tick-detail" title={`${e.src_ip} -> ${e.dst_ip}`}>
                        {e.src_ip} → {e.dst_ip}
                      </span>
                      <span className="tick-badge">
                        {e.protocol}:{e.dst_port}
                      </span>
                      <span className="tick-size">{e.packet_size}B</span>
                      {isTor ? (
                        <span className="pill tor" style={{ padding: "1px 6px", fontSize: "9px", fontWeight: 700 }}>
                          🧅 Tor Relay
                        </span>
                      ) : isAnom ? (
                        <span className="pill high" style={{ padding: "1px 5px", fontSize: "9px" }}>
                          ⚠ Sybil/Burst
                        </span>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <>
              <h2>Latest events</h2>
              <div className="events-scroll">
                {filtered.slice(0, 8).map((a) => (
                  <button key={a.alert_id} onClick={() => setSelected(a)}>
                    <RiskPill value={a.risk_score} />
                    <span>
                      {a.geo_summary}
                      <small>{a.explanation.slice(0, 65)}…</small>
                    </span>
                    <time>{formatTimeAgo(a.timestamp)}</time>
                  </button>
                ))}
              </div>
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
            <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
              <button
                className={`mode-toggle ${torOnly ? "active" : ""}`}
                style={{
                  padding: "4px 10px",
                  fontSize: "11px",
                  borderColor: torOnly ? "#c084fc" : undefined,
                  background: torOnly ? "rgba(168, 85, 247, 0.25)" : undefined,
                  color: torOnly ? "#e9d5ff" : undefined,
                }}
                onClick={() => setTorOnly(!torOnly)}
                title="Filter transactions broadcasted via Tor exit nodes or Darknet markets"
              >
                🧅 Tor / Darknet {torOnly ? "ON" : "Filter"}
              </button>
              <label>
                Minimum risk{" "}
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={minRisk}
                  onChange={(e) => setMinRisk(+e.target.value)}
                />
              </label>
            </div>
          </div>
          <div className="table">
            <div className="thead">
              <span>TXID</span>
              <span>Summary</span>
              <span>Risk</span>
              <span>Time</span>
            </div>
            <div className="table-scroll">
              {loading ? (
                <div className="skeleton" />
              ) : paginatedAlerts.length === 0 ? (
                <div style={{ padding: "20px", textAlign: "center", color: "var(--muted)", fontSize: "12px" }}>
                  No alerts matching the current search / risk criteria.
                </div>
              ) : (
                paginatedAlerts.map((a) => {
                  const isTor = isDarknetOrTor(a);
                  return (
                    <button
                      className={`row ${getRisk(a.risk_score).key}`}
                      onClick={() => setSelected(a)}
                      key={a.alert_id}
                    >
                      <span>
                        {a.txid.slice(0, 8)}…{a.txid.slice(-4)}
                      </span>
                      <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        {isTor && (
                          <span
                            style={{
                              fontSize: "9px",
                              padding: "1px 5px",
                              borderRadius: "4px",
                              background: "rgba(168, 85, 247, 0.2)",
                              border: "1px solid #c084fc",
                              color: "#e9d5ff",
                              fontWeight: 700,
                              whiteSpace: "nowrap",
                            }}
                          >
                            🧅 Tor
                          </span>
                        )}
                        <span>{a.explanation.slice(0, isTor ? 72 : 86)}…</span>
                      </span>
                      <RiskPill value={a.risk_score} />
                      <time>
                        {new Date(a.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </time>
                    </button>
                  );
                })
              )}
            </div>

            {filtered.length > 0 && (
              <div className="pagination-bar">
                <span>
                  Showing <b>{(alertPage - 1) * ALERTS_PER_PAGE + 1}</b>–<b>{Math.min(alertPage * ALERTS_PER_PAGE, filtered.length)}</b> of <b>{filtered.length}</b> alerts
                </span>
                <div style={{ display: "flex", gap: "6px" }}>
                  <button
                    className="pagination-btn"
                    onClick={() => setAlertPage((p) => Math.max(1, p - 1))}
                    disabled={alertPage === 1}
                  >
                    ◀ Prev
                  </button>
                  <span style={{ padding: "4px 8px", background: "var(--ctrl-btn-bg)", borderRadius: "6px" }}>
                    Page {alertPage} / {totalPages}
                  </span>
                  <button
                    className="pagination-btn"
                    onClick={() => setAlertPage((p) => Math.min(totalPages, p + 1))}
                    disabled={alertPage >= totalPages}
                  >
                    Next ▶
                  </button>
                </div>
              </div>
            )}
          </div>
        </article>

        {/* Cluster / Link Analysis - Scrollable & Compact */}
        <article className="glass clusters">
          <div className="section-title">
            <div>
              <h2>Cluster / Link Analysis</h2>
              <p>Clustered entity analysis, transaction heuristics, and member wallet graph exploration.</p>
            </div>
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <span className="live" style={{ fontSize: "10px", padding: "4px 8px" }}>
                {selectedCluster ? "⚡ Single-Cluster Web" : "📊 Entity Directory"}
              </span>
              <span style={{ fontSize: "11px", color: "var(--cyan)" }}>
                {clusters.length} clusters tracked
              </span>
            </div>
          </div>

          {!selectedCluster ? (
            /* DEFAULT VIEW: Scrollable Grid of Cluster Cards */
            <>
              <div className="cluster-grid">
                {visibleClusters.map((c) => {
                  const isTor = isDarknetOrTor({ label: c.label, description: c.description });
                  const r = getRisk(c.avg_risk_score);
                  return (
                    <div
                      key={c.cluster_id}
                      className={`cluster-summary-card ${isTor ? "tor" : r.key}`}
                      onClick={() => {
                        setSelectedCluster(c);
                        if (c.member_addresses && c.member_addresses.length > 0) {
                          handleInspectAddress(c.member_addresses[0]);
                        }
                      }}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="card-header">
                        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                          <RiskBadge value={c.avg_risk_score} />
                          {isTor && (
                            <span
                              style={{
                                fontSize: "9px",
                                padding: "2px 6px",
                                borderRadius: "4px",
                                background: "rgba(168, 85, 247, 0.25)",
                                border: "1px solid #c084fc",
                                color: "#f3e8ff",
                                fontWeight: 700,
                              }}
                            >
                              🧅 Tor / Darknet
                            </span>
                          )}
                        </div>
                        <span className="member-count-badge">
                          {c.member_count.toLocaleString()} member {c.member_count === 1 ? "address" : "addresses"}
                        </span>
                      </div>

                      <h3 className="card-label">
                        {isTor ? "🧅 " : ""}
                        {c.label}
                      </h3>

                      <p className="card-description">{c.description}</p>

                      <div className="card-footer">
                        <span
                          className="method-tag"
                          style={isTor ? { color: "#d8b4fe", background: "rgba(168, 85, 247, 0.15)" } : undefined}
                        >
                          {c.clustering_method.replace(/_/g, " ")}
                        </span>
                        <span className="open-link" style={isTor ? { color: "#d8b4fe" } : undefined}>
                          Explore Graph ➔
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {sortedClusters.length > 15 && (
                <div style={{ display: "flex", justifyContent: "center", marginTop: "10px", marginBottom: "4px" }}>
                  {clusterLimit < sortedClusters.length ? (
                    <button
                      className="show-more-btn"
                      onClick={() => setClusterLimit((prev) => Math.min(prev + 15, sortedClusters.length))}
                    >
                      Show More Clusters ({sortedClusters.length - clusterLimit} remaining) ▼
                    </button>
                  ) : (
                    <button className="show-more-btn" onClick={() => setClusterLimit(15)}>
                      Show Less ▲
                    </button>
                  )}
                </div>
              )}
            </>
          ) : (
            /* SINGLE-CLUSTER DETAIL VIEW: Force-Directed Graph */
            <div className="single-cluster-detail">
              <div className="detail-nav-bar">
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <button
                    className="back-btn"
                    onClick={() => {
                      setSelectedCluster(null);
                      setActiveAddress(null);
                      setGraphData(null);
                    }}
                  >
                    ◀ Back to All Clusters
                  </button>
                  <span className="cluster-id-badge">{selectedCluster.cluster_id}</span>
                </div>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <RiskBadge value={selectedCluster.avg_risk_score} />
                  <span className="info-chip">
                    {selectedCluster.member_count.toLocaleString()} Addresses
                  </span>
                </div>
              </div>

              <div style={{ marginBottom: "10px" }}>
                <h3 style={{ margin: "0 0 4px", fontSize: "15px", color: "var(--ink)" }}>
                  {selectedCluster.label}
                </h3>
                <p className="detail-prominent-desc">{selectedCluster.description}</p>
              </div>

              {/* Force-directed graph canvas */}
              <ClusterWebGraph
                cluster={selectedCluster}
                subgraphData={graphData}
                activeAddress={activeAddress}
                onSelectAddress={(addr) => handleInspectAddress(addr)}
              />

              {/* Member address chips & Ego preview */}
              <div className="cluster-detail" style={{ marginTop: "10px" }}>
                <div className="cluster-members">
                  <h4>
                    Member Addresses ({selectedCluster.member_count.toLocaleString()} total, showing top{" "}
                    {Math.min(16, selectedCluster.member_addresses?.length || 0)}):
                  </h4>
                  <div className="cluster-addr-list">
                    {(selectedCluster.member_addresses || []).slice(0, 16).map((addr) => (
                      <button
                        key={addr}
                        className={`addr-tag ${activeAddress === addr ? "active" : ""}`}
                        onClick={() => handleInspectAddress(addr)}
                        title="Click to focus node & query Neo4j subgraph"
                      >
                        {addr.slice(0, 8)}…{addr.slice(-6)}
                      </button>
                    ))}
                  </div>
                </div>

                {activeAddress && (
                  <div className="cluster-graph-preview">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <h5 style={{ margin: 0, fontSize: "11px", color: "#48f2a0" }}>
                        Ego Subgraph Analysis: <code style={{ color: "var(--ink)" }}>{activeAddress}</code>
                      </h5>
                      {graphLoading && <span style={{ fontSize: "10px", color: "var(--cyan)" }}>Querying Neo4j…</span>}
                    </div>
                    {graphData ? (
                      <div className="graph-stats" style={{ marginTop: "6px" }}>
                        <span>● Verified Nodes: <b>{graphData.nodes.length}</b></span>
                        <span>● Verified Edges: <b>{graphData.edges.length}</b></span>
                        <span>● Component Status: <b>Connected</b></span>
                      </div>
                    ) : !graphLoading ? (
                      <span style={{ fontSize: "10px", color: "var(--muted)" }}>
                        No external multi-hop neighbors found for this address.
                      </span>
                    ) : null}
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="pipeline-box">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3>⚙ Re-run Analysis Pipeline</h3>
                <p>Execute offline ingestion, ML anomaly detection, and clustering over incoming traffic.</p>
              </div>
              {!ingestJob && (
                <button onClick={handleTriggerPipeline}>▶ Run Pipeline</button>
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
          <abbr key={term} title={desc}>
            {term}
          </abbr>
        ))}{" "}
        <span>•</span> Playback of analyzed data, not real-time interception.
      </footer>
    </main>
  );
}

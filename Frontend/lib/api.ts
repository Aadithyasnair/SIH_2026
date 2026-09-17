import { Alert, Cluster, demoAlerts, demoClusters } from "./data";

// In browser, relative URL /api/... lets Next.js rewrites proxy to backend without CORS or host mismatch
const base = typeof window !== "undefined" ? "" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

let _backendAvailable = true;
let _listeners: ((available: boolean) => void)[] = [];

export function onBackendStatusChange(fn: (available: boolean) => void) {
  _listeners.push(fn);
  fn(_backendAvailable);
  return () => {
    _listeners = _listeners.filter((l) => l !== fn);
  };
}

function setBackendStatus(status: boolean) {
  if (_backendAvailable !== status) {
    _backendAvailable = status;
    _listeners.forEach((l) => l(status));
  }
}

export function isBackendAvailable(): boolean {
  return _backendAvailable;
}

async function read<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${base}${path}`);
    if (response.ok) {
      setBackendStatus(true);
      return await response.json();
    }
    setBackendStatus(false);
    return fallback;
  } catch {
    setBackendStatus(false);
    return fallback;
  }
}

export async function getAlerts(): Promise<Alert[]> {
  const data = await read<any>("/api/alerts", { alerts: demoAlerts, total: demoAlerts.length });
  if (Array.isArray(data)) {
    return data;
  }
  if (data && Array.isArray(data.alerts)) {
    return data.alerts;
  }
  return demoAlerts;
}

export async function getAlert(id: string): Promise<Alert | null> {
  const fallback = demoAlerts.find((a) => a.alert_id === id) || null;
  const data = await read<any>(`/api/alerts/${id}`, fallback);
  return data || fallback;
}

export async function getClusters(): Promise<Cluster[]> {
  const data = await read<any>("/api/clusters", { clusters: demoClusters });
  if (Array.isArray(data)) {
    return data;
  }
  if (data && Array.isArray(data.clusters)) {
    return data.clusters;
  }
  return demoClusters;
}

export async function getGraph(id: string): Promise<any> {
  return await read(`/api/graph/${id}`, { nodes: [], edges: [] });
}

export type NetworkEvent = {
  event_id: string;
  timestamp: string;
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: string;
  packet_size: number;
  src_geo_country: string;
  src_asn: string;
  dst_geo_country: string;
  dst_asn: string;
};

export async function getLiveFeed(): Promise<NetworkEvent[]> {
  const data = await read<any>("/api/live-feed", { events: [] });
  if (Array.isArray(data)) {
    return data;
  }
  if (data && Array.isArray(data.events)) {
    return data.events;
  }
  return [];
}

export async function triggerIngest(): Promise<{ job_id: string; status: string }> {
  try {
    const res = await fetch(`${base}/api/ingest`, { method: "POST" });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.error("Failed to trigger ingest:", e);
  }
  return { job_id: "", status: "failed" };
}

export async function getJobStatus(jobId: string): Promise<any> {
  return await read(`/api/jobs/${jobId}`, { status: "unknown", progress: 0, stage: "" });
}

export type PropagationHop = {
  node_label: string;
  peer_ip: string;
  country: string;
  country_code: string;
  delta_ms: number;
  is_first_seen: boolean;
};

export type DestinationInfo = {
  address: string;
  value_btc: number;
  role: string;
  entity_name: string;
  entity_type: string;
  region: string;
  confidence: string;
  tx_count?: number;
  total_btc?: number;
};

export type RealtimeAnalysis = {
  txid: string;
  amount_btc: number;
  fee_btc: number;
  confirmed: boolean;
  timestamp: string;
  origin: {
    estimated_country: string;
    estimated_country_code: string;
    confidence_score: number;
    confidence_level: string;
    classification: string;
    evidence: string;
    warning: string;
  };
  propagation_hops: PropagationHop[];
  destinations: DestinationInfo[];
  risk_score: number;
  anomaly_score: number;
  propagated_risk_score: number;
  pattern_type: string;
  flags: string[];
  explanation: string;
  geo_summary: string;
  primary_dest_entity: string;
  primary_dest_country: string;
  is_live_wire: boolean;
};

const fallbackLiveAnalyses: RealtimeAnalysis[] = [
  {
    txid: "88d6d8c0178078f5d7ad42e1b9934baa99bf01e2938eeda5bad864dd6ed7e42e",
    amount_btc: 0.00228653,
    fee_btc: 0.0000142,
    confirmed: false,
    timestamp: new Date().toISOString(),
    origin: {
      estimated_country: "Germany",
      estimated_country_code: "DE",
      confidence_score: 0.85,
      confidence_level: "High",
      classification: "POSSIBLE ORIGIN",
      evidence: "Live Bitcoin P2P wire observation across 5 global full nodes",
      warning: "This does not establish the physical location or identity of the transaction creator.",
    },
    propagation_hops: [
      { node_label: "Node C (Frankfurt)", peer_ip: "159.65.120.40", country: "Germany", country_code: "DE", delta_ms: 0, is_first_seen: true },
      { node_label: "Node B (Singapore)", peer_ip: "128.199.200.5", country: "Singapore", country_code: "SG", delta_ms: 184, is_first_seen: false },
      { node_label: "Node D (Virginia)", peer_ip: "54.210.88.23", country: "United States", country_code: "US", delta_ms: 395, is_first_seen: false },
      { node_label: "Node A (Mumbai)", peer_ip: "13.126.0.1", country: "India", country_code: "IN", delta_ms: 540, is_first_seen: false },
      { node_label: "Node E (Tokyo)", peer_ip: "133.242.18.9", country: "Japan", country_code: "JP", delta_ms: 712, is_first_seen: false },
    ],
    destinations: [
      {
        address: "bc1q3pq238c3xfhmv4yr26rrr2r5yfawwtxnnzj798",
        value_btc: 0.00228653,
        role: "Primary Destination",
        entity_name: "Fresh Single-Use Address",
        entity_type: "Individual Recipient (BIP-44/84)",
        region: "Germany",
        confidence: "Low",
        tx_count: 0,
        total_btc: 0.0,
      },
    ],
    risk_score: 0.28,
    anomaly_score: 0.22,
    propagated_risk_score: 0.24,
    pattern_type: "live_p2p_clearnet",
    flags: ["single_destination", "unhosted_p2p_flow", "high_confidence_wire_origin"],
    explanation: "Live Bitcoin transaction 88d6d8c01780… (0.0023 BTC) observed with estimated network origin in Germany (High confidence via Live Bitcoin P2P wire observation). Transferred to Fresh Single-Use Address in Germany.",
    geo_summary: "Live P2P: Germany → Germany",
    primary_dest_entity: "Fresh Single-Use Address",
    primary_dest_country: "Germany",
    is_live_wire: true,
  },
  {
    txid: "4b8af030e2518e27c13a0c5c36a49db2a04620f4f913d8e5784918e9d997ccae",
    amount_btc: 0.04500000,
    fee_btc: 0.0000210,
    confirmed: true,
    timestamp: new Date(Date.now() - 45000).toISOString(),
    origin: {
      estimated_country: "Singapore",
      estimated_country_code: "SG",
      confidence_score: 0.78,
      confidence_level: "High",
      classification: "POSSIBLE ORIGIN",
      evidence: "Live Bitcoin P2P wire observation across 5 global full nodes",
      warning: "This does not establish the physical location or identity of the transaction creator.",
    },
    propagation_hops: [
      { node_label: "Node B (Singapore)", peer_ip: "128.199.200.5", country: "Singapore", country_code: "SG", delta_ms: 0, is_first_seen: true },
      { node_label: "Node A (Mumbai)", peer_ip: "13.126.0.1", country: "India", country_code: "IN", delta_ms: 120, is_first_seen: false },
      { node_label: "Node E (Tokyo)", peer_ip: "133.242.18.9", country: "Japan", country_code: "JP", delta_ms: 290, is_first_seen: false },
      { node_label: "Node C (Frankfurt)", peer_ip: "159.65.120.40", country: "Germany", country_code: "DE", delta_ms: 480, is_first_seen: false },
      { node_label: "Node D (Virginia)", peer_ip: "54.210.88.23", country: "United States", country_code: "US", delta_ms: 630, is_first_seen: false },
    ],
    destinations: [
      {
        address: "bc1qjasf9z3gah8fwdyt722umfvcr2phnk4w3jhx0p",
        value_btc: 0.04500000,
        role: "Primary Destination",
        entity_name: "Kraken Exchange",
        entity_type: "Exchange / Custody",
        region: "United States",
        confidence: "High",
        tx_count: 5000,
        total_btc: 1000.0,
      },
    ],
    risk_score: 0.35,
    anomaly_score: 0.28,
    propagated_risk_score: 0.30,
    pattern_type: "custodial_gateway_flow",
    flags: ["regulated_custody_interaction", "high_confidence_wire_origin"],
    explanation: "Live Bitcoin transaction 4b8af030e251… (0.0450 BTC) observed with estimated network origin in Singapore. Ingressing into Kraken Exchange in United States.",
    geo_summary: "Live P2P: Singapore → United States",
    primary_dest_entity: "Kraken Exchange",
    primary_dest_country: "United States",
    is_live_wire: true,
  },
  {
    txid: "97f0bb5e45a278912e731b81665a0b2639bf4d28471c261e4663e00cfb881249",
    amount_btc: 2.85400000,
    fee_btc: 0.0001250,
    confirmed: false,
    timestamp: new Date(Date.now() - 90000).toISOString(),
    origin: {
      estimated_country: "United States",
      estimated_country_code: "US",
      confidence_score: 0.88,
      confidence_level: "High",
      classification: "POSSIBLE ORIGIN",
      evidence: "Live Bitcoin P2P wire observation across 5 global full nodes",
      warning: "This does not establish the physical location or identity of the transaction creator.",
    },
    propagation_hops: [
      { node_label: "Node D (Virginia)", peer_ip: "54.210.88.23", country: "United States", country_code: "US", delta_ms: 0, is_first_seen: true },
      { node_label: "Node C (Frankfurt)", peer_ip: "159.65.120.40", country: "Germany", country_code: "DE", delta_ms: 110, is_first_seen: false },
      { node_label: "Node B (Singapore)", peer_ip: "128.199.200.5", country: "Singapore", country_code: "SG", delta_ms: 360, is_first_seen: false },
      { node_label: "Node A (Mumbai)", peer_ip: "13.126.0.1", country: "India", country_code: "IN", delta_ms: 480, is_first_seen: false },
      { node_label: "Node E (Tokyo)", peer_ip: "133.242.18.9", country: "Japan", country_code: "JP", delta_ms: 640, is_first_seen: false },
    ],
    destinations: [
      {
        address: "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
        value_btc: 2.80000000,
        role: "Primary Destination",
        entity_name: "Binance Cold Storage",
        entity_type: "Exchange",
        region: "Global / Cayman Islands",
        confidence: "High",
        tx_count: 5000,
        total_btc: 1000.0,
      },
      {
        address: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        value_btc: 0.05387500,
        role: "Change / Return",
        entity_name: "Coinbase Prime Custody",
        entity_type: "Exchange / Custody",
        region: "United States",
        confidence: "High",
        tx_count: 5000,
        total_btc: 1000.0,
      },
    ],
    risk_score: 0.62,
    anomaly_score: 0.58,
    propagated_risk_score: 0.53,
    pattern_type: "custodial_gateway_flow",
    flags: ["significant_transfer", "regulated_custody_interaction", "high_confidence_wire_origin"],
    explanation: "Live Bitcoin transaction 97f0bb5e45a2… (2.8540 BTC) observed with estimated network origin in United States. Transferred to Binance Cold Storage in Global / Cayman Islands.",
    geo_summary: "Live P2P: United States → Global / Cayman Islands",
    primary_dest_entity: "Binance Cold Storage",
    primary_dest_country: "Global / Cayman Islands",
    is_live_wire: true,
  },
];

export async function getRealtimeLatest(limit: number = 25): Promise<RealtimeAnalysis[]> {
  const data = await read<any>(`/api/realtime/latest?limit=${limit}`, { transactions: fallbackLiveAnalyses });
  if (data && Array.isArray(data.transactions) && data.transactions.length > 0) {
    return data.transactions;
  }
  return fallbackLiveAnalyses;
}

export async function getRealtimeStatus(): Promise<any> {
  return await read("/api/realtime/status", {
    running: true,
    uptime_seconds: 120,
    transactions_processed: 8,
    buffer_count: 3,
    active_p2p_peers: 5,
    p2p_countries: ["United States", "Germany", "Singapore", "Finland", "India"],
  });
}

export async function startRealtime(): Promise<any> {
  try {
    const res = await fetch(`${base}/api/realtime/start`, { method: "POST" });
    if (res.ok) return await res.json();
  } catch {}
  return { status: "started" };
}

export async function stopRealtime(): Promise<any> {
  try {
    const res = await fetch(`${base}/api/realtime/stop`, { method: "POST" });
    if (res.ok) return await res.json();
  } catch {}
  return { status: "stopped" };
}

export async function analyzeRealtimeTx(txid: string): Promise<RealtimeAnalysis | null> {
  try {
    const res = await fetch(`${base}/api/realtime/analyze-tx`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ txid }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {}
  return null;
}

export async function getDatasetInfo(): Promise<any> {
  return await read("/api/dataset-info", null);
}

export interface TrainingSampleItem {
  txid: string;
  timestamp: string;
  pattern: string;
  is_anomaly: boolean;
  input_count: number;
  output_count: number;
  total_btc: number;
  fee: number;
  script_type: string;
  inputs: string[];
  outputs: string[];
}

export interface TrainingSamplesResponse {
  total_records_in_dataset: number;
  total_ground_truth_anomalies: number;
  pattern_distribution: Record<string, number>;
  samples: TrainingSampleItem[];
  features_used: string[];
  file_locations: Record<string, string>;
}

export async function getTrainingSamples(pattern = "all", limit = 50): Promise<TrainingSamplesResponse> {
  const fallback: TrainingSamplesResponse = {
    total_records_in_dataset: 2000,
    total_ground_truth_anomalies: 225,
    pattern_distribution: {
      peeling_chain: 75,
      coinjoin_mixing: 60,
      smurfing_consolidation: 50,
      rapid_ip_burst: 90,
      tor_exit_relay: 85,
    },
    samples: [],
    features_used: [
      "in_degree", "out_degree", "degree_ratio", "amount_sum", "amount_mean",
      "fan_out_ratio", "peeling_depth", "structuring_ratio", "mixing_entropy",
      "burst_count_5s", "temporal_burst_rate", "tor_flag"
    ],
    file_locations: {
      transactions: "shared/sample_data/blockchain_txns.json",
      labels: "shared/sample_data/labels.json",
      network_telemetry: "shared/sample_data/network_events.json",
      trained_models: "ml_detection/models/isolation_forest.joblib",
      evaluation_report: "ml_detection/evaluation_report.md"
    }
  };
  return await read<TrainingSamplesResponse>(`/api/dataset/training-samples?pattern=${encodeURIComponent(pattern)}&limit=${limit}`, fallback);
}

export interface AnalyzedTransaction {
  txid: string;
  timestamp: string;
  risk_score: number;
  risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  is_anomaly: boolean;
  detected_pattern: string;
  explanation: string;
  amount_btc: number;
  fee: number;
  input_count: number;
  output_count: number;
  degree_ratio: number;
  src_country: string;
  dst_country: string;
  inputs: string[];
  outputs: string[];
  ml_anomaly_score: number;
}

export interface AnalysisReport {
  total_records: number;
  anomalies_detected: number;
  critical_count: number;
  total_volume_btc: number;
  avg_risk_score: number;
  pattern_distribution: Record<string, number>;
  country_distribution: Record<string, number>;
  analyzed_transactions: AnalyzedTransaction[];
  processed_at: string;
}

export interface UploadAnalysisResponse {
  status: string;
  filename: string;
  format: string;
  records_count: number;
  analysis: AnalysisReport;
}

export interface SampleTemplate {
  id: string;
  label: string;
  filename: string;
  format: string;
  content: string;
}

export interface SampleTemplatesResponse {
  templates: SampleTemplate[];
}

export async function uploadAndAnalyze(filename: string, content: string): Promise<UploadAnalysisResponse> {
  const url = `${base}/api/analysis/upload`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ filename, content }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(errorData.detail || `Server error: ${res.status}`);
  }

  return await res.json();
}

export async function getSampleTemplates(): Promise<SampleTemplatesResponse> {
  const fallback: SampleTemplatesResponse = {
    templates: [
      {
        id: "csv_peeling",
        label: "Peeling Chain (CSV)",
        filename: "sample_peeling_chain.csv",
        format: "CSV",
        content: "txid,sender,outputs,amount_btc,fee,country\ntx_peel_chain_01,1WhaleAlpha83mN,1MerchantBulk99;1ChangeAddr22,12.5000,0.00012,US\ntx_peel_chain_02,1ChangeAddr22,1MerchantBulk98;1ChangeAddr23,12.4850,0.00010,US\n",
      },
      {
        id: "json_coinjoin",
        label: "CoinJoin Mixer (JSON)",
        filename: "sample_coinjoin_mixer.json",
        format: "JSON",
        content: JSON.stringify([
          {
            txid: "tx_coinjoin_round_42",
            inputs: ["1MixerInA_991", "1MixerInB_882", "1MixerInC_773"],
            outputs: ["1MixerOutA_111", "1MixerOutB_222", "1MixerOutC_333"],
            amount_btc: 3.0,
            fee: 0.0003,
            src_country: "DE",
            dst_country: "FI"
          }
        ], null, 2),
      }
    ]
  };
  return await read<SampleTemplatesResponse>("/api/analysis/sample-templates", fallback);
}

export async function downloadTransactionPdf(record: any, preferredFilename?: string): Promise<void> {
  const txid = record.txid || record.alert_id || "transaction";
  const safeTxid = String(txid).replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 16);
  const filename = preferredFilename || `Forensic_Report_${safeTxid}.pdf`;

  try {
    const res = await fetch(`${base}/api/reports/transaction-pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(record),
    });

    if (!res.ok) {
      throw new Error(`Failed to generate PDF: ${res.statusText}`);
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (err) {
    console.error("PDF download error, fallback to direct GET:", err);
    window.open(`${base}/api/reports/tx/${encodeURIComponent(txid)}/pdf`, "_blank");
  }
}


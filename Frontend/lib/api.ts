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

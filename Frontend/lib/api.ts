import { Alert, Cluster, demoAlerts, demoClusters } from "./data";
const base=process.env.NEXT_PUBLIC_API_URL ?? "";
async function read<T>(path:string, fallback:T):Promise<T>{ try { const response=await fetch(`${base}${path}`); return response.ok?response.json():fallback; } catch { return fallback; } }
export const getAlerts=()=>read<Alert[]>("/api/alerts",demoAlerts);
export const getAlert=(id:string)=>read<Alert>(`/api/alerts/${id}`,demoAlerts.find(a=>a.alert_id===id)!);
export const getClusters=()=>read<Cluster[]>("/api/clusters",demoClusters);
export const getGraph=(id:string)=>read(`/api/graph/${id}`,{});
export const getLiveFeed=()=>read("/api/live-feed",[]);

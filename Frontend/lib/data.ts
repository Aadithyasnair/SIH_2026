export type Alert={alert_id:string;txid:string;involved_addresses:string[];risk_score:number;anomaly_score:number;propagated_risk_score:number;pattern_type:string|null;cluster_id:string|null;flags:string[];explanation:string;timestamp:string;geo_summary:string};
export type Cluster={cluster_id:string;label:string;member_addresses:string[];member_count:number;avg_risk_score:number;description:string;clustering_method:string};
export const getRisk=(score:number)=>{
  if(score>0.7) return {key:"high",label:"High risk",color:"#ff5267",border:"#ff5267"};
  if(score>=0.4) return {key:"medium",label:"Medium risk",color:"#ffbe3d",border:"#ffbe3d"};
  return {key:"low",label:"Low risk",color:"#4be99a",border:"#4be99a"};
};
export const getRiskColor=(score:number)=>{
  // Continuous smooth interpolation: green (0.0) -> yellow (0.5) -> red (1.0)
  const clamped = Math.max(0, Math.min(1, score));
  if (clamped < 0.5) {
    const t = clamped * 2;
    // 75, 233, 154 (#4be99a) to 255, 190, 61 (#ffbe3d)
    const r = Math.round(75 + (255 - 75) * t);
    const g = Math.round(233 + (190 - 233) * t);
    const b = Math.round(154 + (61 - 154) * t);
    return `rgb(${r}, ${g}, ${b})`;
  } else {
    const t = (clamped - 0.5) * 2;
    // 255, 190, 61 (#ffbe3d) to 255, 82, 103 (#ff5267)
    const r = 255;
    const g = Math.round(190 + (82 - 190) * t);
    const b = Math.round(61 + (103 - 61) * t);
    return `rgb(${r}, ${g}, ${b})`;
  }
};
export const isDarknetOrTor = (item: any): boolean => {
  if (!item) return false;
  if (item.src_port === 9050 || item.src_port === 9051 || item.src_port === 9150) return true;
  if (item.dst_port === 9050 || item.dst_port === 9051 || item.dst_port === 9150) return true;
  if (typeof item.src_asn === "string" && item.src_asn.toLowerCase().includes("tor")) return true;
  if (typeof item.dst_asn === "string" && item.dst_asn.toLowerCase().includes("tor")) return true;
  const flags = Array.isArray(item.flags) ? item.flags.join(" ") : "";
  const text = `${flags} ${item.explanation || ""} ${item.geo_summary || ""} ${item.label || ""} ${item.description || ""}`.toLowerCase();
  return text.includes("tor") || text.includes("onion") || text.includes("darknet") || text.includes("dnm") || (Array.isArray(item.flags) && item.flags.some((f: string) => f.includes("tor") || f.includes("darknet")));
};


export const demoAlerts:Alert[]=[
 {alert_id:"a1",txid:"b6f123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",involved_addresses:["1PeelAddr1xxxx","1PeelAddr2xxxx"],risk_score:1,anomaly_score:.88,propagated_risk_score:.75,pattern_type:"peeling_chain",cluster_id:"c1",flags:["peeling_chain_detected","suspicious_layering"],explanation:"Funds were passed through five wallets while leaving small remainders, a pattern consistent with layering to obscure a money trail.",timestamp:"2026-09-14T00:00:00Z",geo_summary:"Funds traced through Germany, Nigeria and Singapore"},
 {alert_id:"a2",txid:"c7f987654321fedcba987654321fedcba987654321fedcba987654321fedcba",involved_addresses:["1MixerIn1xxxx","1MixerOut1xxxx"],risk_score:.90,anomaly_score:.92,propagated_risk_score:.3,pattern_type:"coinjoin_mixing",cluster_id:"c2",flags:["coinjoin_mixing_detected","equal_amount_distribution"],explanation:"Twelve wallets combined equal amounts, which is consistent with a mixing service designed to break the sender-receiver link.",timestamp:"2026-09-14T00:05:00Z",geo_summary:"Funds traced between Panama and Switzerland"},
 {alert_id:"a3",txid:"d8a112233445566778899aabbccddeeff112233445566778899aabbccddeeff",involved_addresses:["1Hop2RiskAddrxxxx"],risk_score:.7045,anomaly_score:.65,propagated_risk_score:.82,pattern_type:"none",cluster_id:"c3",flags:["propagated_illicit_link"],explanation:"The wallet is two hops from confirmed illicit activity and received funds that trace back to it.",timestamp:"2026-09-14T00:10:00Z",geo_summary:"Funds traced between Cyprus and Russian Federation"},
 {alert_id:"a4",txid:"e9b2233445566778899aabbccddeeff00112233445566778899aabbccddeeff",involved_addresses:["1HighValAddrxxxx"],risk_score:.623,anomaly_score:.79,propagated_risk_score:.15,pattern_type:"none",cluster_id:null,flags:["high_value_burst"],explanation:"This wallet moved an unusually high volume in a short period, including a transfer over three times its usual amount.",timestamp:"2026-09-14T00:15:00Z",geo_summary:"Transaction activity localized to Germany"},
 {alert_id:"a5",txid:"f0d33445566778899aabbccddeeff00112233445566778899aabbccddeeff01",involved_addresses:["1LowRiskAddrxxxx"],risk_score:.31,anomaly_score:.28,propagated_risk_score:.22,pattern_type:"none",cluster_id:"c4",flags:["ip_reuse"],explanation:"The transaction shares infrastructure with several known addresses and needs a low-priority review.",timestamp:"2026-09-14T00:20:00Z",geo_summary:"Transaction traced from United States to Singapore"},
 {alert_id:"a6",txid:"fe882233445566778899aabbccddeeff00112233445566778899aabbccddeeff99",involved_addresses:["1TorRelayVendor1xxxx","1TorRelayVendor2xxxx"],risk_score:.94,anomaly_score:.96,propagated_risk_score:.89,pattern_type:"darknet_vendor_flow",cluster_id:"c2",flags:["tor_exit_relay","darknet_market_proceeds","anonymized_p2p_broadcast"],explanation:"Transaction broadcast via Tor Onion exit relay (port 9050) directly connected to a Darknet Market vendor wallet cluster.",timestamp:"2026-09-14T00:25:00Z",geo_summary:"🧅 Tor Anonymity Network → Germany (Exit Relay)"}
];
export const demoClusters:Cluster[]=[
 {cluster_id:"c1",label:"Possible Mixing Service",member_addresses:["a","b","c","d","e","f","g","h","i","j","k","l"],member_count:12,avg_risk_score:.92,description:"Repeated multi-hop transfers and shared inputs link these addresses.",clustering_method:"common_input_ownership + graph embedding"},
 {cluster_id:"c2",label:"Darknet Market",member_addresses:["a","b","c","d","e","f","g"],member_count:7,avg_risk_score:.87,description:"The group shows rapid consolidation and matching transaction patterns.",clustering_method:"graph embedding"},
 {cluster_id:"c3",label:"International Transfer",member_addresses:["a","b","c","d","e"],member_count:5,avg_risk_score:.63,description:"Connected funds cross several observed network regions.",clustering_method:"time window correlation"},
 {cluster_id:"c4",label:"Merchant Services",member_addresses:["a","b","c","d"],member_count:4,avg_risk_score:.31,description:"A low-risk group with regular transaction cadence.",clustering_method:"common input ownership"},
 {cluster_id:"c5",label:"New Wallet Cluster",member_addresses:["a","b","c","d","e","f"],member_count:6,avg_risk_score:.48,description:"Recently active wallets associated by shared counterparties.",clustering_method:"graph embedding"}
];

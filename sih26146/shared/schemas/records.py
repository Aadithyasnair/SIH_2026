"""
Shared Data Contracts for SIH26146
Official Pydantic v2 models matching NTRO Problem Statement fields exactly.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class NetworkEvent(BaseModel):
    event_id: str = Field(..., description="UUID string identifying the network event")
    timestamp: str = Field(..., description="ISO8601 UTC timestamp")
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str = Field(..., description="TCP, UDP, etc.")
    packet_size: int
    src_geo_country: str = Field(..., description="ISO 2-letter country code or name")
    src_asn: str = Field(..., description="Autonomous System Number, e.g. AS13335")
    dst_geo_country: str
    dst_asn: str


class BlockchainTxn(BaseModel):
    txid: str = Field(..., description="Bitcoin transaction hash")
    timestamp: str = Field(..., description="ISO8601 UTC timestamp")
    input_addresses: List[str] = Field(..., description="List of source input addresses")
    output_addresses: List[str] = Field(..., description="List of destination output addresses")
    input_amounts: List[float] = Field(..., description="List of amounts corresponding to inputs in BTC")
    output_amounts: List[float] = Field(..., description="List of amounts corresponding to outputs in BTC")
    fee: float = Field(..., description="Transaction fee in BTC")
    script_type: str = Field(..., description="P2PKH, P2SH, P2WPKH, P2TR, etc.")


class CorrelationEdge(BaseModel):
    edge_id: str = Field(..., description="UUID string identifying the correlation edge")
    network_event_id: str = Field(..., description="Referenced NetworkEvent.event_id")
    txid: str = Field(..., description="Referenced BlockchainTxn.txid")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    correlation_type: str = Field(..., description="e.g. time_window, ip_reuse, session_burst")


class Cluster(BaseModel):
    cluster_id: str = Field(..., description="Unique identifier for the cluster")
    label: str = Field(..., description="Human-readable summary label, e.g. 'Possible mixing service'")
    member_addresses: List[str] = Field(..., description="List of Bitcoin wallet addresses in this cluster")
    member_count: int = Field(..., description="Total count of member addresses")
    avg_risk_score: float = Field(..., ge=0.0, le=1.0, description="Average risk score of member wallets")
    description: str = Field(..., description="Plain-language explanation of why these addresses are grouped")
    clustering_method: str = Field(..., description="e.g. 'common_input_ownership+node2vec_embedding'")


class Alert(BaseModel):
    alert_id: str = Field(..., description="UUID string identifying the alert")
    txid: str = Field(..., description="Transaction ID associated with the alert")
    involved_addresses: List[str] = Field(..., description="List of addresses involved in the alert")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Final combined risk score [0, 1]")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="ML anomaly score [0, 1]")
    propagated_risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk propagated from seed illicit wallets [0, 1]")
    pattern_type: Optional[str] = Field(None, description="'peeling_chain', 'coinjoin_mixing', or 'none'")
    cluster_id: Optional[str] = Field(None, description="Associated cluster_id if any")
    flags: List[str] = Field(default_factory=list, description="Descriptive trigger flags")
    explanation: str = Field(..., description="Plain-language investigative explanation")
    timestamp: str = Field(..., description="ISO8601 UTC timestamp")
    geo_summary: str = Field(..., description="e.g. 'traced to 3 countries'")

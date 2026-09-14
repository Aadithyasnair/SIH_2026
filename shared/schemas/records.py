"""
Shared Data Contracts for SIH26146
Official Pydantic v2 models matching NTRO Problem Statement fields exactly.
"""
import uuid
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator


class NetworkEvent(BaseModel):
    event_id: str = Field(..., description="UUID string identifying the network event")
    timestamp: str = Field(..., description="ISO8601 UTC timestamp")
    src_ip: str
    dst_ip: str
    src_port: int = Field(default=50000)
    dst_port: int = Field(default=8333)
    protocol: str = Field(default="TCP", description="TCP, UDP, etc.")
    packet_size: int = Field(default=1024)
    src_geo_country: str = Field(default="US", description="ISO 2-letter country code or name")
    src_asn: str = Field(default="AS0000", description="Autonomous System Number, e.g. AS13335")
    dst_geo_country: str = Field(default="US")
    dst_asn: str = Field(default="AS0000")

    @model_validator(mode='before')
    @classmethod
    def populate_defaults_or_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "port" in data and "dst_port" not in data:
                data["dst_port"] = data["port"]
            if "port" in data and "src_port" not in data:
                data["src_port"] = 50000
        return data

    @property
    def port(self) -> int:
        return self.dst_port


class BlockchainTxn(BaseModel):
    txid: str = Field(..., description="Bitcoin transaction hash")
    timestamp: str = Field(..., description="ISO8601 UTC timestamp")
    input_addresses: List[str] = Field(..., description="List of source input addresses")
    output_addresses: List[str] = Field(..., description="List of destination output addresses")
    input_amounts: List[float] = Field(..., description="List of amounts corresponding to inputs in BTC")
    output_amounts: List[float] = Field(..., description="List of amounts corresponding to outputs in BTC")
    fee: float = Field(default=0.0001, description="Transaction fee in BTC")
    script_type: str = Field(default="P2PKH", description="P2PKH, P2SH, P2WPKH, P2TR, etc.")

    @model_validator(mode='before')
    @classmethod
    def populate_from_single_wallet(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "wallet_from" in data and "input_addresses" not in data:
                data["input_addresses"] = [data["wallet_from"]]
            if "wallet_to" in data and "output_addresses" not in data:
                data["output_addresses"] = [data["wallet_to"]]
            if "amount_btc" in data and "input_amounts" not in data:
                data["input_amounts"] = [float(data["amount_btc"])]
            if "amount_btc" in data and "output_amounts" not in data:
                data["output_amounts"] = [float(data["amount_btc"])]
        return data

    @property
    def wallet_from(self) -> str:
        return self.input_addresses[0] if self.input_addresses else ""

    @property
    def wallet_to(self) -> str:
        return self.output_addresses[0] if self.output_addresses else ""

    @property
    def amount_btc(self) -> float:
        return sum(self.output_amounts) if self.output_amounts else 0.0


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
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="UUID string identifying the alert")
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

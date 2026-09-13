import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class NetworkEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str = "TCP"
    packet_size: int = 0
    src_geo_country: Optional[str] = None
    src_asn: Optional[str] = None
    dst_geo_country: Optional[str] = None
    dst_asn: Optional[str] = None

class BlockchainTxn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    txid: str
    timestamp: str
    input_addresses: List[str]
    output_addresses: List[str]
    input_amounts: List[float]
    output_amounts: List[float]
    fee: float = 0.0
    script_type: str = "P2PKH"

class CorrelationEdge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    network_event_id: str
    txid: str
    confidence: float
    correlation_type: str = "time_window"

class Cluster(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    cluster_id: str
    label: str
    member_addresses: List[str]
    member_count: int
    avg_risk_score: float
    description: str
    clustering_method: str

class Alert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    txid: str
    involved_addresses: List[str]
    risk_score: float
    anomaly_score: float
    propagated_risk_score: float = 0.0
    pattern_type: Optional[str] = None
    cluster_id: Optional[str] = None
    flags: List[str] = Field(default_factory=list)
    explanation: str
    timestamp: str
    geo_summary: str

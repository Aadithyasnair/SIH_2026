"""
Consolidated Data Generator wrapper for SIH26146.
Delegates to the canonical generator: ingestion.synthetic_generator.SyntheticDataGenerator.
Eliminates duplicate generators across modules.
"""
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ingestion.synthetic_generator import (
    SyntheticDataGenerator as CanonicalGenerator,
    generate_wallet_address,
    generate_ip,
)
from shared.schemas.records import NetworkEvent, BlockchainTxn


class SyntheticDataGenerator(CanonicalGenerator):
    """Thin compatibility wrapper delegating to the canonical ingestion generator."""
    pass


def generate_full_dataset(
    output_dir: Path,
    network_count: int = 5000,
    txn_count: int = 2000,
    anomaly_ratio: float = 0.07,
) -> Dict[str, Any]:
    """Generates dataset using the canonical generator."""
    gen = CanonicalGenerator(
        network_count=network_count,
        txn_count=txn_count,
        anomaly_ratio=anomaly_ratio,
        inject_anomalies=True,
    )
    events, txns, labels = gen.generate()
    return {
        "network_events": [e.model_dump() for e in events],
        "blockchain_txns": [t.model_dump() for t in txns],
        "labels": labels,
    }

#!/usr/bin/env python3
"""
Validation script for SIH26146 shared sample datasets.
Validates network_events.json, blockchain_txns.json, correlation_edges.json, and clusters.json
against the official Pydantic models.
"""
import json
import sys
from pathlib import Path
from pydantic import ValidationError

try:
    from sih26146.shared.schemas.records import (
        NetworkEvent,
        BlockchainTxn,
        CorrelationEdge,
        Cluster,
        Alert
    )
except ImportError:
    # Allow running directly from file location
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from sih26146.shared.schemas.records import (
        NetworkEvent,
        BlockchainTxn,
        CorrelationEdge,
        Cluster,
        Alert
    )

def validate_file(file_path: Path, model_cls):
    if not file_path.exists():
        print(f"[FAIL] {file_path.name} not found.")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        print(f"[FAIL] {file_path.name}: Root element must be a JSON array.")
        return False

    valid_count = 0
    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            print(f"[ERROR] {file_path.name} Record #{idx} is not a dictionary.")
            return False
        try:
            model_cls(**rec)
            valid_count += 1
        except (ValidationError, TypeError) as e:
            print(f"[ERROR] {file_path.name} Record #{idx} validation failed:\n{e}")
            return False

    print(f"All {valid_count} records valid in {file_path.name}")
    return True

def main():
    sample_dir = Path(__file__).resolve().parents[1] / "sample_data"
    all_ok = True

    targets = [
        ("network_events.json", NetworkEvent),
        ("blockchain_txns.json", BlockchainTxn),
        ("correlation_edges.json", CorrelationEdge),
        ("clusters.json", Cluster)
    ]

    for filename, model_cls in targets:
        path = sample_dir / filename
        if not validate_file(path, model_cls):
            all_ok = False

    if not all_ok:
        sys.exit(1)
    print("\n[SUCCESS] Schema validation passed.")

if __name__ == "__main__":
    main()

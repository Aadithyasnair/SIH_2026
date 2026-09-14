"""
Blockchain Parser Module for SIH26146 Data Ingestion
Parses raw blockchain transaction log data (JSON / CSV / Dicts) into validated BlockchainTxn records.
"""

import csv
import json
import uuid
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Union

from ingestion.data_validator import DataValidator
from ingestion.time_aligner import normalize_timestamp
from shared.schemas.records import BlockchainTxn


def parse_blockchain_txns(
    data: Union[str, Path, List[Dict[str, Any]]],
    validator: DataValidator | None = None,
) -> List[BlockchainTxn]:
    """
    Parses raw blockchain transaction data into a list of validated BlockchainTxn models.
    Accepts:
    - Path object or string file path to JSON or CSV file
    - JSON string or CSV formatted string
    - List of raw dictionary records
    """
    if validator is None:
        validator = DataValidator()

    raw_records: List[Dict[str, Any]] = []

    if isinstance(data, (Path, str)):
        path_obj = Path(data) if isinstance(data, str) and (data.endswith(".json") or data.endswith(".csv") or "/" in data or "\\" in data) else None

        if path_obj and path_obj.exists():
            content = path_obj.read_text(encoding="utf-8").strip()
            if path_obj.suffix.lower() == ".csv":
                raw_records = _parse_csv_string(content)
            else:
                raw_records = json.loads(content)
        elif isinstance(data, str):
            content = data.strip()
            if content.startswith("[") or content.startswith("{"):
                loaded = json.loads(content)
                raw_records = loaded if isinstance(loaded, list) else [loaded]
            else:
                raw_records = _parse_csv_string(content)
    elif isinstance(data, list):
        raw_records = data
    else:
        raise ValueError(f"Unsupported data type for blockchain parsing: {type(data)}")

    standardized: List[Dict[str, Any]] = []
    for rec in raw_records:
        if not isinstance(rec, dict):
            validator.quarantined_records.append({"raw_record": str(rec), "error": "Not a dict"})
            continue

        normalized_rec = dict(rec)

        # Generate txid if missing
        if "txid" not in normalized_rec or not normalized_rec["txid"]:
            normalized_rec["txid"] = f"tx_{uuid.uuid4().hex[:16]}"

        # Normalize timestamp if present
        if "timestamp" in normalized_rec:
            try:
                normalized_rec["timestamp"] = normalize_timestamp(normalized_rec["timestamp"])
            except Exception as e:
                validator.quarantined_records.append({"raw_record": rec, "error": f"Bad timestamp: {e}"})
                continue

        # Convert numeric fields
        if "fee" in normalized_rec and normalized_rec["fee"] is not None:
            try:
                normalized_rec["fee"] = float(normalized_rec["fee"])
            except (ValueError, TypeError):
                pass

        if "amount_btc" in normalized_rec and normalized_rec["amount_btc"] is not None:
            try:
                normalized_rec["amount_btc"] = float(normalized_rec["amount_btc"])
            except (ValueError, TypeError):
                pass

        # Handle list conversions if CSV string was passed for list fields
        for list_field in ["input_addresses", "output_addresses"]:
            if list_field in normalized_rec and isinstance(normalized_rec[list_field], str):
                normalized_rec[list_field] = [addr.strip() for addr in normalized_rec[list_field].split(";") if addr.strip()]

        for float_list_field in ["input_amounts", "output_amounts"]:
            if float_list_field in normalized_rec and isinstance(normalized_rec[float_list_field], str):
                try:
                    normalized_rec[float_list_field] = [float(val.strip()) for val in normalized_rec[float_list_field].split(";") if val.strip()]
                except ValueError:
                    pass

        standardized.append(normalized_rec)

    valid_txns, _ = validator.validate_batch(standardized, BlockchainTxn)
    return valid_txns


def _parse_csv_string(csv_text: str) -> List[Dict[str, Any]]:
    """Helper to parse CSV string into list of dicts."""
    reader = csv.DictReader(StringIO(csv_text))
    return [dict(row) for row in reader]

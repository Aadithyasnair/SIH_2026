"""
Network Parser Module for SIH26146 Data Ingestion
Parses raw network log data (JSON / CSV / Dicts) into validated NetworkEvent records.
"""

import csv
import json
import uuid
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Union

from ingestion.data_validator import DataValidator
from ingestion.time_aligner import normalize_timestamp
from shared.schemas.records import NetworkEvent


def parse_network_events(
    data: Union[str, Path, List[Dict[str, Any]]],
    validator: DataValidator | None = None,
) -> List[NetworkEvent]:
    """
    Parses raw network log data into a list of validated NetworkEvent models.
    Accepts:
    - Path object or string file path to JSON or CSV file
    - JSON string or CSV formatted string
    - List of raw dictionary records
    """
    if validator is None:
        validator = DataValidator()

    raw_records: List[Dict[str, Any]] = []

    if isinstance(data, Path):
        path_obj = data
    elif isinstance(data, str) and (data.endswith(".json") or data.endswith(".csv") or data.endswith(".xml") or "/" in data or "\\" in data):
        path_obj = Path(data)
    else:
        path_obj = None

    if path_obj is not None:
        if path_obj.exists():
            content = path_obj.read_text(encoding="utf-8").strip()
            if path_obj.suffix.lower() == ".csv":
                raw_records = _parse_csv_string(content)
            elif path_obj.suffix.lower() == ".xml":
                from ingestion.xml_parser import parse_xml_to_dicts
                raw_records = parse_xml_to_dicts(path_obj)
            else:
                raw_records = json.loads(content)
        elif isinstance(data, str):
            content = data.strip()
            if content.startswith("<"):
                from ingestion.xml_parser import parse_xml_to_dicts
                raw_records = parse_xml_to_dicts(content)
            elif content.startswith("[") or content.startswith("{"):
                loaded = json.loads(content)
                raw_records = loaded if isinstance(loaded, list) else [loaded]
            else:
                raw_records = _parse_csv_string(content)
    elif isinstance(data, list):
        raw_records = data
    else:
        raise ValueError(f"Unsupported data type for network parsing: {type(data)}")

    # Standardize & normalize records before validation
    standardized: List[Dict[str, Any]] = []
    for rec in raw_records:
        if not isinstance(rec, dict):
            validator.quarantined_records.append({"raw_record": str(rec), "error": "Not a dict"})
            continue

        normalized_rec = dict(rec)

        # Generate event_id if missing
        if "event_id" not in normalized_rec or not normalized_rec["event_id"]:
            normalized_rec["event_id"] = f"net_{uuid.uuid4().hex[:12]}"

        # Normalize timestamp if present
        if "timestamp" in normalized_rec:
            try:
                normalized_rec["timestamp"] = normalize_timestamp(normalized_rec["timestamp"])
            except Exception as e:
                validator.quarantined_records.append({"raw_record": rec, "error": f"Bad timestamp: {e}"})
                continue

        # Convert ports and packet size to int if possible
        for int_field in ["src_port", "dst_port", "port", "packet_size"]:
            if int_field in normalized_rec and normalized_rec[int_field] is not None:
                try:
                    normalized_rec[int_field] = int(normalized_rec[int_field])
                except (ValueError, TypeError):
                    pass

        standardized.append(normalized_rec)

    valid_events, _ = validator.validate_batch(standardized, NetworkEvent)
    return valid_events


def _parse_csv_string(csv_text: str) -> List[Dict[str, Any]]:
    """Helper to parse CSV string into list of dicts."""
    reader = csv.DictReader(StringIO(csv_text))
    return [dict(row) for row in reader]

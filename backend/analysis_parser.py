"""
Universal Multi-Format File Parser for SIH26146 Bitcoin Monitoring.
Supports parsing CSV, TSV, JSON (arrays, objects, JSONL), and XML formats.
Normalizes heterogeneous schemas into standard transaction dictionaries.
"""
import csv
import io
import json
import re
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _clean_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _parse_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        # Remove currency symbols or commas if present
        cleaned = re.sub(r"[^\d.-]", "", str(val))
        return float(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


def _parse_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    try:
        cleaned = re.sub(r"[^\d-]", "", str(val))
        return int(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


def _split_addresses(val: Any) -> List[str]:
    """Splits string or list of addresses into clean string list."""
    if isinstance(val, list):
        out = []
        for x in val:
            if isinstance(x, dict):
                addr = x.get("address") or x.get("addr") or x.get("id") or str(x)
                if addr:
                    out.append(str(addr).strip())
            elif x:
                out.append(str(x).strip())
        return out

    s = _clean_str(val)
    if not s:
        return []
    # If JSON formatted array inside string
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return _split_addresses(parsed)
        except Exception:
            pass
    # Split by semicolon, comma, or pipe
    items = re.split(r"[,;|]+", s)
    return [item.strip() for item in items if item.strip()]


def parse_json_content(content: str) -> List[Dict[str, Any]]:
    """Parse JSON strings formatted as arrays, wrapper objects, or JSONL."""
    content = content.strip()
    if not content:
        return []

    # Try standard JSON
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Check for common wrapper keys
            for key in ["transactions", "txs", "data", "events", "records", "items", "rows"]:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # Single transaction object
            return [data]
    except json.JSONDecodeError:
        pass

    # Try JSONL (newline-delimited JSON)
    records = []
    for line in content.splitlines():
        line = line.strip()
        if line:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    records.append(obj)
            except json.JSONDecodeError:
                continue
    if records:
        return records

    raise ValueError("Unable to parse content as JSON or JSON-Lines.")


def parse_csv_content(content: str) -> List[Dict[str, Any]]:
    """Parse CSV/TSV with automatic delimiter detection."""
    content = content.strip()
    if not content:
        return []

    # Detect delimiter
    sample = content[:4096]
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except Exception:
        # Default heuristics: check tab, semicolon, comma
        if "\t" in sample:
            delimiter = "\t"
        elif ";" in sample:
            delimiter = ";"
        elif "|" in sample:
            delimiter = "|"
        else:
            delimiter = ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    records = []
    for row in reader:
        # Clean keys and values
        cleaned_row = {
            _clean_str(k).lower(): _clean_str(v)
            for k, v in row.items()
            if k is not None
        }
        if any(cleaned_row.values()):
            records.append(cleaned_row)
    return records


def parse_xml_content(content: str) -> List[Dict[str, Any]]:
    """Parse XML documents containing repeating transaction or event nodes."""
    content = content.strip()
    if not content:
        return []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise ValueError(f"XML Parsing Error: {str(e)}")

    records = []
    # Candidate tag names for transaction items
    candidate_tags = {
        "transaction", "tx", "txentry", "event", "networkevent", "record", "item", "row", "entry"
    }

    # Search for candidate elements anywhere in tree
    matched_elements = []
    for elem in root.iter():
        tag_name = elem.tag.split("}")[-1].lower()  # strip XML namespaces
        if tag_name in candidate_tags:
            matched_elements.append(elem)

    # If no candidate tags matched, use direct children of root
    if not matched_elements:
        matched_elements = list(root)

    for elem in matched_elements:
        row_dict = {}
        # Include XML attributes
        for k, v in elem.attrib.items():
            row_dict[k.lower()] = v

        # Include child tags
        for child in elem:
            child_tag = child.tag.split("}")[-1].lower()
            text_val = child.text.strip() if child.text else ""
            # If child has children (e.g. <inputs><input>...</input></inputs>)
            if len(child) > 0:
                sub_items = [c.text.strip() for c in child if c.text and c.text.strip()]
                if sub_items:
                    row_dict[child_tag] = sub_items
                else:
                    row_dict[child_tag] = text_val
            else:
                row_dict[child_tag] = text_val

        if row_dict:
            records.append(row_dict)

    return records


def normalize_record(raw: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Standardizes a parsed record from any format into a normalized transaction dictionary.
    Handles aliases across Bitcoin UTXO models and network event records.
    """
    keys = {k.lower(): k for k in raw.keys()}

    def get_first_val(*aliases: str) -> Any:
        for a in aliases:
            if a in keys:
                val = raw[keys[a]]
                if val is not None and str(val).strip() != "":
                    return val
        return None

    # 1. Identifier
    txid = get_first_val("txid", "tx_id", "id", "hash", "transaction_id", "event_id")
    if not txid:
        txid = f"tx_uploaded_{index:04d}_{uuid.uuid4().hex[:6]}"
    else:
        txid = str(txid).strip()

    # 2. Timestamp
    ts_val = get_first_val("timestamp", "time", "date", "datetime", "created_at")
    if ts_val:
        timestamp_str = str(ts_val).strip()
    else:
        timestamp_str = datetime.now(timezone.utc).isoformat()

    # 3. Inputs / Senders
    raw_inputs = get_first_val(
        "inputs", "input_addresses", "from", "sender", "source", "source_address",
        "src_address", "sender_address", "src_ip", "src_addr", "senders"
    )
    input_addrs = _split_addresses(raw_inputs)
    if not input_addrs:
        input_addrs = [f"1AddrSrc_{uuid.uuid4().hex[:8]}"]

    # 4. Outputs / Recipients
    raw_outputs = get_first_val(
        "outputs", "output_addresses", "to", "receiver", "dest", "dest_address",
        "destination", "destination_address", "dst_address", "receiver_address",
        "dst_ip", "dst_addr", "recipients"
    )
    output_addrs = _split_addresses(raw_outputs)
    if not output_addrs:
        output_addrs = [f"1AddrDst_{uuid.uuid4().hex[:8]}"]

    # 5. Amount (BTC)
    amount_val = get_first_val(
        "amount_btc", "amount", "total_btc", "value", "btc", "volume",
        "packet_size", "size"
    )
    amount_btc = _parse_float(amount_val, default=1.0)
    if amount_btc <= 0:
        amount_btc = 1.0

    # 6. Fee
    fee_val = get_first_val("fee", "tx_fee", "transaction_fee", "fees")
    fee = _parse_float(fee_val, default=0.0001)

    # 7. Countries / Geolocation
    src_country = get_first_val("src_country", "source_country", "src_geo_country", "country_from")
    dst_country = get_first_val("dst_country", "dest_country", "destination_country", "dst_geo_country", "country_to")
    country = get_first_val("country", "geo")

    if not src_country and country:
        src_country = country
    if not src_country:
        src_country = "US"  # Fallback standard
    if not dst_country:
        dst_country = "DE" if src_country != "DE" else "GB"

    # 8. Extra network / protocol fields
    protocol = get_first_val("protocol", "proto") or "TCP"
    port = _parse_int(get_first_val("port", "dst_port", "destination_port"), default=8333)
    script_type = get_first_val("script_type", "type") or ("P2PKH" if len(input_addrs) == 1 else "P2WSH")

    return {
        "txid": txid,
        "timestamp": timestamp_str,
        "input_addresses": input_addrs,
        "output_addresses": output_addrs,
        "amount_btc": round(amount_btc, 4),
        "fee": round(fee, 6),
        "src_country": str(src_country).strip().upper()[:2],
        "dst_country": str(dst_country).strip().upper()[:2],
        "protocol": str(protocol).strip().upper(),
        "port": port,
        "script_type": script_type,
        "raw_record": raw,
    }


def parse_uploaded_file(filename: str, content: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    High-level entry point: detects format from extension or content inspection,
    parses records, and normalizes them into standard transactions.

    Returns:
        (detected_format, normalized_transactions)
    """
    fn_lower = filename.lower()
    raw_records: List[Dict[str, Any]] = []
    detected_format = "unknown"

    # Check format by filename extension first
    if fn_lower.endswith(".json") or fn_lower.endswith(".jsonl"):
        detected_format = "JSON"
        raw_records = parse_json_content(content)
    elif fn_lower.endswith(".xml"):
        detected_format = "XML"
        raw_records = parse_xml_content(content)
    elif fn_lower.endswith(".csv") or fn_lower.endswith(".tsv"):
        detected_format = "CSV" if fn_lower.endswith(".csv") else "TSV"
        raw_records = parse_csv_content(content)
    else:
        # Heuristic content detection
        c_strip = content.strip()
        if c_strip.startswith("{") or c_strip.startswith("["):
            detected_format = "JSON"
            raw_records = parse_json_content(content)
        elif c_strip.startswith("<"):
            detected_format = "XML"
            raw_records = parse_xml_content(content)
        else:
            detected_format = "CSV"
            raw_records = parse_csv_content(content)

    if not raw_records:
        raise ValueError(f"No valid records found in {filename} (format: {detected_format}).")

    normalized = [normalize_record(r, idx + 1) for idx, r in enumerate(raw_records)]
    return detected_format, normalized

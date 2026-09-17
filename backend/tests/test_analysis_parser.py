"""
Unit tests for backend analysis_parser and analysis_engine.
Verifies parsing of CSV, JSON, and XML, as well as forensic scoring.
"""
import pytest
from backend.analysis_parser import (
    parse_uploaded_file,
    parse_csv_content,
    parse_json_content,
    parse_xml_content,
)
from backend.analysis_engine import analyze_records


def test_parse_csv_comma():
    csv_data = """txid,from,to,amount,fee,country
tx_1,1AliceAddr,1BobAddr,2.5,0.0001,US
tx_2,1CharlieAddr,1DaveAddr,14.8,0.0002,DE
"""
    fmt, records = parse_uploaded_file("sample.csv", csv_data)
    assert fmt == "CSV"
    assert len(records) == 2
    assert records[0]["txid"] == "tx_1"
    assert records[0]["amount_btc"] == 2.5
    assert records[0]["src_country"] == "US"


def test_parse_csv_semicolon():
    csv_data = """tx_id;source_address;dest_address;amount_btc;fee
tx_peel_1;1SrcAddr;1DstAddr,1ChangeAddr;5.0;0.0005
"""
    fmt, records = parse_uploaded_file("data.csv", csv_data)
    assert fmt == "CSV"
    assert len(records) == 1
    assert records[0]["amount_btc"] == 5.0
    assert len(records[0]["output_addresses"]) == 2


def test_parse_json_array():
    json_data = """[
        {"txid": "tx_c1", "inputs": ["1A", "1B"], "outputs": ["1C"], "amount_btc": 1.25, "src_country": "FI"},
        {"txid": "tx_c2", "inputs": ["1D"], "outputs": ["1E"], "amount_btc": 0.85, "src_country": "NL"}
    ]"""
    fmt, records = parse_uploaded_file("test.json", json_data)
    assert fmt == "JSON"
    assert len(records) == 2
    assert records[0]["txid"] == "tx_c1"
    assert records[0]["src_country"] == "FI"


def test_parse_json_wrapped():
    json_data = """{
        "status": "ok",
        "transactions": [
            {"txid": "tx_wrap_1", "amount": 3.4}
        ]
    }"""
    fmt, records = parse_uploaded_file("wrapped.json", json_data)
    assert fmt == "JSON"
    assert len(records) == 1
    assert records[0]["txid"] == "tx_wrap_1"
    assert records[0]["amount_btc"] == 3.4


def test_parse_xml():
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <transactions>
        <transaction>
            <txid>tx_xml_1</txid>
            <sender>1AliceAddr</sender>
            <receiver>1BobAddr</receiver>
            <amount>7.5</amount>
            <country>FR</country>
        </transaction>
        <transaction>
            <txid>tx_xml_2</txid>
            <sender>1CharlieAddr</sender>
            <receiver>1DaveAddr</receiver>
            <amount>0.15</amount>
            <country>JP</country>
        </transaction>
    </transactions>
    """
    fmt, records = parse_uploaded_file("feed.xml", xml_data)
    assert fmt == "XML"
    assert len(records) == 2
    assert records[0]["txid"] == "tx_xml_1"
    assert records[0]["amount_btc"] == 7.5
    assert records[0]["src_country"] == "FR"


def test_analysis_engine_scoring():
    raw_txs = [
        # Peeling chain
        {
            "txid": "tx_peel_test",
            "input_addresses": ["1PeelSrc"],
            "output_addresses": ["1PeelDstLarge", "1PeelChangeSmall"],
            "amount_btc": 8.0,
            "fee": 0.0001,
            "raw_record": {"type": "peeling_chain"},
        },
        # Smurfing fan-in
        {
            "txid": "tx_smurf_test",
            "input_addresses": ["1A", "1B", "1C", "1D", "1E"],
            "output_addresses": ["1ConsolidateTarget"],
            "amount_btc": 4.5,
            "fee": 0.0001,
            "raw_record": {},
        },
        # Normal
        {
            "txid": "tx_normal_test",
            "input_addresses": ["1NormalSrc"],
            "output_addresses": ["1NormalDst"],
            "amount_btc": 0.5,
            "fee": 0.0001,
            "raw_record": {},
        },
    ]

    report = analyze_records(raw_txs)
    assert report["total_records"] == 3
    assert report["anomalies_detected"] >= 2
    assert "peeling_chain" in report["pattern_distribution"]
    assert "smurfing_consolidation" in report["pattern_distribution"]
    assert report["avg_risk_score"] > 0.40

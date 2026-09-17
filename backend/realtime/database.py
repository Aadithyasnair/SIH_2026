"""
database.py - SQLite storage and caching layer for real-time Bitcoin transaction analysis.
Stores observed transactions, network propagation observations, IP geolocation cache,
and destination entity resolutions.
"""

import sqlite3
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "app.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_PATH) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS live_transactions (
                txid TEXT PRIMARY KEY,
                amount_btc REAL,
                fee_btc REAL,
                estimated_origin_country TEXT,
                confidence_score REAL,
                confidence_level TEXT,
                classification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS live_propagation_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txid TEXT,
                node_label TEXT,
                peer_ip TEXT,
                country TEXT,
                delta_ms INTEGER,
                is_first_seen INTEGER DEFAULT 0,
                FOREIGN KEY (txid) REFERENCES live_transactions (txid)
            );

            CREATE TABLE IF NOT EXISTS live_destinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txid TEXT,
                address TEXT,
                entity_name TEXT,
                entity_type TEXT,
                region TEXT,
                confidence TEXT,
                FOREIGN KEY (txid) REFERENCES live_transactions (txid)
            );

            CREATE TABLE IF NOT EXISTS ip_cache (
                ip TEXT PRIMARY KEY,
                country TEXT,
                country_code TEXT,
                city TEXT,
                org TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS address_cache (
                address TEXT PRIMARY KEY,
                entity_name TEXT,
                entity_type TEXT,
                region TEXT,
                confidence TEXT,
                tx_count INTEGER,
                total_btc REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()

def save_analysis(
    tx_data: Dict[str, Any],
    origin_data: Dict[str, Any],
    propagation_hops: List[Dict[str, Any]],
    destinations: List[Dict[str, Any]],
    db_path: str = DB_PATH
) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO live_transactions (
                txid, amount_btc, fee_btc, estimated_origin_country,
                confidence_score, confidence_level, classification, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tx_data.get("txid"),
            tx_data.get("amount_btc", 0.0),
            tx_data.get("fee_btc", 0.0),
            origin_data.get("estimated_country", "Unknown"),
            origin_data.get("confidence_score", 0.0),
            origin_data.get("confidence_level", "Low"),
            origin_data.get("classification", "UNKNOWN"),
            datetime.now(timezone.utc).isoformat()
        ))

        conn.execute("DELETE FROM live_propagation_observations WHERE txid = ?", (tx_data.get("txid"),))
        conn.execute("DELETE FROM live_destinations WHERE txid = ?", (tx_data.get("txid"),))

        for hop in propagation_hops:
            conn.execute("""
                INSERT INTO live_propagation_observations (
                    txid, node_label, peer_ip, country, delta_ms, is_first_seen
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tx_data.get("txid"),
                hop.get("node_label", "Unknown Node"),
                hop.get("peer_ip", ""),
                hop.get("country", "Unknown"),
                hop.get("delta_ms", 0),
                1 if hop.get("is_first_seen") else 0
            ))

        for dest in destinations:
            conn.execute("""
                INSERT INTO live_destinations (
                    txid, address, entity_name, entity_type, region, confidence
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tx_data.get("txid"),
                dest.get("address", ""),
                dest.get("entity_name", "Unknown Entity"),
                dest.get("entity_type", "Uncategorized"),
                dest.get("region", "Unknown"),
                dest.get("confidence", "Low")
            ))
    conn.close()

def get_transaction_analysis(txid: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    conn = get_connection(db_path)
    tx_row = conn.execute("SELECT * FROM live_transactions WHERE txid = ?", (txid,)).fetchone()
    if not tx_row:
        conn.close()
        return None

    hops = conn.execute("SELECT * FROM live_propagation_observations WHERE txid = ? ORDER BY delta_ms ASC", (txid,)).fetchall()
    dests = conn.execute("SELECT * FROM live_destinations WHERE txid = ?", (txid,)).fetchall()
    conn.close()

    return {
        "tx": dict(tx_row),
        "propagation": [dict(h) for h in hops],
        "destinations": [dict(d) for d in dests]
    }

def get_cached_ip(ip: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM ip_cache WHERE ip = ?", (ip,)).fetchone()
    conn.close()
    return dict(row) if row else None

def set_cached_ip(ip: str, data: Dict[str, Any], db_path: str = DB_PATH) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO ip_cache (ip, country, country_code, city, org, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ip,
            data.get("country", "Unknown"),
            data.get("country_code", "??"),
            data.get("city", "Unknown"),
            data.get("org", "Unknown"),
            datetime.now(timezone.utc).isoformat()
        ))
    conn.close()

def get_cached_address(address: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM address_cache WHERE address = ?", (address,)).fetchone()
    conn.close()
    return dict(row) if row else None

def set_cached_address(address: str, data: Dict[str, Any], db_path: str = DB_PATH) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO address_cache (
                address, entity_name, entity_type, region, confidence, tx_count, total_btc, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            address,
            data.get("entity_name", "Unknown Entity"),
            data.get("entity_type", "Unknown"),
            data.get("region", "Unknown"),
            data.get("confidence", "Low"),
            data.get("tx_count", 0),
            data.get("total_btc", 0.0),
            datetime.now(timezone.utc).isoformat()
        ))
    conn.close()

def list_recent_transactions(limit: int = 25, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM live_transactions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

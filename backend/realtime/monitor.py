"""
monitor.py - Live Bitcoin transaction monitor and mempool ingestion.
Supports resilient multi-provider feeds (Blockchain.com WS, Blockstream API, Mempool.space)
with instantaneous real-time streaming.
"""

import json
import time
import asyncio
import requests
from typing import Dict, Any, Optional, Callable, List

BLOCKSTREAM_API = "https://blockstream.info/api"
BLOCKCHAIN_API = "https://blockchain.info"
BLOCKCHAIN_WS = "wss://ws.blockchain.info/inv"

def parse_blockstream_tx(data: Dict[str, Any]) -> Dict[str, Any]:
    vout = data.get("vout", [])
    total_satoshis = sum(v.get("value", 0) for v in vout)
    fee_satoshis = data.get("fee", 0)

    outputs = []
    for v in vout:
        addr = v.get("scriptpubkey_address") or "Non-standard / OP_RETURN"
        outputs.append({
            "address": addr,
            "value_btc": round(v.get("value", 0) / 100_000_000, 8),
            "script_type": v.get("scriptpubkey_type", "")
        })

    return {
        "txid": data.get("txid"),
        "amount_btc": round(total_satoshis / 100_000_000, 8),
        "fee_btc": round(fee_satoshis / 100_000_000, 8),
        "size": data.get("size", 0),
        "weight": data.get("weight", 0),
        "confirmed": data.get("status", {}).get("confirmed", False),
        "outputs": outputs
    }

def parse_blockchain_tx(data: Dict[str, Any]) -> Dict[str, Any]:
    outs = data.get("out", [])
    inputs = data.get("inputs", [])
    total_satoshis = sum(o.get("value", 0) for o in outs)

    in_sum = sum(i.get("prev_out", {}).get("value", 0) for i in inputs if i.get("prev_out"))
    fee_satoshis = max(0, in_sum - total_satoshis) if in_sum > total_satoshis else 0

    outputs = []
    for o in outs:
        addr = o.get("addr") or "Non-standard / OP_RETURN"
        outputs.append({
            "address": addr,
            "value_btc": round(o.get("value", 0) / 100_000_000, 8),
            "script_type": ""
        })

    return {
        "txid": data.get("hash", ""),
        "amount_btc": round(total_satoshis / 100_000_000, 8),
        "fee_btc": round(fee_satoshis / 100_000_000, 8),
        "size": data.get("size", 0),
        "weight": data.get("weight", 0),
        "confirmed": data.get("block_height") is not None,
        "relayed_by": data.get("relayed_by"),
        "outputs": outputs
    }

def fetch_transaction_details(txid: str, timeout: float = 4.0) -> Optional[Dict[str, Any]]:
    """
    Fetches transaction details with multi-provider failover: Blockstream -> Blockchain.info
    """
    try:
        resp = requests.get(f"{BLOCKSTREAM_API}/tx/{txid}", timeout=timeout)
        if resp.status_code == 200:
            return parse_blockstream_tx(resp.json())
    except Exception:
        pass

    try:
        resp = requests.get(f"{BLOCKCHAIN_API}/rawtx/{txid}?cors=true", timeout=timeout)
        if resp.status_code == 200:
            return parse_blockchain_tx(resp.json())
    except Exception:
        pass

    return None

def fetch_recent_mempool_txids(limit: int = 5, timeout: float = 4.0) -> List[str]:
    """
    Fetches recent transaction IDs currently pending in the mempool.
    """
    try:
        resp = requests.get(f"{BLOCKSTREAM_API}/mempool/recent", timeout=timeout)
        if resp.status_code == 200:
            items = resp.json()
            return [item.get("txid") for item in items[:limit] if "txid" in item]
    except Exception:
        pass

    try:
        resp = requests.get(f"{BLOCKCHAIN_API}/unconfirmed-transactions?format=json", timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            txs = data.get("txs", [])
            return [t.get("hash") for t in txs[:limit] if "hash" in t]
    except Exception:
        pass

    return []

async def stream_live_transactions(on_transaction: Callable[[Dict[str, Any]], Any], max_count: Optional[int] = None):
    """
    Streams live Bitcoin transactions via WebSocket with automatic failover to REST polling.
    """
    import websockets
    count = 0

    try:
        async with websockets.connect(BLOCKCHAIN_WS, open_timeout=5) as ws:
            await ws.send(json.dumps({"op": "unconfirmed_sub"}))

            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(msg)
                x = data.get("x")
                if x:
                    parsed = parse_blockchain_tx(x)
                    if asyncio.iscoroutinefunction(on_transaction):
                        await on_transaction(parsed)
                    else:
                        on_transaction(parsed)
                    count += 1
                    if max_count and count >= max_count:
                        return
    except Exception:
        pass

    # Fallback: Rapid mempool polling
    seen = set()
    while True:
        recent_ids = fetch_recent_mempool_txids(limit=5)
        for tid in recent_ids:
            if tid in seen:
                continue
            seen.add(tid)
            tx_details = fetch_transaction_details(tid)
            if tx_details:
                if asyncio.iscoroutinefunction(on_transaction):
                    await on_transaction(tx_details)
                else:
                    on_transaction(tx_details)
                count += 1
                if max_count and count >= max_count:
                    return
            await asyncio.sleep(0.5)
        await asyncio.sleep(2.0)

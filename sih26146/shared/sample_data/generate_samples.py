import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import argparse

# Paths - derive dynamically relative to this file
parser = argparse.ArgumentParser(description="Generate sample datasets for SIH26146")
parser.add_argument("--output-dir", type=str, default=None, help="Directory to output sample data files")
args, _ = parser.parse_known_args()

out_dir = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent
out_dir.mkdir(parents=True, exist_ok=True)

base_time = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)

# 1. Generate Blockchain Transactions
# Include:
# - Normal transactions
# - A 4-hop peeling chain: W_PEEL_0 -> W_PEEL_1 (forward) + W_OUT_1 (peeled) -> ...
# - A CoinJoin transaction: 4 equal inputs, 4 equal outputs

txns = []
events = []

# Peeling chain addresses
peel_addrs = [f"1PeelSeedIllicitAddr{i}xyz" for i in range(5)]
peeled_outs = [f"1MerchantSpendAddr{i}abc" for i in range(4)]

# Peeling chain txns
current_val = 10.0
for i in range(4):
    t_time = base_time + timedelta(minutes=i * 10)
    peel_amt = 0.5
    fwd_amt = round(current_val - peel_amt - 0.0001, 4)
    txns.append({
        "txid": f"tx_peel_chain_hop_{i}_" + uuid.uuid4().hex[:8],
        "timestamp": t_time.isoformat(),
        "input_addresses": [peel_addrs[i]],
        "output_addresses": [peel_addrs[i+1], peeled_outs[i]],
        "input_amounts": [current_val],
        "output_amounts": [fwd_amt, peel_amt],
        "fee": 0.0001,
        "script_type": "P2PKH"
    })
    current_val = fwd_amt

# CoinJoin txn
cj_time = base_time + timedelta(minutes=45)
cj_in_addrs = [f"1CoinJoinIn_{i}_" + uuid.uuid4().hex[:6] for i in range(5)]
cj_out_addrs = [f"1CoinJoinOut_{i}_" + uuid.uuid4().hex[:6] for i in range(5)]
txns.append({
    "txid": "tx_coinjoin_mixing_" + uuid.uuid4().hex[:8],
    "timestamp": cj_time.isoformat(),
    "input_addresses": cj_in_addrs,
    "output_addresses": cj_out_addrs,
    "input_amounts": [1.0, 1.0, 1.0, 1.0, 1.0],
    "output_amounts": [0.9999, 0.9999, 0.9999, 0.9999, 0.9999],
    "fee": 0.0005,
    "script_type": "P2WPKH"
})

# Multi-input cluster (common input ownership)
cl_time = base_time + timedelta(minutes=60)
cluster_in_addrs = [f"1EntityCluster_{i}_" + uuid.uuid4().hex[:6] for i in range(3)]
txns.append({
    "txid": "tx_common_input_cluster_" + uuid.uuid4().hex[:8],
    "timestamp": cl_time.isoformat(),
    "input_addresses": cluster_in_addrs,
    "output_addresses": ["1ConsolidatedVaultAddr123"],
    "input_amounts": [2.5, 1.5, 3.0],
    "output_amounts": [6.9998],
    "fee": 0.0002,
    "script_type": "P2SH"
})

# Normal transactions (to fill up to 25 records)
for i in range(18):
    norm_time = base_time + timedelta(minutes=70 + i * 5)
    txns.append({
        "txid": f"tx_normal_{i}_" + uuid.uuid4().hex[:8],
        "timestamp": norm_time.isoformat(),
        "input_addresses": [f"1NormalUserIn_{i}_" + uuid.uuid4().hex[:6]],
        "output_addresses": [f"1NormalUserOut_{i}_" + uuid.uuid4().hex[:6], f"1ChangeOut_{i}_" + uuid.uuid4().hex[:6]],
        "input_amounts": [round(0.5 + i * 0.1, 4)],
        "output_amounts": [round(0.3 + i * 0.05, 4), round(0.1998 + i * 0.05, 4)],
        "fee": 0.0002,
        "script_type": "P2WPKH"
    })

# 2. Generate Network Events matching txns closely in time
# For each transaction, create an event within +/- 15s to test correlation
ips = [
    ("198.51.100.12", "US", "AS15169"),
    ("203.0.113.45", "DE", "AS3320"),
    ("192.0.2.88", "RU", "AS12389"),
    ("185.220.101.5", "NL", "AS60729"),
    ("198.51.100.99", "US", "AS15169")
]

for idx, t in enumerate(txns):
    t_dt = datetime.fromisoformat(t["timestamp"])
    e_dt = t_dt - timedelta(seconds=12) # 12s before txn broadcast
    ip_info = ips[idx % len(ips)]
    events.append({
        "event_id": str(uuid.uuid4()),
        "timestamp": e_dt.isoformat(),
        "src_ip": ip_info[0],
        "dst_ip": "83.136.255.40",
        "src_port": 54320 + idx,
        "dst_port": 8333,
        "protocol": "TCP",
        "packet_size": 512 + idx * 8,
        "src_geo_country": ip_info[1],
        "src_asn": ip_info[2],
        "dst_geo_country": "DE",
        "dst_asn": "AS24940"
    })

# Add a few un-correlated network noise events
for i in range(5):
    noise_dt = base_time + timedelta(hours=5, minutes=i*10)
    events.append({
        "event_id": str(uuid.uuid4()),
        "timestamp": noise_dt.isoformat(),
        "src_ip": "198.51.100.77",
        "dst_ip": "83.136.255.41",
        "src_port": 49152 + i,
        "dst_port": 8333,
        "protocol": "TCP",
        "packet_size": 128,
        "src_geo_country": "US",
        "src_asn": "AS15169",
        "dst_geo_country": "DE",
        "dst_asn": "AS24940"
    })

# 3. Correlation edges (placeholder samples)
corr_edges = []
for i in range(len(txns)):
    corr_edges.append({
        "edge_id": str(uuid.uuid4()),
        "network_event_id": events[i]["event_id"],
        "txid": txns[i]["txid"],
        "confidence": 0.88,
        "correlation_type": "time_window"
    })

# 4. Clusters (placeholder samples)
clusters = [
    {
        "cluster_id": "cluster-entity-001",
        "label": "Consolidation pattern",
        "member_addresses": cluster_in_addrs + ["1ConsolidatedVaultAddr123"],
        "member_count": 4,
        "avg_risk_score": 0.42,
        "description": "4 addresses consolidating funds into a primary vault wallet. Common input ownership confirms single-entity control.",
        "clustering_method": "common_input_ownership+node2vec_embedding"
    },
    {
        "cluster_id": "cluster-mixing-002",
        "label": "Possible mixing service",
        "member_addresses": peel_addrs,
        "member_count": len(peel_addrs),
        "avg_risk_score": 0.89,
        "description": "5 addresses participating in a rapid peeling chain laundering sequence across multiple consecutive hops.",
        "clustering_method": "common_input_ownership+node2vec_embedding"
    }
]

# 5. labels.json (ground truth labels for evaluation and seed illicit wallets)
labels = {
    "seed_illicit_wallets": [
        peel_addrs[0] # Seed illicit wallet: starts the peeling chain!
    ],
    "anomalous_transactions": [
        {"txid": txns[0]["txid"], "pattern_type": "peeling_chain", "reason": "Hop 0 of peeling chain from seed illicit wallet"},
        {"txid": txns[1]["txid"], "pattern_type": "peeling_chain", "reason": "Hop 1 of peeling chain"},
        {"txid": txns[2]["txid"], "pattern_type": "peeling_chain", "reason": "Hop 2 of peeling chain"},
        {"txid": txns[3]["txid"], "pattern_type": "peeling_chain", "reason": "Hop 3 of peeling chain"},
        {"txid": txns[4]["txid"], "pattern_type": "coinjoin_mixing", "reason": "Equal-value multi-party CoinJoin transaction"}
    ]
}

# Write files
with open(out_dir / "network_events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, indent=2)

with open(out_dir / "blockchain_txns.json", "w", encoding="utf-8") as f:
    json.dump(txns, f, indent=2)

with open(out_dir / "correlation_edges.json", "w", encoding="utf-8") as f:
    json.dump(corr_edges, f, indent=2)

with open(out_dir / "clusters.json", "w", encoding="utf-8") as f:
    json.dump(clusters, f, indent=2)

with open(out_dir / "labels.json", "w", encoding="utf-8") as f:
    json.dump(labels, f, indent=2)

# Sample data README
with open(out_dir / "README.md", "w", encoding="utf-8") as f:
    f.write("# Shared Sample Data (Temporary Placeholder)\n\n"
            "This folder contains initial placeholder data matching the official SIH26146 schemas.\n"
            "Used to unblock parallel development across modules before Module 1 completes.\n")

print(f"Successfully generated {len(events)} events, {len(txns)} txns, {len(corr_edges)} edges, {len(clusters)} clusters.")

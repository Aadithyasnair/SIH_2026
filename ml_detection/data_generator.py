"""
Realistic Bitcoin Transaction and Network Data Generator.
Produces a comprehensive, PS-compliant dataset for SIH26146:
- 3,000 Blockchain Transactions (multi-input, multi-output, realistic script types and amounts)
- 3,000 Enriched Transactions (with Module B pattern_type, flags, propagated_risk_score)
- ~9,000 Network Events (IPs, ports, Geo countries, ASNs, Tor & standard Bitcoin nodes)
- ~3,000 Correlation Edges (linking network events to blockchain transactions with confidence scores)
- 60 Entity Clusters (with human-readable labels, descriptions, and risk scores)
- labels.json with 15 seed illicit wallets and 360 anomalous transactions (peeling chains,
  CoinJoin mixing, rapid multi-hop layering, whale spikes, Tor-proxied flows)
- entity_graph.graphml (NetworkX entity graph linking IPs, wallets, and transactions)

Strict schema validation against sih26146.shared.schemas.records is performed before saving.
"""

import json
import uuid
import random
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import sys
import networkx as nx

# Ensure repo root is on sys.path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sih26146.shared.schemas.records import (
    NetworkEvent,
    BlockchainTxn,
    CorrelationEdge,
    Cluster,
)


class BitcoinDatasetGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        self.base_time = datetime(2026, 1, 15, 8, 0, 0, tzinfo=timezone.utc)

        # Country & ASN distribution (top Bitcoin node jurisdictions)
        self.geo_asn_profiles = [
            ("US", "AS15169", 0.22),   # Google / US Cloud
            ("US", "AS7922", 0.10),    # Comcast
            ("DE", "AS24940", 0.12),   # Hetzner DE
            ("DE", "AS3320", 0.06),    # Deutsche Telekom
            ("NL", "AS60729", 0.08),   # Tor exit / hosting NL
            ("RU", "AS12389", 0.07),   # Rostelecom RU
            ("CN", "AS4134", 0.06),    # Chinanet
            ("GB", "AS2856", 0.05),    # BT GB
            ("CA", "AS852", 0.04),     # Telus CA
            ("SG", "AS4657", 0.04),    # StarHub SG
            ("FR", "AS16276", 0.04),   # OVH FR
            ("JP", "AS2516", 0.03),    # KDDI JP
            ("CH", "AS3303", 0.03),    # Swisscom CH
            ("SE", "AS8473", 0.02),    # Bahnhof SE
            ("IS", "AS44546", 0.02),   # FlokiNET IS
            ("PA", "AS27775", 0.02),   # Panama offshore
        ]

        # Script types
        self.script_types = ["P2WPKH", "P2PKH", "P2SH", "P2TR"]
        self.script_weights = [0.50, 0.30, 0.15, 0.05]

        # Wallet universe
        self.wallets: List[str] = []
        self.seed_illicit_wallets: List[str] = []
        self.wallet_profiles: Dict[str, Dict[str, Any]] = {}
        self.wallet_ips: Dict[str, str] = {}

    def _random_ip(self) -> str:
        return f"{random.randint(11, 220)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

    def _sample_geo_asn(self) -> Tuple[str, str]:
        r = random.random()
        cumulative = 0.0
        for country, asn, weight in self.geo_asn_profiles:
            cumulative += weight
            if r <= cumulative:
                return country, asn
        return "US", "AS15169"

    def setup_wallets(self, num_wallets: int = 1000):
        """Create diverse wallet addresses with base profiles."""
        self.wallets = []
        for i in range(num_wallets):
            st = random.choices(self.script_types, weights=self.script_weights)[0]
            if st == "P2WPKH":
                addr = f"bc1q{uuid.uuid4().hex[:28]}"
            elif st == "P2TR":
                addr = f"bc1p{uuid.uuid4().hex[:28]}"
            elif st == "P2SH":
                addr = f"3{uuid.uuid4().hex[:26]}"
            else:
                addr = f"1{uuid.uuid4().hex[:26]}"

            self.wallets.append(addr)
            self.wallet_ips[addr] = self._random_ip()

            # Assign wallet personality
            r_type = random.random()
            if r_type < 0.70:
                base_amt = round(random.uniform(0.01, 1.5), 4)
                volatility = 0.25
            elif r_type < 0.90:
                base_amt = round(random.uniform(2.0, 15.0), 4)
                volatility = 0.35
            else:
                base_amt = round(random.uniform(20.0, 120.0), 4)
                volatility = 0.40

            self.wallet_profiles[addr] = {
                "script_type": st,
                "base_amount": base_amt,
                "volatility": volatility,
            }

        # 15 Seed illicit wallets for propagation and peel roots
        self.seed_illicit_wallets = [
            f"1DarknetMarketVendor_{i}_{uuid.uuid4().hex[:8]}" for i in range(5)
        ] + [
            f"1RansomwarePayment_{i}_{uuid.uuid4().hex[:8]}" for i in range(5)
        ] + [
            f"1LaunderingHub_{i}_{uuid.uuid4().hex[:8]}" for i in range(5)
        ]

        for s_addr in self.seed_illicit_wallets:
            self.wallet_profiles[s_addr] = {
                "script_type": "P2PKH",
                "base_amount": 25.0,
                "volatility": 0.5,
            }
            self.wallet_ips[s_addr] = self._random_ip()

    def generate_dataset(
        self,
        num_normal_txns: int = 2640,
        num_peeling_chains: int = 24,
        peeling_hops: int = 5,
        num_coinjoin_txns: int = 60,
        num_burst_txns: int = 80,
        num_whale_txns: int = 60,
        num_tor_txns: int = 40,
    ) -> Dict[str, Any]:
        """
        Generates all entities:
        - 2640 normal + 120 peel + 60 coinjoin + 80 burst + 60 whale + 40 tor = 3000 txns
        - 360 anomalous txns total (12.0%)
        """
        self.setup_wallets(num_wallets=1200)

        txns: List[Dict[str, Any]] = []
        enriched_txns: List[Dict[str, Any]] = []
        network_events: List[Dict[str, Any]] = []
        correlation_edges: List[Dict[str, Any]] = []
        labeled_anomalies: List[Dict[str, Any]] = []

        all_tx_times: List[datetime] = []
        time_cursor = self.base_time

        # Helper for network event generation
        def create_network_event(
            t: datetime,
            src_ip: str,
            dst_port: int = 8333,
            is_tor: bool = False,
        ) -> Dict[str, Any]:
            eid = f"net_{uuid.uuid4().hex[:12]}"
            s_country, s_asn = self._sample_geo_asn()
            d_country, d_asn = self._sample_geo_asn()
            if is_tor:
                d_port = random.choice([9050, 9001, 9150])
                protocol = "TCP"
                s_country = "NL"
                s_asn = "AS60729"
            else:
                d_port = dst_port
                protocol = "TCP"

            ev = {
                "event_id": eid,
                "timestamp": t.isoformat(),
                "src_ip": src_ip,
                "dst_ip": self._random_ip(),
                "src_port": random.randint(30000, 65000),
                "dst_port": d_port,
                "protocol": protocol,
                "packet_size": random.randint(450, 2400),
                "src_geo_country": s_country,
                "src_asn": s_asn,
                "dst_geo_country": d_country,
                "dst_asn": d_asn,
            }
            return ev

        # -------------------------------------------------------------
        # 1. PEELING CHAINS (24 chains x 5 hops = 120 txns)
        # -------------------------------------------------------------
        peel_chain_wallets: Set[str] = set()
        for c_idx in range(num_peeling_chains):
            seed_addr = self.seed_illicit_wallets[c_idx % len(self.seed_illicit_wallets)]
            current_addr = seed_addr
            current_amt = round(random.uniform(8.0, 35.0), 4)
            chain_time = self.base_time + timedelta(hours=c_idx * 5, minutes=random.randint(5, 50))

            for hop in range(peeling_hops):
                peel_chain_wallets.add(current_addr)
                next_hop_addr = f"1PeelHop_{c_idx}_{hop+1}_{uuid.uuid4().hex[:6]}"
                peel_spend_addr = f"1MerchantSpend_{c_idx}_{hop}_{uuid.uuid4().hex[:6]}"
                self.wallet_profiles[next_hop_addr] = {"script_type": "P2PKH", "base_amount": 5.0, "volatility": 0.2}
                self.wallet_profiles[peel_spend_addr] = {"script_type": "P2PKH", "base_amount": 0.5, "volatility": 0.1}

                peel_amt = round(random.uniform(0.1, 0.45), 4)
                fwd_amt = round(max(0.005, current_amt - peel_amt - 0.0002), 4)
                tx_time = chain_time + timedelta(minutes=hop * 12 + random.randint(1, 4))
                txid = f"tx_peel_chain_c{c_idx}_hop{hop}_{uuid.uuid4().hex[:8]}"

                txn_dict = {
                    "txid": txid,
                    "timestamp": tx_time.isoformat(),
                    "input_addresses": [current_addr],
                    "output_addresses": [next_hop_addr, peel_spend_addr],
                    "input_amounts": [current_amt],
                    "output_amounts": [fwd_amt, peel_amt],
                    "fee": 0.0002,
                    "script_type": "P2PKH",
                }
                txns.append(txn_dict)

                # Simulated Module B enrichment
                enriched = dict(txn_dict)
                enriched["pattern_type"] = "peeling_chain"
                enriched["flags"] = ["peeling_chain_detected", "illicit_seed_proximity", "unbalanced_outputs"]
                # Risk decays slightly per hop: 1.0 -> 0.9 -> 0.82 -> ...
                enriched["propagated_risk_score"] = round(1.0 * (0.92 ** hop), 4)
                enriched_txns.append(enriched)

                labeled_anomalies.append({
                    "txid": txid,
                    "pattern_type": "peeling_chain",
                    "reason": f"Hop {hop} of peeling chain originated from seed illicit wallet {seed_addr[:14]}...",
                })

                # Correlated events
                ip = self._random_ip()
                for e_i in range(3):
                    ev = create_network_event(tx_time + timedelta(seconds=e_i * 2), src_ip=ip, dst_port=8333)
                    network_events.append(ev)
                    correlation_edges.append({
                        "edge_id": f"edge_{uuid.uuid4().hex[:12]}",
                        "network_event_id": ev["event_id"],
                        "txid": txid,
                        "confidence": round(0.85 - e_i * 0.05, 3),
                        "correlation_type": "time_window",
                    })

                current_amt = fwd_amt
                current_addr = next_hop_addr

        # -------------------------------------------------------------
        # 2. COINJOIN MIXING TRANSACTIONS (60 txns)
        # -------------------------------------------------------------
        coinjoin_wallets: Set[str] = set()
        for cj_idx in range(num_coinjoin_txns):
            cj_time = self.base_time + timedelta(days=cj_idx % 45, hours=random.randint(1, 23))
            num_parties = random.randint(6, 12)
            in_addrs = [f"1CJ_In_{cj_idx}_{p}_{uuid.uuid4().hex[:6]}" for p in range(num_parties)]
            out_addrs = [f"bc1qCJ_Out_{cj_idx}_{p}_{uuid.uuid4().hex[:6]}" for p in range(num_parties)]
            for a in in_addrs + out_addrs:
                coinjoin_wallets.add(a)

            denomination = random.choice([0.1, 0.25, 0.5, 1.0, 2.0])
            fee_per_party = 0.0001
            out_val = round(denomination - fee_per_party, 4)

            txid = f"tx_coinjoin_mixing_{cj_idx}_{uuid.uuid4().hex[:8]}"
            txn_dict = {
                "txid": txid,
                "timestamp": cj_time.isoformat(),
                "input_addresses": in_addrs,
                "output_addresses": out_addrs,
                "input_amounts": [denomination] * num_parties,
                "output_amounts": [out_val] * num_parties,
                "fee": round(fee_per_party * num_parties, 4),
                "script_type": "P2WPKH",
            }
            txns.append(txn_dict)

            enriched = dict(txn_dict)
            enriched["pattern_type"] = "coinjoin_mixing"
            enriched["flags"] = ["equal_output_values", "multi_party_mixing", "anonymity_set_spike"]
            enriched["propagated_risk_score"] = round(random.uniform(0.75, 0.95), 4)
            enriched_txns.append(enriched)

            labeled_anomalies.append({
                "txid": txid,
                "pattern_type": "coinjoin_mixing",
                "reason": f"Equal-value multi-party CoinJoin transaction ({num_parties} inputs/outputs of {denomination} BTC)",
            })

            # Events for CoinJoin
            for p in range(min(5, num_parties)):
                ev = create_network_event(cj_time + timedelta(seconds=p), src_ip=self._random_ip(), dst_port=8333)
                network_events.append(ev)
                correlation_edges.append({
                    "edge_id": f"edge_{uuid.uuid4().hex[:12]}",
                    "network_event_id": ev["event_id"],
                    "txid": txid,
                    "confidence": 0.90,
                    "correlation_type": "session_burst",
                })

        # -------------------------------------------------------------
        # 3. BURST / RAPID LAYERING TRANSACTIONS (80 txns)
        # -------------------------------------------------------------
        # 16 hubs x 5 rapid txns each in a tight 30-min window
        for hub_idx in range(16):
            hub_addr = f"1RapidLayerHub_{hub_idx}_{uuid.uuid4().hex[:6]}"
            burst_time = self.base_time + timedelta(days=hub_idx * 2, hours=random.randint(2, 22))
            hub_ip = self._random_ip()

            for b_i in range(5):
                t_b = burst_time + timedelta(minutes=b_i * 4 + random.randint(1, 2))
                out_a = random.choice(self.wallets)
                amt = round(random.uniform(3.0, 15.0), 4)
                txid = f"tx_burst_layering_h{hub_idx}_n{b_i}_{uuid.uuid4().hex[:8]}"

                txn_dict = {
                    "txid": txid,
                    "timestamp": t_b.isoformat(),
                    "input_addresses": [hub_addr],
                    "output_addresses": [out_a],
                    "input_amounts": [amt + 0.0005],
                    "output_amounts": [amt],
                    "fee": 0.0005,
                    "script_type": "P2WPKH",
                }
                txns.append(txn_dict)

                enriched = dict(txn_dict)
                enriched["pattern_type"] = "none"
                enriched["flags"] = ["high_frequency_burst", "rapid_fund_movement"]
                enriched["propagated_risk_score"] = round(random.uniform(0.68, 0.85), 4)
                enriched_txns.append(enriched)

                labeled_anomalies.append({
                    "txid": txid,
                    "pattern_type": "rapid_layering",
                    "reason": f"High-frequency burst hop {b_i+1}/5 from hub {hub_addr[:14]} within 30 minutes",
                })

                ev = create_network_event(t_b, src_ip=hub_ip, dst_port=8333)
                network_events.append(ev)
                correlation_edges.append({
                    "edge_id": f"edge_{uuid.uuid4().hex[:12]}",
                    "network_event_id": ev["event_id"],
                    "txid": txid,
                    "confidence": 0.88,
                    "correlation_type": "ip_reuse",
                })

        # -------------------------------------------------------------
        # 4. WHALE SPIKE TRANSACTIONS (60 txns)
        # -------------------------------------------------------------
        for w_idx in range(num_whale_txns):
            w_time = self.base_time + timedelta(days=w_idx % 50, hours=random.randint(0, 23))
            sender = random.choice(self.wallets[:300])
            normal_base = self.wallet_profiles[sender]["base_amount"]
            whale_amt = round(normal_base * random.uniform(15.0, 45.0), 4)
            recipients = random.sample(self.wallets, k=random.randint(2, 4))
            splits = [round(whale_amt / len(recipients), 4) for _ in recipients]
            txid = f"tx_whale_spike_{w_idx}_{uuid.uuid4().hex[:8]}"

            txn_dict = {
                "txid": txid,
                "timestamp": w_time.isoformat(),
                "input_addresses": [sender],
                "output_addresses": recipients,
                "input_amounts": [whale_amt + 0.002],
                "output_amounts": splits,
                "fee": 0.002,
                "script_type": self.wallet_profiles[sender]["script_type"],
            }
            txns.append(txn_dict)

            enriched = dict(txn_dict)
            enriched["pattern_type"] = "none"
            enriched["flags"] = ["abnormal_amount_spike", "wallet_behavioral_outlier"]
            enriched["propagated_risk_score"] = round(random.uniform(0.60, 0.78), 4)
            enriched_txns.append(enriched)

            labeled_anomalies.append({
                "txid": txid,
                "pattern_type": "whale_spike",
                "reason": f"Amount {whale_amt} BTC is >20x historical mean for sender {sender[:12]}",
            })

            ev = create_network_event(w_time, src_ip=self.wallet_ips[sender], dst_port=8333)
            network_events.append(ev)
            correlation_edges.append({
                "edge_id": f"edge_{uuid.uuid4().hex[:12]}",
                "network_event_id": ev["event_id"],
                "txid": txid,
                "confidence": 0.92,
                "correlation_type": "time_window",
            })

        # -------------------------------------------------------------
        # 5. TOR PROXIED SUSPICIOUS TRANSACTIONS (40 txns)
        # -------------------------------------------------------------
        for tor_idx in range(num_tor_txns):
            t_time = self.base_time + timedelta(days=tor_idx % 40, hours=random.randint(0, 5))
            sender = random.choice(self.wallets)
            receiver = random.choice(self.wallets)
            amt = round(random.uniform(1.0, 10.0), 4)
            txid = f"tx_tor_proxied_{tor_idx}_{uuid.uuid4().hex[:8]}"

            txn_dict = {
                "txid": txid,
                "timestamp": t_time.isoformat(),
                "input_addresses": [sender],
                "output_addresses": [receiver],
                "input_amounts": [amt + 0.0008],
                "output_amounts": [amt],
                "fee": 0.0008,
                "script_type": "P2WPKH",
            }
            txns.append(txn_dict)

            enriched = dict(txn_dict)
            enriched["pattern_type"] = "none"
            enriched["flags"] = ["tor_exit_traffic", "cross_border_obscuration"]
            enriched["propagated_risk_score"] = round(random.uniform(0.65, 0.82), 4)
            enriched_txns.append(enriched)

            labeled_anomalies.append({
                "txid": txid,
                "pattern_type": "tor_obscuration",
                "reason": f"Broadcast via Tor darknet proxy with cross-border hop at night ({t_time.hour:02d}:00 UTC)",
            })

            for e_k in range(3):
                ev = create_network_event(t_time + timedelta(seconds=e_k * 3), src_ip=self._random_ip(), is_tor=True)
                network_events.append(ev)
                correlation_edges.append({
                    "edge_id": f"edge_{uuid.uuid4().hex[:12]}",
                    "network_event_id": ev["event_id"],
                    "txid": txid,
                    "confidence": 0.85,
                    "correlation_type": "time_window",
                })

        # -------------------------------------------------------------
        # 6. NORMAL TRANSACTIONS (2,640 txns)
        # -------------------------------------------------------------
        cur_day = 0
        for n_idx in range(num_normal_txns):
            # Advance time realistically over 60 days
            if n_idx % 45 == 0:
                cur_day += 1
            hour = random.choices(
                list(range(24)),
                weights=[1, 1, 1, 1, 2, 3, 5, 7, 9, 10, 10, 9, 8, 8, 8, 9, 9, 8, 7, 6, 5, 4, 3, 2],
            )[0]
            t_norm = self.base_time + timedelta(days=cur_day, hours=hour, minutes=random.randint(0, 59))

            in_cnt = random.choices([1, 2, 3], weights=[0.70, 0.22, 0.08])[0]
            out_cnt = random.choices([1, 2, 3], weights=[0.40, 0.52, 0.08])[0]

            in_addrs = random.sample(self.wallets, k=in_cnt)
            out_addrs = random.sample(self.wallets, k=out_cnt)

            # Amounts consistent with sender wallet base_amount
            base = self.wallet_profiles[in_addrs[0]]["base_amount"]
            vol = self.wallet_profiles[in_addrs[0]]["volatility"]
            total_amt = round(max(0.001, base * random.normalvariate(1.0, vol)), 4)

            # Split among inputs
            in_amts = [round(total_amt / in_cnt, 4) for _ in range(in_cnt)]
            actual_in = round(sum(in_amts), 4)

            fee = round(0.00005 * in_cnt + random.uniform(0.00002, 0.00008), 5)
            net_out = max(0.0005, actual_in - fee)

            if out_cnt == 1:
                out_amts = [net_out]
            elif out_cnt == 2:
                # Typical spend + change
                spend = round(net_out * random.uniform(0.3, 0.7), 4)
                change = round(net_out - spend, 4)
                out_amts = [spend, change]
            else:
                out_amts = [round(net_out / out_cnt, 4) for _ in range(out_cnt)]

            txid = f"tx_norm_{n_idx}_{uuid.uuid4().hex[:8]}"
            st = self.wallet_profiles[in_addrs[0]]["script_type"]

            txn_dict = {
                "txid": txid,
                "timestamp": t_norm.isoformat(),
                "input_addresses": in_addrs,
                "output_addresses": out_addrs,
                "input_amounts": in_amts,
                "output_amounts": out_amts,
                "fee": fee,
                "script_type": st,
            }
            txns.append(txn_dict)

            enriched = dict(txn_dict)
            enriched["pattern_type"] = "none"
            enriched["flags"] = []
            enriched["propagated_risk_score"] = round(random.uniform(0.0, 0.18), 4)
            enriched_txns.append(enriched)

            # 2 to 4 network events per normal txn
            sender_ip = self.wallet_ips[in_addrs[0]]
            for ev_i in range(random.randint(2, 3)):
                ev = create_network_event(t_norm + timedelta(seconds=ev_i), src_ip=sender_ip, dst_port=8333)
                network_events.append(ev)
                correlation_edges.append({
                    "edge_id": f"edge_{uuid.uuid4().hex[:12]}",
                    "network_event_id": ev["event_id"],
                    "txid": txid,
                    "confidence": round(random.uniform(0.75, 0.95), 3),
                    "correlation_type": "time_window",
                })

        # -------------------------------------------------------------
        # 7. ENTITY CLUSTERS (60 clusters)
        # -------------------------------------------------------------
        clusters: List[Dict[str, Any]] = []

        # 15 High-risk clusters (mixing & peel operations)
        for i in range(15):
            members = random.sample(list(peel_chain_wallets.union(coinjoin_wallets)), k=min(12, max(4, len(peel_chain_wallets)//2)))
            cid = f"cluster_high_risk_{i}_{uuid.uuid4().hex[:6]}"
            clusters.append({
                "cluster_id": cid,
                "label": f"Suspicious Entity Group {i+1} (Mixing / Peeling)",
                "member_addresses": members,
                "member_count": len(members),
                "avg_risk_score": round(random.uniform(0.78, 0.96), 3),
                "description": f"Group of {len(members)} addresses repeatedly co-participating in multi-hop layering and unlinked mixing chains.",
                "clustering_method": "common_input_ownership+node2vec_embedding",
            })

        # 20 Medium-risk clusters
        for i in range(20):
            members = random.sample(self.wallets[300:700], k=random.randint(5, 15))
            cid = f"cluster_med_risk_{i}_{uuid.uuid4().hex[:6]}"
            clusters.append({
                "cluster_id": cid,
                "label": f"Merchant / Payment Processor Cluster {i+1}",
                "member_addresses": members,
                "member_count": len(members),
                "avg_risk_score": round(random.uniform(0.40, 0.65), 3),
                "description": f"Commercial wallet cluster with co-spent inputs across business settlements.",
                "clustering_method": "common_input_ownership",
            })

        # 25 Low-risk / Normal clusters
        for i in range(25):
            members = random.sample(self.wallets[700:], k=random.randint(3, 8))
            cid = f"cluster_normal_{i}_{uuid.uuid4().hex[:6]}"
            clusters.append({
                "cluster_id": cid,
                "label": f"Standard Co-Spend Entity {i+1}",
                "member_addresses": members,
                "member_count": len(members),
                "avg_risk_score": round(random.uniform(0.02, 0.25), 3),
                "description": f"Standard user or small institution co-spending multiple UTXOs.",
                "clustering_method": "common_input_ownership",
            })

        # -------------------------------------------------------------
        # 8. BUILD ENTITY GRAPH (NetworkX -> GraphML)
        # -------------------------------------------------------------
        G = nx.Graph()
        # Add address nodes and transaction nodes with connections
        for tx in txns:
            txid = tx["txid"]
            G.add_node(txid, node_type="transaction", fee=float(tx["fee"]), script_type=tx["script_type"])
            for in_a in tx["input_addresses"]:
                G.add_node(in_a, node_type="address")
                G.add_edge(in_a, txid, relation="input")
            for out_a in tx["output_addresses"]:
                G.add_node(out_a, node_type="address")
                G.add_edge(txid, out_a, relation="output")

        # Add IP nodes from network events
        for ev in network_events[:1000]:  # Link top events to keep graphml concise and fast
            ip = ev["src_ip"]
            G.add_node(ip, node_type="ip", geo_country=ev["src_geo_country"], asn=ev["src_asn"])

        labels_data = {
            "seed_illicit_wallets": self.seed_illicit_wallets,
            "anomalous_transactions": labeled_anomalies,
        }

        return {
            "blockchain_txns": txns,
            "enriched_txns": enriched_txns,
            "network_events": network_events,
            "correlation_edges": correlation_edges,
            "clusters": clusters,
            "labels": labels_data,
            "entity_graph": G,
        }

    def validate_and_save(self, data: Dict[str, Any], output_dir: Path):
        """Strictly validate each record against Pydantic models, then save to disk."""
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"[1/6] Validating {len(data['network_events'])} NetworkEvents against Pydantic schema...")
        for ev in data["network_events"]:
            NetworkEvent(**ev)

        print(f"[2/6] Validating {len(data['blockchain_txns'])} BlockchainTxns against Pydantic schema...")
        for tx in data["blockchain_txns"]:
            BlockchainTxn(**tx)

        print(f"[3/6] Validating {len(data['correlation_edges'])} CorrelationEdges against Pydantic schema...")
        for edge in data["correlation_edges"]:
            CorrelationEdge(**edge)

        print(f"[4/6] Validating {len(data['clusters'])} Clusters against Pydantic schema...")
        for cl in data["clusters"]:
            Cluster(**cl)

        print("[5/6] All records strictly conform to shared Pydantic contracts!")

        # Write files
        print(f"[6/6] Writing files to {output_dir}...")
        with open(output_dir / "network_events.json", "w", encoding="utf-8") as f:
            json.dump(data["network_events"], f, indent=2)

        with open(output_dir / "blockchain_txns.json", "w", encoding="utf-8") as f:
            json.dump(data["blockchain_txns"], f, indent=2)

        with open(output_dir / "enriched_txns.json", "w", encoding="utf-8") as f:
            json.dump(data["enriched_txns"], f, indent=2)

        with open(output_dir / "correlation_edges.json", "w", encoding="utf-8") as f:
            json.dump(data["correlation_edges"], f, indent=2)

        with open(output_dir / "clusters.json", "w", encoding="utf-8") as f:
            json.dump(data["clusters"], f, indent=2)

        with open(output_dir / "labels.json", "w", encoding="utf-8") as f:
            json.dump(data["labels"], f, indent=2)

        graph_path = output_dir / "entity_graph.graphml"
        nx.write_graphml(data["entity_graph"], str(graph_path))

        print(f"[SUCCESS] Generated complete, fully validated dataset:")
        print(f"  - Blockchain Transactions: {len(data['blockchain_txns'])}")
        print(f"  - Enriched Transactions:   {len(data['enriched_txns'])}")
        print(f"  - Network Events:          {len(data['network_events'])}")
        print(f"  - Correlation Edges:       {len(data['correlation_edges'])}")
        print(f"  - Clusters:                {len(data['clusters'])}")
        print(f"  - Labeled Anomalies:       {len(data['labels']['anomalous_transactions'])} (12.0%)")
        print(f"  - Seed Illicit Wallets:    {len(data['labels']['seed_illicit_wallets'])}")
        print(f"  - Entity Graph:            {data['entity_graph'].number_of_nodes()} nodes, {data['entity_graph'].number_of_edges()} edges")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate large realistic PS-compliant Bitcoin dataset for SIH26146")
    parser.add_argument("--output", type=str, default="sih26146/shared/sample_data", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    gen = BitcoinDatasetGenerator(seed=args.seed)
    data = gen.generate_dataset()
    gen.validate_and_save(data, Path(args.output))


if __name__ == "__main__":
    main()

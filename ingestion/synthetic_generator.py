"""
Synthetic Data Generator Module for SIH26146 Data Ingestion
Generates synthetic Bitcoin network events and blockchain transactions with scenario-injected anomalies.
Outputs validated datasets to /shared/sample_data/ and ground-truth labels to labels.json.
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ingestion.data_validator import DataValidator
from ingestion.geo_enrichment import get_geo_enricher
from shared.schemas.records import NetworkEvent, BlockchainTxn

SCRIPT_TYPES = ["P2PKH", "P2SH", "P2WPKH", "P2TR"]


def generate_wallet_address(prefix: str = "1") -> str:
    """Generates a realistic fake Bitcoin address."""
    chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return prefix + "".join(random.choices(chars, k=33))


def generate_ip() -> str:
    """Generates a random public IPv4 address."""
    return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


class SyntheticDataGenerator:
    def __init__(
        self,
        network_count: int = 5000,
        txn_count: int = 2000,
        anomaly_ratio: float = 0.07,
        inject_anomalies: bool = True,
        seed: int = 42,
    ):
        self.network_count = network_count
        self.txn_count = txn_count
        self.anomaly_ratio = anomaly_ratio
        self.inject_anomalies = inject_anomalies
        random.seed(seed)

        self.start_time = datetime(2026, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        self.validator = DataValidator()

        # Target anomaly transaction count (minimum 5% of txn_count)
        self.num_anomaly_txns = int(self.txn_count * self.anomaly_ratio) if inject_anomalies else 0

        self.network_events: List[Dict[str, Any]] = []
        self.blockchain_txns: List[Dict[str, Any]] = []
        self.labels: Dict[str, Any] = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_network_events": network_count,
                "total_blockchain_txns": txn_count,
                "anomaly_ratio": self.anomaly_ratio,
                "inject_anomalies": inject_anomalies,
            },
            "anomalous_transactions": [],
            "seed_illicit_wallets": [],
            "anomalous_txids": {},
            "anomalous_events": {},
            "anomalous_addresses": {},
            "scenarios": [],
        }

    def generate(self) -> Tuple[List[NetworkEvent], List[BlockchainTxn], Dict[str, Any]]:
        """Executes full synthetic dataset generation and returns validated objects."""
        print(f"Generating {self.txn_count} blockchain txns and {self.network_count} network events...")

        # 1. Inject specific anomaly scenarios first
        if self.inject_anomalies and self.num_anomaly_txns > 0:
            self._inject_anomaly_scenarios()

        # 2. Fill remainder with normal background traffic
        self._generate_background_transactions()
        self._generate_background_network_events()

        # Sort chronologically by timestamp
        self.blockchain_txns.sort(key=lambda x: x["timestamp"])
        self.network_events.sort(key=lambda x: x["timestamp"])

        # 3. Validate output records with Pydantic
        valid_events, event_quarantined = self.validator.validate_batch(self.network_events, NetworkEvent)
        valid_txns, txn_quarantined = self.validator.validate_batch(self.blockchain_txns, BlockchainTxn)

        print(f"Generated {len(valid_events)} valid NetworkEvents (Quarantined: {len(event_quarantined)})")
        print(f"Generated {len(valid_txns)} valid BlockchainTxns (Quarantined: {len(txn_quarantined)})")
        print(f"Injected {len(self.labels['scenarios'])} anomaly scenarios covering {len(self.labels['anomalous_txids'])} txns.")

        return valid_events, valid_txns, self.labels

    def _inject_anomaly_scenarios(self):
        """Injects known suspicious patterns matching official PS focus areas."""
        current_time = self.start_time

        # Scenario 1: Rapid IP Reuse / Burst (1 IP -> 6+ wallets within 5 seconds)
        for i in range(max(2, self.num_anomaly_txns // 20)):
            ip_addr = f"185.220.101.{10 + i}" # Tor exit node style
            geo_info = ("RO", "AS9009", "M247 Europe SRL")
            scenario_id = f"scen_ip_burst_{i}"
            scenario_txids = []
            scenario_events = []
            scenario_wallets = []

            burst_time = current_time + timedelta(minutes=15 * i)

            for j in range(6):
                w_from = generate_wallet_address("1RapidSrc")
                w_to = generate_wallet_address("1RapidDst")
                txid = f"tx_rapid_ip_burst_{i}_{j}_{uuid.uuid4().hex[:6]}"
                event_id = f"net_rapid_ip_burst_{i}_{j}_{uuid.uuid4().hex[:6]}"
                event_time = (burst_time + timedelta(seconds=j)).isoformat()

                net_rec = {
                    "event_id": event_id,
                    "timestamp": event_time,
                    "src_ip": ip_addr,
                    "dst_ip": f"199.14.213.{20 + j}",
                    "src_port": 49000 + j,
                    "dst_port": 8333,
                    "protocol": "TCP",
                    "packet_size": random.randint(500, 2500),
                    "src_geo_country": geo_info[0],
                    "src_asn": geo_info[1],
                    "dst_geo_country": "US",
                    "dst_asn": "AS15169",
                }

                tx_rec = {
                    "txid": txid,
                    "timestamp": event_time,
                    "input_addresses": [w_from],
                    "output_addresses": [w_to],
                    "input_amounts": [round(random.uniform(0.5, 3.0), 4)],
                    "output_amounts": [round(random.uniform(0.49, 2.99), 4)],
                    "fee": 0.0001,
                    "script_type": "P2PKH",
                }

                self.network_events.append(net_rec)
                self.blockchain_txns.append(tx_rec)

                scenario_txids.append(txid)
                scenario_events.append(event_id)
                scenario_wallets.extend([w_from, w_to])

                self.labels["anomalous_txids"][txid] = "rapid_ip_burst"
                self.labels["anomalous_events"][event_id] = "rapid_ip_burst"
                self.labels["anomalous_transactions"].append({
                    "txid": txid,
                    "pattern_type": "rapid_ip_burst",
                    "scenario_id": scenario_id,
                })

            for w in scenario_wallets:
                self.labels["anomalous_addresses"][w] = "rapid_ip_burst"

            self.labels["scenarios"].append({
                "scenario_id": scenario_id,
                "pattern_type": "rapid_ip_burst",
                "description": f"Single IP {ip_addr} initiated 6 distinct wallet transactions within 5 seconds",
                "txids": scenario_txids,
                "event_ids": scenario_events,
                "involved_addresses": list(set(scenario_wallets)),
            })

        # Scenario 2: Smurfing / Consolidation (wallet receiving 10 small deposits then single large payout)
        for i in range(max(2, self.num_anomaly_txns // 15)):
            collector_wallet = generate_wallet_address("1SmurfCollector")
            final_dest = generate_wallet_address("1DarkMarketCashout")
            scenario_id = f"scen_smurf_{i}"
            scenario_txids = []
            scenario_events = []

            collector_time = current_time + timedelta(hours=1 + i)
            total_collected = 0.0

            # 10 small fan-in incoming deposits
            for j in range(10):
                small_amt = round(random.uniform(0.05, 0.15), 4)
                total_collected += small_amt
                txid = f"tx_smurf_in_{i}_{j}_{uuid.uuid4().hex[:6]}"
                event_id = f"net_smurf_in_{i}_{j}_{uuid.uuid4().hex[:6]}"
                t_str = (collector_time + timedelta(minutes=j * 3)).isoformat()
                sender = generate_wallet_address(f"1SmurfSrc_{j}")

                net_rec = {
                    "event_id": event_id,
                    "timestamp": t_str,
                    "src_ip": generate_ip(),
                    "dst_ip": generate_ip(),
                    "src_port": random.randint(30000, 60000),
                    "dst_port": 8333,
                    "protocol": "TCP",
                    "packet_size": 1200,
                    "src_geo_country": "DE",
                    "src_asn": "AS24940",
                    "dst_geo_country": "US",
                    "dst_asn": "AS7018",
                }

                tx_rec = {
                    "txid": txid,
                    "timestamp": t_str,
                    "input_addresses": [sender],
                    "output_addresses": [collector_wallet],
                    "input_amounts": [small_amt + 0.0001],
                    "output_amounts": [small_amt],
                    "fee": 0.0001,
                    "script_type": "P2PKH",
                }

                self.network_events.append(net_rec)
                self.blockchain_txns.append(tx_rec)
                scenario_txids.append(txid)
                scenario_events.append(event_id)

                self.labels["anomalous_txids"][txid] = "smurfing_consolidation"
                self.labels["anomalous_events"][event_id] = "smurfing_consolidation"
                self.labels["anomalous_transactions"].append({
                    "txid": txid,
                    "pattern_type": "smurfing_consolidation",
                    "scenario_id": scenario_id,
                })

            # Rapid single large outgoing consolidation transfer
            out_txid = f"tx_smurf_out_{i}_{uuid.uuid4().hex[:6]}"
            out_event_id = f"net_smurf_out_{i}_{uuid.uuid4().hex[:6]}"
            out_time = (collector_time + timedelta(minutes=32)).isoformat()
            out_amt = round(total_collected - 0.0005, 4)

            self.blockchain_txns.append({
                "txid": out_txid,
                "timestamp": out_time,
                "input_addresses": [collector_wallet],
                "output_addresses": [final_dest],
                "input_amounts": [round(total_collected, 4)],
                "output_amounts": [out_amt],
                "fee": 0.0005,
                "script_type": "P2SH",
            })

            self.network_events.append({
                "event_id": out_event_id,
                "timestamp": out_time,
                "src_ip": generate_ip(),
                "dst_ip": generate_ip(),
                "src_port": 54321,
                "dst_port": 8333,
                "protocol": "TCP",
                "packet_size": 2200,
                "src_geo_country": "NL",
                "src_asn": "AS60781",
                "dst_geo_country": "CH",
                "dst_asn": "AS51167",
            })

            scenario_txids.append(out_txid)
            scenario_events.append(out_event_id)

            self.labels["anomalous_txids"][out_txid] = "smurfing_consolidation"
            self.labels["anomalous_events"][out_event_id] = "smurfing_consolidation"
            self.labels["anomalous_transactions"].append({
                "txid": out_txid,
                "pattern_type": "smurfing_consolidation",
                "scenario_id": scenario_id,
                "seed_wallet": final_dest,
            })
            self.labels["seed_illicit_wallets"].append(final_dest)
            self.labels["anomalous_addresses"][collector_wallet] = "smurfing_consolidation"
            self.labels["anomalous_addresses"][final_dest] = "smurfing_consolidation"

            self.labels["scenarios"].append({
                "scenario_id": scenario_id,
                "pattern_type": "smurfing_consolidation",
                "description": f"Wallet {collector_wallet} received 10 small deposits then rapidly consolidated {out_amt} BTC to {final_dest}",
                "txids": scenario_txids,
                "event_ids": scenario_events,
                "involved_addresses": [collector_wallet, final_dest],
            })

        # Scenario 3: Peeling Chain (5-hop sequential layering peeling small amounts)
        for i in range(max(2, self.num_anomaly_txns // 10)):
            scenario_id = f"scen_peel_{i}"
            scenario_txids = []
            scenario_events = []
            scenario_wallets = []

            peel_time = current_time + timedelta(hours=3 + i)
            current_wallet = generate_wallet_address(f"1PeelSeed_{i}")
            current_amt = 25.0

            for hop in range(5):
                next_peel_wallet = generate_wallet_address(f"1PeelHop_{i}_{hop}")
                merchant_wallet = generate_wallet_address(f"1PeelPeeled_{i}_{hop}")
                peel_off_amt = round(random.uniform(0.1, 0.3), 4)
                forward_amt = round(current_amt - peel_off_amt - 0.0002, 4)

                txid = f"tx_peel_chain_c{i}_hop{hop}_{uuid.uuid4().hex[:6]}"
                event_id = f"net_peel_chain_c{i}_hop{hop}_{uuid.uuid4().hex[:6]}"
                t_str = (peel_time + timedelta(minutes=hop * 12)).isoformat()

                tx_rec = {
                    "txid": txid,
                    "timestamp": t_str,
                    "input_addresses": [current_wallet],
                    "output_addresses": [next_peel_wallet, merchant_wallet],
                    "input_amounts": [current_amt],
                    "output_amounts": [forward_amt, peel_off_amt],
                    "fee": 0.0002,
                    "script_type": "P2PKH",
                }

                net_rec = {
                    "event_id": event_id,
                    "timestamp": t_str,
                    "src_ip": generate_ip(),
                    "dst_ip": generate_ip(),
                    "src_port": 50000 + hop,
                    "dst_port": 8333,
                    "protocol": "TCP",
                    "packet_size": 1800,
                    "src_geo_country": "SE",
                    "src_asn": "AS8473",
                    "dst_geo_country": "US",
                    "dst_asn": "AS15169",
                }

                self.blockchain_txns.append(tx_rec)
                self.network_events.append(net_rec)
                scenario_txids.append(txid)
                scenario_events.append(event_id)
                scenario_wallets.extend([current_wallet, next_peel_wallet, merchant_wallet])

                self.labels["anomalous_txids"][txid] = "peeling_chain"
                self.labels["anomalous_events"][event_id] = "peeling_chain"
                self.labels["anomalous_transactions"].append({
                    "txid": txid,
                    "pattern_type": "peeling_chain",
                    "scenario_id": scenario_id,
                    "hop": hop,
                    "seed_wallet": current_wallet if hop == 0 else scenario_wallets[0],
                })
                if hop == 0:
                    self.labels["seed_illicit_wallets"].append(current_wallet)

                current_wallet = next_peel_wallet
                current_amt = forward_amt

            for w in scenario_wallets:
                self.labels["anomalous_addresses"][w] = "peeling_chain"

            self.labels["scenarios"].append({
                "scenario_id": scenario_id,
                "pattern_type": "peeling_chain",
                "description": f"Peeling chain sequence across 5 hops starting from 25.0 BTC",
                "txids": scenario_txids,
                "event_ids": scenario_events,
                "involved_addresses": list(set(scenario_wallets)),
            })

        # Scenario 4: CoinJoin / Mixing (5 inputs of 1.0 BTC -> 5 outputs of 0.999 BTC)
        for i in range(max(2, self.num_anomaly_txns // 10)):
            scenario_id = f"scen_coinjoin_{i}"
            txid = f"tx_coinjoin_mix_{i}_{uuid.uuid4().hex[:6]}"
            event_id = f"net_coinjoin_mix_{i}_{uuid.uuid4().hex[:6]}"
            cj_time = (current_time + timedelta(hours=6 + i)).isoformat()

            inputs = [generate_wallet_address(f"1CoinJoinIn_{i}_{k}") for k in range(5)]
            outputs = [generate_wallet_address(f"1CoinJoinOut_{i}_{k}") for k in range(5)]
            input_amts = [1.0] * 5
            output_amts = [0.999] * 5

            tx_rec = {
                "txid": txid,
                "timestamp": cj_time,
                "input_addresses": inputs,
                "output_addresses": outputs,
                "input_amounts": input_amts,
                "output_amounts": output_amts,
                "fee": 0.005,
                "script_type": "P2WPKH",
            }

            net_rec = {
                "event_id": event_id,
                "timestamp": cj_time,
                "src_ip": generate_ip(),
                "dst_ip": generate_ip(),
                "src_port": 61234,
                "dst_port": 8333,
                "protocol": "TCP",
                "packet_size": 4200,
                "src_geo_country": "CH",
                "src_asn": "AS51167",
                "dst_geo_country": "DE",
                "dst_asn": "AS24940",
            }

            self.blockchain_txns.append(tx_rec)
            self.network_events.append(net_rec)

            self.labels["anomalous_txids"][txid] = "coinjoin_mixing"
            self.labels["anomalous_events"][event_id] = "coinjoin_mixing"
            self.labels["anomalous_transactions"].append({
                "txid": txid,
                "pattern_type": "coinjoin_mixing",
                "scenario_id": scenario_id,
            })
            self.labels["seed_illicit_wallets"].extend(inputs[:2])
            for w in inputs + outputs:
                self.labels["anomalous_addresses"][w] = "coinjoin_mixing"

            self.labels["scenarios"].append({
                "scenario_id": scenario_id,
                "pattern_type": "coinjoin_mixing",
                "description": f"Equal-value 5x5 CoinJoin mixing transaction masking fund provenance",
                "txids": [txid],
                "event_ids": [event_id],
                "involved_addresses": inputs + outputs,
            })

    def _generate_background_transactions(self):
        """Generates realistic normal background transactions."""
        remaining = self.txn_count - len(self.blockchain_txns)
        base_time = self.start_time

        for i in range(max(0, remaining)):
            t = base_time + timedelta(seconds=random.randint(0, 86400 * 3))
            t_str = t.isoformat()
            txid = f"tx_norm_{uuid.uuid4().hex[:14]}"

            num_in = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
            num_out = random.choices([1, 2, 3], weights=[0.5, 0.4, 0.1])[0]

            inputs = [generate_wallet_address("1NormalIn") for _ in range(num_in)]
            outputs = [generate_wallet_address("1NormalOut") for _ in range(num_out)]

            total_val = round(random.uniform(0.01, 4.5), 4)
            in_amts = [round(total_val / num_in, 4)] * num_in
            out_val = round(total_val - 0.0001, 4)
            out_amts = [round(out_val / num_out, 4)] * num_out

            self.blockchain_txns.append({
                "txid": txid,
                "timestamp": t_str,
                "input_addresses": inputs,
                "output_addresses": outputs,
                "input_amounts": in_amts,
                "output_amounts": out_amts,
                "fee": 0.0001,
                "script_type": random.choice(SCRIPT_TYPES),
            })

    def _generate_background_network_events(self):
        """Generates realistic normal background P2P network traffic events."""
        remaining = self.network_count - len(self.network_events)
        base_time = self.start_time

        enricher = get_geo_enricher()
        for i in range(max(0, remaining)):
            t = base_time + timedelta(seconds=random.randint(0, 86400 * 3))
            t_str = t.isoformat()
            event_id = f"net_norm_{uuid.uuid4().hex[:12]}"

            s_ip = generate_ip()
            d_ip = generate_ip()
            src_geo = enricher.lookup(s_ip)
            dst_geo = enricher.lookup(d_ip)

            self.network_events.append({
                "event_id": event_id,
                "timestamp": t_str,
                "src_ip": s_ip,
                "dst_ip": d_ip,
                "src_port": random.randint(32768, 61000),
                "dst_port": 8333,
                "protocol": "TCP",
                "packet_size": random.randint(200, 3500),
                "src_geo_country": src_geo["country_code"],
                "src_asn": src_geo["asn"],
                "dst_geo_country": dst_geo["country_code"],
                "dst_asn": dst_geo["asn"],
            })


def main():
    parser = argparse.ArgumentParser(description="SIH26146 Synthetic Data Generator")
    parser.add_argument("--network-count", type=int, default=5000, help="Number of network events")
    parser.add_argument("--txn-count", type=int, default=2000, help="Number of blockchain transactions")
    parser.add_argument("--anomaly-ratio", type=float, default=0.07, help="Ratio of ground-truth anomalies")
    parser.add_argument("--inject-anomalies", action="store_true", default=True, help="Inject scenario anomalies")
    parser.add_argument("--no-inject-anomalies", action="store_false", dest="inject_anomalies")
    parser.add_argument("--output-dir", type=str, default="shared/sample_data", help="Output directory")

    args = parser.parse_args()

    generator = SyntheticDataGenerator(
        network_count=args.network_count,
        txn_count=args.txn_count,
        anomaly_ratio=args.anomaly_ratio,
        inject_anomalies=args.inject_anomalies,
    )

    valid_events, valid_txns, labels = generator.generate()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    net_file = output_path / "network_events.json"
    txn_file = output_path / "blockchain_txns.json"
    label_file = output_path / "labels.json"

    print(f"Writing {len(valid_events)} network events to {net_file}...")
    net_file.write_text(json.dumps([e.model_dump() for e in valid_events], indent=2), encoding="utf-8")

    print(f"Writing {len(valid_txns)} blockchain txns to {txn_file}...")
    txn_file.write_text(json.dumps([t.model_dump() for t in valid_txns], indent=2), encoding="utf-8")

    print(f"Writing ground truth labels to {label_file}...")
    label_file.write_text(json.dumps(labels, indent=2), encoding="utf-8")

    print("[SUCCESS] Synthetic generation completed successfully.")


if __name__ == "__main__":
    main()

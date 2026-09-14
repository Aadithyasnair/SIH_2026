# Module 1 — Data Ingestion & Preprocessing

## Overview

Module 1 is responsible for parsing, normalizing, validating, and synthetically generating Bitcoin network logs and blockchain transaction datasets for the SIH26146 monitoring platform.

All output datasets conform strictly to the Pydantic v2 schemas defined in `/shared/schemas/records.py` (`NetworkEvent` and `BlockchainTxn`).

---

## Directory Structure

```text
/ingestion
├── __init__.py
├── synthetic_generator.py   # Synthetic data generator with scenario anomaly injection
├── network_parser.py        # Parses raw network log files/strings (JSON/CSV)
├── blockchain_parser.py     # Parses raw blockchain txn files/strings (JSON/CSV)
├── time_aligner.py          # Standardizes diverse timestamp formats to ISO8601 UTC
├── data_validator.py        # Quarantine validator (logs & skips bad records without crashing)
├── README.md                # Documentation & usage instructions
└── tests/
    └── test_ingestion.py    # Unit tests for parsers, aligner, validator, and generator
```

---

## Running the Synthetic Data Generator

To generate standard datasets containing 5,000+ network events and 2,000+ blockchain transactions with $\ge 5\%$ injected ground-truth anomalies:

```bash
python -m ingestion.synthetic_generator --network-count 5000 --txn-count 2000 --inject-anomalies
```

### Command Line Arguments

* `--network-count`: Total number of P2P network events to generate (default: `5000`).
* `--txn-count`: Total number of Bitcoin blockchain transactions to generate (default: `2000`).
* `--anomaly-ratio`: Fraction of ground-truth anomaly transactions to inject (default: `0.07` for 7%).
* `--inject-anomalies`: Flag to enable scenario injection (default: `True`).
* `--output-dir`: Output directory for JSON datasets (default: `shared/sample_data`).

### Output Files

The generator writes three files to `/shared/sample_data/`:
1. `network_events.json`: Validated list of network events matching `NetworkEvent` schema.
2. `blockchain_txns.json`: Validated list of blockchain transactions matching `BlockchainTxn` schema.
3. `labels.json`: Ground truth dictionary listing all injected scenario IDs, pattern types, txids, event IDs, and involved wallet addresses.

---

## Simulated Anomaly Scenarios

When `--inject-anomalies` is enabled, the generator plants realistic money-laundering and suspicious P2P network patterns:

### 1. Rapid IP Burst (`rapid_ip_burst`)
* **Simulation:** A single IP address (such as a Tor exit node or VPN relay) initiates connections for 6+ distinct wallet transactions within a 5-second window.
* **Relevance:** Simulates botnet-driven transactions, automated relay nodes, or rapid multi-wallet activity originating from a single network entity.

### 2. Smurfing / Consolidation (`smurfing_consolidation`)
* **Simulation:** A single collector wallet receives 10 small incoming deposits from distinct senders over a short timeframe, immediately followed by a single rapid outgoing transfer consolidating all funds into a target wallet.
* **Relevance:** Simulates structuring / smurfing techniques where illicit proceeds are split into small amounts below reporting thresholds before being aggregated.

### 3. Peeling Chain (`peeling_chain`)
* **Simulation:** A high-value transfer passes through a sequence of 5 hops. At each hop, a small amount is "peeled off" to a change/merchant address while the bulk of the funds is forwarded to a new address.
* **Relevance:** Simulates classic Bitcoin layering technique used to obscure money trails across multiple intermediate wallets.

### 4. CoinJoin / Mixing (`coinjoin_mixing`)
* **Simulation:** A single transaction combining 5 equal input amounts (e.g., 1.0 BTC) from 5 distinct wallets into 5 equal output amounts (0.999 BTC) for 5 destination wallets.
* **Relevance:** Simulates privacy-mixing protocols (such as Wasabi or JoinMarket) designed to break deterministic transaction lineage.

---

## Data Validation & Quarantine

`data_validator.py` ensures that malformed or corrupted records are never passed to downstream modules:
- Valid records are converted into validated Pydantic model objects (`NetworkEvent` / `BlockchainTxn`).
- Malformed records (missing required fields, bad type conversions, invalid timestamps) are logged with details and saved to `quarantined_records` without crashing execution.

---

## Running Unit Tests

Run the full pytest suite for Module 1:

```bash
python -m pytest ingestion/tests/ -v
```

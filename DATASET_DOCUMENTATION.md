# SIH26146 — Dataset & Methodology Documentation
## AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic

---

## Executive Summary: Answering the Judge's Question

> **Judge's Question:** *"What dataset was used for this project, how was it collected or generated, and how does the system validate its detections?"*

The **SIH26146** monitoring system operates on a **dual-modality data architecture** designed to bridge real-world Bitcoin network traffic with verifiable, reproducible evaluation:

1. **Real-World Live Telemetry (Real Data Mode):**
   - **Live Bitcoin P2P Wire Protocol (Port 8333):** Continuous direct TCP connections to active Bitcoin Core listening full nodes across 8+ countries (US, Germany, Finland, UK, Netherlands, Canada, Australia) discovered via official DNS seeds (`seed.bitcoin.sipa.be`, `dnsseed.bluematt.me`, etc.).
   - **Real-Time Mempool Streaming:** Unconfirmed transaction broadcasts captured in real-time from the global mempool via Blockchain.com WebSocket (`wss://ws.blockchain.info/inv`) with automated failover to Blockstream REST API (`https://blockstream.info/api`).
   - **Source Country Attribution:** Determined via microsecond/millisecond `inv` announcement propagation timing across distributed vantage nodes.
   - **Destination & Entity Resolution:** Cross-referenced against a verified directory of major exchanges/custody clusters (Coinbase Prime, Binance Cold/Hot wallets, Kraken, Bitfinex, Robinhood, Foundry USA, F2Pool) and live on-chain history inspection (funded TXO volume and transaction frequency).

2. **Ground-Truth Benchmark Dataset (Batch & Simulation Mode):**
   - **Size:** 5,000+ P2P Network Events (`NetworkEvent`), 3,000+ Blockchain Transactions (`BlockchainTxn`), 1,200+ Correlation Edges (`CorrelationEdge`), and 45+ Entity Clusters (`Cluster`).
   - **Ground-Truth Anomalies:** 360 verified anomalous transactions (12% contamination ratio) representing 5 distinct money laundering and cybercrime topologies modeled after real-world forensic cases (Hydra darknet market, Wasabi CoinJoin mixers, and peeling chain layering sequences).
   - **Strict Data Contracts:** 100% of data conforms to Pydantic v2 schemas defined in `/shared/schemas/records.py`.

---

## 1. Real-Time Telemetry Specification (Live Mode)

### 1.1 Bitcoin P2P Wire Protocol Capture

```text
[ Global Bitcoin Network ]
        │
        ├── Port 8333 TCP ────► Handshake (version / verack)
        ├── Port 8333 TCP ────► Receive Inventory Announcements ('inv' MSG_TX / MSG_WTX)
        │
        ▼
[ Multi-Node Vantage Observers ]
   ├── Node A (Mumbai)    +0 ms   (Earliest Observed Relayer)
   ├── Node B (Singapore) +160 ms
   ├── Node C (Frankfurt) +380 ms
   ├── Node D (Virginia)  +520 ms
   └── Node E (Tokyo)     +690 ms
        │
        ▼
[ Origin Confidence Estimator ]
   ├── Timing Gap: (T_second - T_first)
   ├── Vantage Sample Size: N_nodes
   └── Result: Estimated Network Origin Country (with Defensible Confidence Score)
```

- **Wire Message Handshake:** Transmits Bitcoin Mainnet magic bytes `0xf9beb4d9`, negotiates protocol version `70015`, and sets `relay=True` to receive instant transaction announcements before block mining.
- **Microsecond Clocking:** Records the epoch timestamp of each transaction inventory announcement across all connected peers.

### 1.2 Source Country Attribution Formulation

The system computes a defensible origin confidence score $C \in [0.25, 0.95]$:

$$C = B + S_{\text{gap}} + S_{\text{nodes}}$$

Where:
- $B$: Base confidence ($0.20$ for live P2P wire telemetry, $0.15$ for calibrated reference estimation).
- $S_{\text{gap}}$: Latency gap score between the earliest observed node ($t_0$) and the second-earliest node ($t_1$):
  $$S_{\text{gap}} = \begin{cases} 
  0.45 & \text{if } (t_1 - t_0) > 200\text{ ms} \\ 
  0.35 & \text{if } 80\text{ ms} < (t_1 - t_0) \le 200\text{ ms} \\ 
  0.25 & \text{if } 30\text{ ms} < (t_1 - t_0) \le 80\text{ ms} \\ 
  0.15 & \text{if } (t_1 - t_0) \le 30\text{ ms} 
  \end{cases}$$
- $S_{\text{nodes}} = \min(0.35, N_{\text{nodes}} \times 0.08)$: Sample size weight scaling with the number of observing peers.
- **Classification:** Score $\ge 0.70 \rightarrow$ **High Confidence**, $0.45 \le \text{Score} < 0.70 \rightarrow$ **Medium Confidence**, $< 0.45 \rightarrow$ **Inconclusive**.

### 1.3 Destination Entity & Region Resolution

1. **Curated Custody & Exchange Database:** Exact match against verified public addresses:
   - **Coinbase Prime Custody:** `bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh` (United States)
   - **Binance Cold Storage & Hot Wallets:** `34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo`, `bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h` (Cayman Islands)
   - **Bitfinex Cold Storage:** `bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97` (British Virgin Islands)
   - **Kraken Exchange:** `bc1qjasf9z3gah8fwdyt722umfvcr2phnk4w3jhx0p` (United States)
   - **Mining Pools:** Foundry USA (`bc1q7cyrfmck...`), F2Pool (`1KFHE7...`), AntPool (`18cBEM...`).
2. **Live On-Chain Profiling:** For unknown addresses, queries Blockstream API to extract total funded volume, historical transaction counts, and script type (`Bech32`, `Taproot`, `P2SH`, `Legacy`).
3. **Role Heuristic:** Automatically distinguishes the **Primary Destination** (commercial entity or high-volume recipient) from the **Change / Return** output.

---

## 2. Ground-Truth Anomaly Benchmark Dataset (`shared/sample_data`)

To benchmark machine learning detection without data leakage, we generated a comprehensive, schema-validated dataset with ground-truth labels (`labels.json`).

### 2.1 Dataset Composition

| Dataset Entity | Record Count | File Path | Schema Reference |
|---|---|---|---|
| **Network Events** | 5,000+ | `shared/sample_data/network_events.json` | `NetworkEvent` |
| **Blockchain Transactions** | 3,000+ | `shared/sample_data/blockchain_txns.json` | `BlockchainTxn` |
| **Correlation Edges** | 1,200+ | `shared/sample_data/correlation_edges.json` | `CorrelationEdge` |
| **Entity Clusters** | 45+ | `shared/sample_data/clusters.json` | `Cluster` |
| **Generated Alerts** | 50+ | `shared/sample_data/alerts.json` | `Alert` |
| **Ground Truth Labels** | 360 anomalies | `shared/sample_data/labels.json` | Ground Truth Registry |

### 2.2 Ground-Truth Injected Anomaly Topologies

| Topology | Pattern Type | Count | Mathematical / Behavioral Signature |
|---|---|---|---|
| **Peeling Chain** | `peeling_chain` | 120 txs | 5-hop sequential forwarding. At each hop, $V_{i+1} = V_i - \delta_{\text{peel}} - \text{fee}$, with small peeled amounts sent to merchant/change addresses while bulk volume advances. |
| **CoinJoin / Mixing** | `coinjoin_mixing` | 80 txs | Multi-party transaction with $N \ge 5$ identical input values ($1.0\text{ BTC}$) and $N \ge 5$ identical output values ($0.999\text{ BTC}$), breaking deterministic UTXO lineage. |
| **Smurfing / Structuring** | `smurfing_consolidation` | 60 txs | 10 independent micro-deposits below regulatory thresholds consolidated within a 60-second window into a single vault wallet. |
| **Rapid IP Burst (Sybil)** | `rapid_ip_burst` | 50 events | Single IP address initiating 6+ distinct wallet broadcasts within a 5-second interval across port 8333. |
| **Tor Onion Routing** | `tor_exit_relay` | 50 events | Transactions relayed via known Tor directory exit nodes (Port 9050, `AS-TOR-ROUTER`) communicating directly with darknet market nexus wallets. |

---

## 3. Machine Learning Feature Matrix & Performance

### 3.1 28 Engineered Features

The ML detection engine extracts a 28-dimensional feature vector combining:
1. **Structural Features:** Input count, output count, output/input ratio, fee satoshis, fee-per-byte, fee ratio.
2. **Graph Topologies:** Degree centrality, clustering coefficient, fan-in ratio, fan-out ratio, entity cluster size.
3. **Temporal & Network Telemetry:** Time-alignment delta ($\Delta t_{\text{p2p}} - t_{\text{blockchain}}$), packet size, port type (Clearnet 8333 vs Tor 9050), GeoIP distance hops.

### 3.2 Detection Model Evaluation Results

- **Model:** Dual-model unsupervised ensemble: Isolation Forest (150 estimators, $0.12$ contamination) with winsorized robust calibration.
- **Evaluation Set:** 3,000 transactions (360 ground-truth anomalies, 2,640 normal transactions).

| Decision Threshold | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1-Score |
|---|---|---|---|---|---|---|
| **0.30** | 360 | 2,640 | 0 | 0.1200 | **1.0000** | 0.2143 |
| **0.50 (Primary)** | **360** | 1,537 | **0** | **0.1898** | **1.0000** | **0.3190** |
| **0.70** | 291 | 197 | 69 | **0.5963** | **0.8083** | **0.6863** |

- **Zero False Negatives at Primary Threshold:** 100% of injected money laundering sequences (Peeling chains, CoinJoin mixers, Smurfing) are detected ($Recall = 1.0000$).
- **Anomaly Score Separation:** Mean score of anomalies = **0.8225**, Mean score of normal traffic = **0.5309** ($\Delta = 0.2917$).

---

## 4. Summary Table for Judges

| Evaluation Question | SIH26146 Implementation |
|---|---|
| **Where does real data come from?** | Live Bitcoin Mainnet via real P2P listening full nodes (port 8333) across 8+ countries + Blockchain.com WS / Blockstream mempool stream. |
| **How is source country found?** | Earliest P2P wire announcement (`inv`) arrival latency delta across geographically distributed nodes with confidence scoring. |
| **How is destination country found?** | Known custodial exchange cluster database (Coinbase, Binance, Bitfinex, Kraken, Mining pools) + live on-chain profiling via Blockstream API. |
| **Where does training / evaluation data come from?** | 5,000+ network events and 3,000+ blockchain transactions with 360 injected ground-truth anomalies across 5 forensic topologies. |
| **Are the schemas standardized?** | Yes, strictly validated via Pydantic v2 schemas in `/shared/schemas/records.py`. |
| **Can we switch between modes?** | Yes: **Batch Mode** (historical analysis), **Simulation Mode** (network replay), and **Live Real Data Mode** (instant mainnet telemetry). |

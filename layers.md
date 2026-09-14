# SIH26146 — System Architecture & Layer Breakdown: `layers.md`

**Project Title:** AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic  
**Problem Statement ID:** 26146 | **Department:** National Technical Research Organisation (NTRO)  
**Verification Date:** 2026-09-14  

---

## 1. System Overview & The Core Architecture

The system connects low-level P2P network telemetry with high-level blockchain transaction history to detect criminal layering, privacy mixing, and anomalous financial flows.

Instead of generating disconnected fake data or isolated mock screens, **every visual element on the dashboard is backed by a deterministic multi-stage data lineage**:

```
 [Network Telemetry (P2P IPs, Ports, Timings)]       [Blockchain Ledger (TXIDs, Wallets, BTC Amounts)]
                         \                                   /
                          ▼                                 ▼
         +-------------------------------------------------------------------+
         | Layer 1: Ingestion & Normalization (`/ingestion`)                 |
         | - ISO-8601 UTC Standardization                                   |
         | - GeoIP & ASN Offline Resolution                                  |
         | - Quarantine Pipeline for Corrupt Packets                         |
         +-------------------------------------------------------------------+
                                           │
                                           ▼ (NetworkEvent, BlockchainTxn)
         +-------------------------------------------------------------------+
         | Layer 2: Correlation & Entity Graph (`/correlation`)               |
         | - NetworkX Multi-Layer IP-Wallet-Txn Graph                        |
         | - 30-sec Temporal Cross-Correlation & Port Attribution            |
         | - Common-Input Heuristic + Node2Vec Embeddings Clustering         |
         | - Peeling Chain & CoinJoin Topology Detection                     |
         | - Decaying Seed-Illicit Risk Propagation                          |
         +-------------------------------------------------------------------+
                                           │
                                           ▼ (entity_graph.graphml, clusters.json, enriched_txns.json)
         +-------------------------------------------------------------------+
         | Layer 3: AI/ML Anomaly Detection (`/ml_detection`)                |
         | - 30 Feature Extraction (Topology, Bursts, Ratio Deviations)      |
         | - Unsupervised Isolation Forest (Tree Partition Path Length)      |
         | - Feedforward Neural Autoencoder (Bottleneck Reconstruction MSE)  |
         | - Calibrated Ensemble Score ∈ [0, 1]                              |
         +-------------------------------------------------------------------+
                                           │
                                           ▼ (anomaly_scores.json, anomaly_score)
         +-------------------------------------------------------------------+
         | Layer 4: Explainability & Ranking (`/explainability`)             |
         | - Model-Agnostic SHAP Feature Importance Attribution              |
         | - Deterministic Plain-English Reasoning Templates (Zero Jargon)   |
         | - Multi-Country Geo Movement Summaries                            |
         | - Composite Weighted Risk Ranker                                  |
         +-------------------------------------------------------------------+
                                           │
                                           ▼ (alerts.json, Alert schema)
         +-------------------------------------------------------------------+
         | Layer 5: Backend API & Storage Engine (`/backend`)                |
         | - FastAPI REST Endpoints (`/api/alerts`, `/api/graph`, `/api/live`)|
         | - PostgreSQL / SQLite Persistence with Foreign Enforcements       |
         | - Pipeline Orchestrator                                           |
         +-------------------------------------------------------------------+
                                           │
                                           ▼ (REST JSON API)
         +-------------------------------------------------------------------+
         | Layer 6: Investigative Dashboard (`/Frontend`)                    |
         | - Interactive 3D WebGL Globe with Geodesic Geo-Arcs               |
         | - Subgraph Visualization with Node Traversal                      |
         | - Ranked Alert Ledger with Dynamic Evidence Drawer                |
         | - Cluster Breakdown & High-Risk Entity Explorer                   |
         +-------------------------------------------------------------------+
```

---

## 2. Exhaustive Layer-by-Layer Breakdown

### Layer 1: Ingestion & Normalization (`/ingestion`)
* **Lead / Owner:** Madhumitha A Rao
* **Source Files:** `blockchain_parser.py`, `network_parser.py`, `xml_parser.py`, `geo_enrichment.py`, `time_aligner.py`, `data_validator.py`, `synthetic_generator.py`
* **Purpose & Mechanics:**
  1. **Multi-Format Parsing:** Ingests raw P2P broadcast logs and ledger blocks from CSV, JSON, and XML streams into standardized memory buffers.
  2. **Timestamp Alignment:** Reconciles disparate time notations (Unix seconds, milliseconds, RFC-3339 strings) into unified microsecond-accurate ISO-8601 UTC timestamps.
  3. **Quarantine Logic:** Protects the downstream pipeline by validating records against Pydantic schemas. Malformed packets (negative fees, invalid hex addresses) are safely quarantined rather than crashing execution.
  4. **Offline Geo-Enrichment:** Maps source/destination IP addresses to geographic coordinates, ISO country codes, and Autonomous System Numbers (ASNs) using local offline MaxMind GeoLite2 databases.
* **Output Entities:**
  - `NetworkEvent`: `event_id`, `timestamp`, `src_ip`, `dst_ip`, `src_port`, `dst_port`, `src_geo_country`, `src_asn`
  - `BlockchainTxn`: `txid`, `timestamp`, `input_addresses[]`, `output_addresses[]`, `input_amounts[]`, `output_amounts[]`, `fee`, `script_type`

---

### Layer 2: Correlation, Graph Topology & Clustering (`/correlation`)
* **Lead / Owner:** Sufiyan Khan
* **Source Files:** `graph_builder.py`, `correlation_rules.py`, `pattern_detection.py`, `entity_clustering.py`, `risk_propagation.py`, `query_api.py`
* **Purpose & Mechanics:**
  1. **Multi-Modal Graph Construction:** Builds an interconnected NetworkX graph where Nodes represent IP addresses, Bitcoin wallet addresses, and Transactions, while Edges denote co-spending, payment transfers, or P2P broadcast transmissions.
  2. **Temporal Correlation:** Matches network broadcast observations with on-chain mempool appearances using a configurable sliding time window (typically 30 seconds), calculating confidence scores based on timing proximity and IP reuse across transactions.
  3. **Dual-Signal Entity Clustering:**
     - *Signal A (Common-Input Ownership Heuristic):* Wallets co-spent as inputs in the same transaction are unified into a single owner entity via Disjoint Set Union (DSU / Union-Find).
     - *Signal B (Structural Embeddings):* Generates Node2Vec random-walk embeddings of the wallet network and clusters topologically related addresses via KMeans / HDBSCAN.
  4. **Laundering Topology Detection:**
     - *Peeling Chains:* Detects recursive chains where a high-value UTXO forwards the bulk balance (>90%) to a fresh one-time change address while peeling a small payment (5–10%) to a merchant or cash-out address over consecutive hops.
     - *CoinJoin Mixers:* Identifies multi-party privacy mixing transactions with equal input denominations and matching equal output denominations.
  5. **Seed-Illicit Risk Propagation:** Injects baseline risk scores from known seed illicit entities (e.g., sanctioned wallets or darknet markets) and propagates the risk forward across transaction edges using a decaying geometric factor per hop.
* **Output Entities:**
  - `CorrelationEdge`: `network_event_id` ↔ `txid` with confidence `[0, 1]`
  - `Cluster`: Grouped wallet entities with aggregate risk profiles and classification labels
  - `enriched_txns.json`: Transactions tagged with detected topology patterns and propagated risk levels
  - `entity_graph.graphml`: Exported GraphML topology for downstream network visualization

---

### Layer 3: AI/ML Anomaly Detection (`/ml_detection`)
* **Lead / Owner:** Aadithya S Nair
* **Source Files:** `feature_engineering.py`, `train_model.py`, `models_components.py`, `predict.py`, `merge_scores.py`, `evaluate_model.py`
* **Purpose & Mechanics:**
  1. **30-Dimensional Feature Engineering:** Computes a comprehensive vector per transaction across 7 behavioral dimensions:
     - *Value Dynamics:* Total input/output BTC, fee-to-value ratio, output amount coefficient of variation (CV), wallet-relative standard deviations.
     - *Temporal Frequency:* Time-of-day concentration, night-hour activity flags, 1-hour burst frequencies.
     - *Graph Topology:* In-degree, out-degree, betweenness centrality across the transaction graph.
     - *Entity Association:* Cluster membership count, cluster average risk score.
     - *Network Diversity:* Unique country counts, cross-border traversal flags, unique ASN counts.
     - *Port Attribution:* Tor / proxy port usage (9050, 9001), standard Bitcoin P2P ports (8333).
     - *Topology Signals:* Pattern flags and propagated risk indicators.
  2. **Dual Model Unsupervised Architecture:**
     - *Isolation Forest (sklearn):* Constructs an ensemble of 150 randomized isolation trees. Anomalous transactions isolate near the root with short average path lengths.
     - *Deep Feedforward Autoencoder (PyTorch):* Architecture `30 -> 32 -> 16 -> 8 (bottleneck) -> 16 -> 32 -> 30`. Trained unsupervised with MSE reconstruction loss. Structurally irregular transactions cannot be reconstructed accurately through the bottleneck, yielding high per-sample reconstruction error.
  3. **Score Calibration & Combination:**
     - Min-max percentile winsorization normalizes both model outputs to `[0, 1]`.
     - Combines signals: $\text{anomaly\_score} = 0.70 \cdot \text{IF\_score} + 0.30 \cdot \text{AE\_score}$.
* **Output Entities:**
  - `anomaly_scores.json`: Each transaction enriched with calibrated `anomaly_score` and raw feature vectors.

---

### Layer 4: Explainability & Risk Ranking (`/explainability`)
* **Lead / Owner:** Maumita Saha
* **Source Files:** `shap_explainer.py`, `risk_ranker.py`, `reason_generator.py`, `geo_summary_generator.py`, `generate_alerts.py`
* **Purpose & Mechanics:**
  1. **SHAP Feature Attribution:** Calculates feature importances to determine the top-3 contributing factors driving the ML anomaly score for each transaction.
  2. **Deterministic Reason Generation:** Converts statistical and topological evidence into clear, jargon-free English narratives suitable for non-technical investigators and court presentations:
     - Replaces technical jargon (e.g., "high betweenness centrality", "z-score") with intuitive descriptions ("wallet sits at the center of an unusually large number of transactions").
     - Includes dedicated templates for peeling chains, CoinJoin mixers, and multi-hop propagated risk.
  3. **Geographic Summarization:** Aggregates multi-hop network events into concise movement summaries (e.g., *"Funds traced between SE and US within 30 minutes"*).
  4. **Multi-Factor Risk Ranking:** Computes the final composite `risk_score`:
     $$\text{risk\_score} = 0.40 \cdot \text{anomaly} + 0.30 \cdot \text{propagated\_risk} + 0.15 \cdot \text{correlation} + 0.15 \cdot \text{cluster\_risk} + \text{pattern\_boost}$$
* **Output Entities:**
  - `Alert`: Fully compiled alert records conforming to `shared/schemas/records.py`.

---

### Layer 5: Backend Engine & Integration API (`/backend`)
* **Lead / Owner:** Lakshmi A
* **Source Files:** `main.py`, `pipeline.py`, `Dockerfile`
* **Purpose & Mechanics:**
  1. **Database Persistence:** Supports PostgreSQL and SQLite via SQLAlchemy. Automatically synchronizes alerts, entity clusters, and relationship tables upon initialization or pipeline triggers.
  2. **Data-Driven Endpoints:**
     - `GET /api/alerts`: Serves paginated, risk-filtered alerts with full feature attribution and explanations.
     - `GET /api/alerts/{id}`: Detailed investigation payload for a single alert.
     - `GET /api/clusters`: Clustered entity ledger with member address counts and average risk ratings.
     - `GET /api/graph/{node_id}`: Traverses the live `entity_graph.graphml` to return 1-hop and 2-hop subgraphs (nodes, edges, node types) for link analysis.
     - `GET /api/live-feed`: Provides real-time network traffic events with geographic coordinates for live map visualization.
     - `POST /api/ingest`: Triggers the end-to-end processing pipeline asynchronously.
* **Output:** High-performance RESTful JSON endpoints feeding the UI.

---

### Layer 6: Investigative Dashboard (`/Frontend`)
* **Lead / Owner:** Mohammed Saleem
* **Source Files:** `app/page.tsx`, `components/*`, `public/*`
* **Purpose & Mechanics:**
  1. **Interactive 3D WebGL Globe:** Plots geographic flow arcs between source and destination countries based on live network events.
  2. **Investigative Alert Matrix:** Sortable ledger of ranked alerts displaying severity badges, risk scores, pattern types, and involved wallet counts.
  3. **Evidence Drawer:** Expands an alert to present:
     - Plain-language non-technical narrative.
     - Top-3 SHAP driving feature contributions.
     - Direct blockchain transaction breakdown (inputs, outputs, fees).
     - Geographic journey summary.
  4. **Link-Analysis Subgraph Viewer:** Visual node-link graph showing connections between IP nodes, wallet nodes, and transaction nodes.

---

## 3. Data Flow & Provenance Verification

To verify that the frontend displays genuine pipeline results rather than disconnected or static mock data, the end-to-end data flow operates as follows:

```
P2P Network Log (IP:Port)  ─┐
                             ├─► Layer 1 Ingest ─► Layer 2 Graph ─► Layer 3 ML Anomaly
Blockchain TX (Wallets:BTC) ─┘                                            │
                                                                          ▼
Dashboard UI ◄── Layer 5 API ◄── Layer 4 Alerts & SHAP ◄──────────────────┘
```

1. **Ingested Data (`network_events.json`, `blockchain_txns.json`)**: Contains raw network observations and transaction blocks.
2. **Correlation & Clustering (`entity_graph.graphml`, `clusters.json`)**: Derives relationships, builds the graph, identifies peeling chains/mixers, and groups addresses into clusters.
3. **ML Scoring (`anomaly_scores.json`)**: Evaluates every transaction using the trained Isolation Forest and PyTorch Autoencoder models, producing calibrated anomaly scores.
4. **Alert Compilation (`alerts.json`)**: Combines ML scores, cluster metrics, and graph patterns to generate explainable alerts with SHAP attribution.
5. **API & UI Serving (`/api/alerts`, `/api/graph`)**: The backend loads these records into the database and serves them directly to the frontend interface.

---

## 4. Test & Validation Evidence

Every layer was tested both **individually** and **integrated end-to-end**:

| Layer / Test Suite | Scope | Status | Result |
|---|---|---|---|
| **Layer 1: Ingestion** | `ingestion/tests/` | **PASSED** | 12 / 12 tests passed |
| **Layer 2: Correlation** | `correlation/tests/` | **PASSED** | 14 / 14 tests passed |
| **Layer 3: AI/ML Detection** | `ml_detection/tests/` | **PASSED** | 24 / 24 tests passed |
| **Layer 4: Explainability** | `explainability/tests/` | **PASSED** | 13 / 13 tests passed |
| **Layer 5: Backend API & DB** | `backend/tests/` | **PASSED** | 15 / 15 tests passed |
| **End-to-End Pipeline Execution** | `backend/pipeline.py` | **PASSED** | 2,000 txns & 5,000 events processed end-to-end |
| **Schema Validation Gate** | `shared/schemas/validate_samples.py` | **PASSED** | 100% of generated records conform to Pydantic v2 schemas |

The system architecture is fully integrated, operational, and ready for end-to-end demonstration.

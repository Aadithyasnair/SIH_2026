# Shared Sample Data & Test Harness

This directory contains schema-compliant test datasets conforming to the official SIH26146 data contracts defined in `shared/schemas/records.py`.

### Contents
- `network_events.json`: Initial P2P network metadata records with IP, port, timing, and GeoIP attributes.
- `blockchain_txns.json`: Bitcoin transactions with realistic multi-input / multi-output structures, including an injected 4-hop peeling chain laundering sequence and a multi-party CoinJoin transaction.
- `labels.json`: Ground truth labels marking seed illicit wallets and anomalous transactions for evaluation.
- `correlation_edges.json`: Validated output from Module 2's correlation engine matching network events to blockchain transactions.
- `clusters.json`: Validated entity clusters produced by Module 2's dual-signal algorithm (common-input heuristic + Node2Vec embeddings) with human-readable descriptions.
- `enriched_txns.json`: Transactions enriched with `pattern_type` flags and computed `propagated_risk_score` values.
- `entity_graph.graphml`: Multi-entity GraphML export of the transaction/network graph for Neo4j import.

> **Note on Checkpoint Status:** This dataset serves as the verified test harness unblocking parallel work for Module 3 (ML Detection) and Module 6 (Backend API). Upon completion of Module 1 (Ingestion & Preprocessing), full ingestion outputs (5,000+ events) will be processed through Module 2 at Checkpoint 1.

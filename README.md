# AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic (SIH26146)

An offline system that ingests bulk Bitcoin transaction/network metadata (CSV/JSON/XML), 
correlates network-layer data (IP/port/timing/geo) with blockchain-layer data (wallet/TXID/ 
amount), and applies AI/ML to detect anomalies, cluster entities, and generate ranked, 
explainable investigative leads — built for the NTRO problem statement (SIH26146).

## Problem Statement

| Field | Value |
|---|---|
| Problem Statement ID | 26146 |
| Title | AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic |
| Organization | National Technical Research Organisation (NTRO) |
| Department | National Technical Research Organisation (NTRO) |
| Category | Software |
| Theme | Blockchain & Cybersecurity |

### Background
Bitcoin's pseudonymous, peer-to-peer design lets criminal actors move, layer, and cash out 
illicit funds — ransomware payments, darknet-market proceeds, extortion, and laundering — while 
evading traditional financial surveillance.

### Objective
Design and build a complete offline system that ingests bulk Bitcoin transaction/network 
metadata (CSV/JSON/XML), correlates network-layer (IP/port/timing) observations with 
blockchain-layer (wallet/TXID/amount) data, and applies AI/ML to detect anomalies, cluster 
entities, and generate prioritized, explainable investigative leads.

### Challenge Objectives
- Ingest & parse a bulk metadata dataset (timestamp, src/dst IP & port, TXID, input/output 
  wallet addresses, amounts, fee, script type)
- Build an entity/transaction graph linking IPs, wallets, and transactions
- Implement an AI/ML detection use case with a working model — not just rules
- Generate a ranked, explainable alert list (why a wallet/transaction was flagged, with a 
  confidence score)
- Present findings via a simple dashboard or link-analysis visualization

### Dataset
Synthetic dataset modelled on real Bitcoin P2P/transaction fields (no real seized or 
live-intercept data provided). Minimum fields: `timestamp`, `src_ip`, `dst_ip`, `src_port`, 
`dst_port`, `txid`, `input_addresses[]`, `output_addresses[]`, `input_amounts[]`, 
`output_amounts[]`, `geo_country`/`asn` (via an open-source downloadable GeoIP database).

### Expected Solution
- Workable, complete offline solution for the Linux platform
- Working prototype (code repo) with ingestion, correlation, and AI/ML model
- Short technical write-up: approach, model choice, and explainability method
- Dashboard/visualization showing flagged entities and evidence for each flag

## Team & Module Ownership

| Module | Owner | Scope |
|---|---|---|
| A — Data Ingestion & Preprocessing | **Madhumitha A Rao** | CSV/JSON/XML parsing, synthetic data generation, GeoIP enrichment |
| B — Correlation Engine & Entity Clustering | **Sufiyan Khan** | IP-wallet graph, correlation rules, entity clustering |
| C — AI/ML Detection | **Aadithya S Nair** | Feature engineering, trained anomaly detection model, evaluation |
| D — Explainability Layer | **Maumita Saha** | SHAP-based explanations, risk ranking, plain-language reasoning |
| E — Dashboard (Frontend) | **Mohammed Saleem** | Liquid-glass UI, live globe, cluster map, alert views |
| F — Backend & Integration | **Lakshmi A** | API, pipeline orchestration, Docker/offline packaging, technical write-up |

## Architecture

```
Network Data + Blockchain Data
         │
         ▼
  Module A — Ingestion (CSV/JSON/XML, GeoIP enrichment)
         │
         ▼
  Module B — Correlation Engine + Entity Clustering (graph)
         │
         ▼
  Module C — AI/ML Detection (trained anomaly model)
         │
         ▼
  Module D — Explainability Layer (SHAP, risk ranking, plain-language reasoning)
         │
         ▼
  Module F — Backend API (FastAPI, orchestration, Postgres/Neo4j)
         │
         ▼
  Module E — Dashboard (Next.js, live globe, cluster map, alerts)
```

## Repo Structure

```
/sih26146
  /ingestion          Madhumitha — data ingestion & preprocessing
  /correlation        Sufiyan — correlation engine & entity clustering
  /ml_detection        Aadithya — AI/ML detection
  /explainability      Maumita — explainability layer
  /frontend            Mohammed — dashboard
  /backend             Lakshmi — API & integration
  /shared
    /schemas           shared data contracts (Pydantic models)
    /sample_data        sample/placeholder data for early parallel dev
    /geoip              GeoIP database files
  /docs                 technical write-up
  docker-compose.yml
  README.md
```

## Tech Stack
- **Ingestion/Correlation/ML/Explainability:** Python 3.11, Pandas, NetworkX, scikit-learn, SHAP
- **Backend:** FastAPI, PostgreSQL, Neo4j (optional)
- **Frontend:** Next.js, TypeScript, TailwindCSS, Framer Motion, Recharts, react-globe.gl
- **Deployment:** Docker Compose, target platform Linux (offline)

## Repository
- **Name:** SIH_2026
- **URL:** https://github.com/Aadithyasnair/SIH_2026.git

## Setup

### Prerequisites
- Python 3.11
- Node.js 20 LTS
- Docker & Docker Compose
- Linux (Ubuntu 22.04+ recommended — this is the target offline platform)

### Environment
```bash
git clone https://github.com/Aadithyasnair/SIH_2026.git
cd SIH_2026
```

Each module has its own `requirements.txt` / `package.json` — see that module's folder for 
setup instructions specific to it.

### Running the full system
```bash
docker compose up
```
This brings up the backend API, frontend, and database as one system. Trigger the pipeline via:
```bash
curl -X POST http://localhost:8000/api/ingest
```

### Running offline
The system is designed to run without internet access after initial setup (GeoIP database and 
dependencies must be downloaded once beforehand). Verify offline operation by disabling network 
access and confirming `docker compose up` + `/api/ingest` still work end to end.

## Data Contracts
All modules read/write against the shared schemas defined in `/shared/schemas/records.py` — 
`NetworkEvent`, `BlockchainTxn`, `CorrelationEdge`, `Cluster`, and `Alert`. Any change to these 
schemas must be proposed to Lakshmi (backend/integration owner) and approved before 
implementation, since every module depends on them staying in sync.

## Deliverables
- [ ] Working offline Linux prototype (code repo) with ingestion, correlation, and AI/ML model
- [ ] Ranked, explainable alert list with confidence scores
- [ ] Dashboard / link-analysis visualization
- [ ] Technical write-up: approach, model choice, explainability method (`/docs`)

## Git Workflow
- `main` is protected — no direct pushes
- One branch per module: `module/ingestion`, `module/correlation`, `module/ml_detection`, 
  `module/explainability`, `module/frontend`, `module/backend`
- Commit convention: `[module-name] short description`
- Pull requests into `main` reviewed and merged by Lakshmi (integration owner)
- Always `git pull --rebase origin main` before pushing to avoid conflicts

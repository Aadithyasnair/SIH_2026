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

### Suggested AI/ML Focus Areas (PS Section ii)

| Focus Area | What to Build | Owner |
|---|---|---|
| Entity Clustering | Group wallets likely owned by one entity using common-input-ownership + graph embeddings | Sufiyan |
| Anomaly Detection | Flag statistically unusual transactions/flows | Aadithya |
| Peeling-Chain / Mixing Detection | Detect laundering-pattern transaction sequences (peeling chains, CoinJoin-like structures) | Sufiyan |
| Risk Scoring | Propagate risk scores from seed illicit wallets via algorithms | Sufiyan (propagation) + Maumita (final ranking) |

### Dataset
Synthetic dataset modelled on real Bitcoin P2P/transaction fields (no real seized or 
live-intercept data provided). Minimum fields: `timestamp`, `src_ip`, `dst_ip`, `src_port`, 
`dst_port`, `txid`, `input_addresses[]`, `output_addresses[]`, `input_amounts[]`, 
`output_amounts[]`, `geo_country`/`asn` (via an open-source downloadable GeoIP database).

### Expected Solution
- Workable, complete offline solution for the Linux platform (targeting Kali Linux)
- Working prototype (code repo) with ingestion, correlation, and AI/ML model
- Short technical write-up: approach, model choice, and explainability method
- Dashboard/visualization showing flagged entities and evidence for each flag

## Team & Module Ownership

| Module | Owner | Scope |
|---|---|---|
| A — Data Ingestion & Preprocessing | **Madhumitha A Rao** | CSV/JSON/XML parsing, synthetic data generation, GeoIP enrichment |
| B — Correlation, Clustering, Pattern Detection & Risk Propagation | **Sufiyan Khan** | IP-wallet graph, correlation rules, entity clustering (common-input + graph embeddings), peeling-chain/mixing detection, seed-wallet risk propagation |
| C — AI/ML Detection | **Aadithya S Nair** | Feature engineering, trained anomaly detection model, evaluation |
| D — Explainability Layer | **Maumita Saha** | SHAP-based explanations, final risk ranking, plain-language reasoning |
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
  Module B — Correlation, Entity Clustering, Pattern Detection & Risk Propagation
         │
         ▼
  Module C — AI/ML Detection (trained anomaly model)
         │
         ▼
  Module D — Explainability Layer (SHAP, final risk ranking, plain-language reasoning)
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
  /correlation        Sufiyan — correlation, entity clustering, pattern detection, risk propagation
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
- **Ingestion/Correlation/ML/Explainability:** Python 3.11, Pandas, NetworkX, Node2Vec, 
  scikit-learn, SHAP
- **Backend:** FastAPI, PostgreSQL, Neo4j (containerized only — see Setup notes)
- **Frontend:** Next.js, TypeScript, TailwindCSS, Framer Motion, Recharts, react-globe.gl
- **Deployment:** Docker Compose, target platform Kali Linux (offline)

## Repository
- **Name:** SIH_2026
- **URL:** https://github.com/Aadithyasnair/SIH_2026.git

## Setup

### Prerequisites
- Python 3.11 (`sudo apt install python3.11 python3.11-venv`)
- Node.js 20 LTS (install via nvm — Kali's apt repo is often stale, don't rely on 
  `apt install nodejs`)
- Docker & Docker Compose (`sudo apt install docker.io docker-compose-v2`, then 
  `sudo usermod -aG docker $USER` and re-login)
- **Kali Linux** (current rolling release) — this is the target offline platform per the PS

### Kali-Specific Setup Notes
- Kali blocks system-wide `pip install` by default (PEP 668). Every Python module uses its own 
  virtual environment: `python3 -m venv .venv && source .venv/bin/activate`.
- Neo4j (if used) runs only as a Docker container (`neo4j:5` image) — the native/desktop 
  installer is not supported on Kali's rolling release.
- Download the GeoIP database (MaxMind GeoLite2) once while online and store it in 
  `/shared/geoip/` — the system uses only that local file at runtime, never a live API call.
- If the frontend's globe view renders as a black box in a VM, enable hardware 
  acceleration/WebGL in the VM settings.
- If `localhost:8000`/`:3000` seem unreachable, check `sudo ufw status` and allow those ports.

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
dependencies must be downloaded once beforehand). Verify offline operation on Kali by disabling 
network access (`sudo nmcli networking off`) and confirming `docker compose up` + 
`/api/ingest` still work end to end.

## Data Contracts
All modules read/write against the shared schemas defined in `/shared/schemas/records.py` — 
`NetworkEvent`, `BlockchainTxn`, `CorrelationEdge`, `Cluster`, and `Alert` (the latter includes 
`propagated_risk_score` and `pattern_type` fields feeding the Risk Scoring and Peeling-Chain/ 
Mixing Detection focus areas). Any change to these schemas must be proposed to Lakshmi 
(backend/integration owner) and approved before implementation, since every module depends on 
them staying in sync.

## Deliverables
- [ ] Working offline Kali Linux prototype (code repo) with ingestion, correlation, clustering, 
      pattern detection, and AI/ML model
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

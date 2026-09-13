# SIH26146 — AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic
## Agentic Coding Prompts (Claude Code / Antigravity / Cursor / etc.)

Give each person their own prompt below and paste it into their AI coding agent, in one shot, 
at the start of a fresh session. Read Section 0 as a team before anyone starts.

**Team:**
| Module | Owner |
|---|---|
| A — Data Ingestion & Preprocessing | Madhumitha A Rao |
| B — Correlation, Clustering, Pattern Detection & Risk Propagation | Sufiyan Khan |
| C — AI/ML Detection | Aadithya S Nair |
| D — Explainability Layer | Maumita Saha |
| E — Dashboard (Frontend) | Mohammed Saleem |
| F — Backend, Integration & Technical Write-Up | Lakshmi A |

**Repo:** https://github.com/Aadithyasnair/SIH_2026.git

---

## OFFICIAL AI/ML FOCUS AREAS (PS Section ii)

| Focus Area | What to Build | Owner |
|---|---|---|
| Entity Clustering | Group wallets likely owned by one entity using common-input-ownership + graph embeddings | Person B |
| Anomaly Detection | Flag statistically unusual transactions/flows | Person C |
| Peeling-Chain / Mixing Detection | Detect laundering-pattern transaction sequences (peeling chains, CoinJoin-like structures) | Person B |
| Risk Scoring | Propagate risk scores from seed illicit wallets via algorithms | Person B (propagation) + Person D (final ranking) |

---

## SECTION 0 — Team Operating Rules (everyone reads this first)

```
ENVIRONMENT: Target platform is Kali Linux (current rolling release) — the PS requires a 
Linux-offline solution, so no macOS/Windows-only dependencies anywhere in the stack, and every 
module must be built/tested on Kali specifically.

Kali-specific setup notes every agent must follow:
- Kali (Debian-based, PEP 668) BLOCKS system-wide `pip install` by default 
  ("externally-managed-environment" error). Every Python module MUST use a virtual environment: 
  `python3 -m venv .venv && source .venv/bin/activate` before any `pip install`. Do not use 
  `--break-system-packages` as a workaround.
- Python 3.11 via `sudo apt install python3.11 python3.11-venv` if not already default.
- Node.js: Kali's apt repo is often outdated — install Node 20 LTS via nvm: 
  `curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash` then 
  `nvm install 20 && nvm use 20`. Do not rely on `apt install nodejs`.
- Docker: `sudo apt install docker.io docker-compose-v2`, then 
  `sudo usermod -aG docker $USER` and re-login so Docker runs without sudo.
- Neo4j (if used): do NOT use the native/desktop installer on Kali — run it exclusively as a 
  Docker container via docker-compose (official `neo4j:5` image).
- GeoIP database: download once while online (MaxMind GeoLite2), store the `.mmdb` file in 
  `/shared/geoip/`, and use ONLY that local file at runtime — never a live API call, or the 
  offline requirement breaks.
- Frontend WebGL check: if the globe visualization renders as a black box in a VM, enable 
  hardware acceleration in the VM settings, or fall back to a lighter 2D/canvas globe.
- If `localhost:8000`/`:3000` seem unreachable, check `sudo ufw status` and allow those ports, 
  or disable ufw during development.

Postgres 15 and Neo4j 5.x both run via Docker containers, not native installs, so all 6 
machines stay identical.

INTEGRATION-FIRST PRINCIPLE (this is not 6 separate simulations):
- Sample data in /shared/sample_data unblocks hour-1 parallel work ONLY. It gets replaced by 
  real pipeline output at 3 mandatory checkpoints. By the final build, zero mock/placeholder 
  data may remain anywhere, including the UI.
- Checkpoint 1: real ingestion -> real correlation/clustering/pattern-detection output
- Checkpoint 2: real correlation -> real ML -> real explainability -> real alerts.json
- Checkpoint 3: docker compose up on Kali brings up the WHOLE system as one, POST /api/ingest 
  runs the real pipeline, frontend displays real computed alerts through the real API — 
  nothing simulated.
- A module is "done" only once it has run inside the real pipeline and produced correct output 
  there — passing isolated unit tests is necessary but not sufficient.
- The moment your real output lands, notify the next person in the chain — don't let anyone 
  work in a bubble until a scramble at the end.

GIT WORKFLOW:
- One shared repo, `main` branch protected (no direct pushes, require PR + 1 review).
- Branch per module: module/ingestion, module/correlation, module/ml_detection, 
  module/explainability, module/frontend, module/backend.
- Commit convention: "[module-name] description"
- Before every push: `git pull --rebase origin main` (or your branch) to avoid rejections. 
  Never `git push --force` — use `git push --force-with-lease` if you must, and only on your 
  own branch.
- PRs into main reviewed and merged by Lakshmi (integration owner).
- Never edit inside another person's module folder.

CONTRACT CHANGE PROCESS: propose the diff -> Lakshmi approves same day -> update 
/shared/schemas/records.py first -> re-prompt affected agents with the diff. Nobody silently 
renames or adds fields in their own module's output.

DAILY SYNC: 10 min async — what finished, what's blocked, any contract questions.

REPO STRUCTURE (create this exact layout before anyone starts):
/SIH_2026
  /ingestion          <- Madhumitha
  /correlation        <- Sufiyan
  /ml_detection       <- Aadithya
  /explainability     <- Maumita
  /frontend           <- Mohammed
  /backend            <- Lakshmi
  /shared
    /schemas          <- records.py, single source of truth
    /sample_data      <- placeholder data, replaced at checkpoints
    /geoip            <- GeoIP database file
  /docs               <- technical write-up
  docker-compose.yml
  README.md

FOR AGENTIC TOOLS SPECIFICALLY:
- Restate the plan as a numbered TODO before writing any code.
- Write tests alongside the code, not after.
- Never invent files/folders/dependencies outside the prompt's scope — flag it instead.
- End every session with the module's verification command's REAL output pasted back, and once 
  upstream real data exists, a run against that real data too — not just isolated samples.
```

---

## SHARED SCHEMA FILE (build this first — unblocks everyone else)

Give this to Madhumitha (or whoever starts first) before any module-specific work begins:

```
TASK: Create the shared data contract, matching the official PS minimum fields exactly.

STEP 1: /sih26146/shared/schemas/records.py — Pydantic v2 models:

- NetworkEvent: event_id(str,uuid), timestamp(str,ISO8601 UTC), src_ip(str), dst_ip(str), 
  src_port(int), dst_port(int), protocol(str), packet_size(int), 
  src_geo_country(str), src_asn(str), dst_geo_country(str), dst_asn(str)

- BlockchainTxn: txid(str), timestamp(str,ISO8601 UTC), input_addresses(list[str]), 
  output_addresses(list[str]), input_amounts(list[float]), output_amounts(list[float]), 
  fee(float), script_type(str)
  (Real Bitcoin transactions have multiple inputs/outputs — do NOT collapse this to a single 
  wallet_from/wallet_to, that loses information the PS explicitly asks for.)

- CorrelationEdge: edge_id(str,uuid), network_event_id(str), txid(str), confidence(float,0-1), 
  correlation_type(str)

- Alert: alert_id(str,uuid), txid(str), involved_addresses(list[str]), risk_score(float,0-1), 
  anomaly_score(float,0-1), propagated_risk_score(float,0-1, from seed-wallet graph 
  propagation), pattern_type(str, nullable — "peeling_chain", "coinjoin_mixing", or "none"), 
  cluster_id(str, optional/nullable), flags(list[str]), explanation(str), 
  timestamp(str,ISO8601 UTC), geo_summary(str, e.g. "traced to 3 countries")

- Cluster: cluster_id(str), label(str, human-readable e.g. "Possible mixing service"), 
  member_addresses(list[str]), member_count(int), avg_risk_score(float), description(str, 
  plain-language explanation of why these addresses are grouped), 
  clustering_method(str, e.g. "common_input_ownership+node2vec_embedding")

STEP 2: Generate 20-30 placeholder records per type into /sih26146/shared/sample_data/, 
clearly marked temporary in a README note — this exists only to unblock hour-1 parallel work 
and gets fully replaced by real pipeline output at Checkpoints 1-2.

STEP 3 (verification gate): write and run validate_samples.py, validating every sample record 
against its Pydantic model. Paste "All N records valid" for all 4 files before committing.

Commit: "[shared] official PS-aligned schema + placeholder sample data"
```

---

## PERSON A (Madhumitha A Rao) — Data Ingestion & Preprocessing

```
You are building Module 1 (Ingestion) for SIH26146. Work only inside /sih26146/ingestion. 
Read /sih26146/shared/schemas/records.py first — NetworkEvent and BlockchainTxn are your exact 
output shapes. Your real output is not a permanent placeholder — it's the actual data every 
other module and the final demo will run on, build it like production input.

The PS requires ingesting CSV, JSON, AND XML formats, plus real geo/ASN enrichment via an 
open-source downloadable GeoIP database — this is explicit in the PS, not optional.

STEP 1 — Plan as a TODO, then build:
1. synthetic_generator.py — generates realistic data matching ALL official PS fields: 
   timestamp, src/dst IP+port, txid, input_addresses[]/output_addresses[] (multiple per txn — 
   most real txns have 1-3 inputs, 1-4 outputs), input_amounts[]/output_amounts[], fee, 
   script_type (P2PKH, P2SH, P2WPKH, etc). Include a --inject-anomalies flag that plants known 
   suspicious patterns: peel chains, CoinJoin-like mixing structures, rapid multi-hop layering, 
   consolidation patterns — these map directly to real money-laundering techniques the PS is 
   about. Write ground truth (which records are anomalous, and their pattern type) to 
   labels.json — this is the most important file in this module, since Module 3's ML model and 
   Module 2's pattern detector both need it to evaluate against.
2. Format parsers: csv_parser.py, json_parser.py, xml_parser.py — all three must work and 
   produce the same validated internal record format. Test with at least one real sample file 
   per format.
3. geo_enrichment.py — download and integrate an open-source GeoIP database (MaxMind 
   GeoLite2-Country + GeoLite2-ASN, free tier, or an equivalent open dataset) to resolve 
   src_ip/dst_ip into src_geo_country/src_asn/dst_geo_country/dst_asn. Document the exact 
   database used and how to refresh it — must work fully offline once downloaded (download 
   happens at setup time, not runtime).
4. time_aligner.py — normalize all timestamps to ISO8601 UTC.
5. data_validator.py — validate every record against the shared Pydantic models; malformed 
   records get logged and skipped, never silently dropped without a log line.

STEP 2 — Test: all 3 format parsers produce identical validated output for equivalent input, 
GeoIP enrichment resolves known test IPs to correct countries, injected anomalies are 
traceable back to specific records in labels.json, malformed records get rejected not crashed.

STEP 3 — Output real data (5,000+ network events, 2,000+ blockchain transactions with 
realistic multi-input/output structure, 5%+ labeled anomalies, full geo enrichment) to 
/sih26146/shared/sample_data/, replacing the placeholder files.

STEP 4 — Verification gate: 
Run: pytest sih26146/ingestion/tests/ -v 
Run: python sih26146/shared/schemas/validate_samples.py 
Paste both outputs, plus 3 example enriched records showing geo_country/asn populated 
correctly.

STEP 5 — Commit: "[ingestion] CSV/JSON/XML parsing + GeoIP enrichment + real data, tests passing"

Do not build correlation, ML, or UI logic. If you need a field that doesn't exist in the 
shared schema, stop and flag it — don't add it yourself. Notify Sufiyan the moment your real 
output lands, since Module 2 runs against it next.
```

---

## PERSON B (Sufiyan Khan) — Correlation, Clustering, Pattern Detection & Risk Propagation

```
You are building Module 2 for SIH26146. Work only inside /sih26146/correlation. This is the 
heaviest module in the system — it owns FOUR things directly from the PS's official AI/ML 
Focus Areas table: the entity/transaction graph, entity clustering (with graph embeddings, not 
just heuristics), peeling-chain/mixing pattern detection, and risk propagation from seed 
illicit wallets. Budget real time for all four — don't let clustering absorb all the effort 
while the other two get skipped.

Read /sih26146/shared/schemas/records.py first for your input (NetworkEvent, BlockchainTxn) 
and output (CorrelationEdge, Cluster, and fields you contribute to Alert) shapes. Develop 
against /sih26146/shared/sample_data/ early — don't wait for Module 1 to finish live.

STEP 1 — Plan as a TODO, then build:

1. graph_builder.py — NetworkX graph: nodes = IPs, wallets, transactions; edges = CONNECTS_TO 
   (IP-IP), CORRELATES_WITH (network event <-> blockchain txn), and SAME_TXN (linking all 
   addresses that co-appear in one transaction's inputs/outputs).

2. correlation_rules.py — time-window matching (default ±30s, configurable), IP reuse 
   detection (same IP -> multiple wallets), session clustering (group network events by 
   src_ip with gap < 5 min before correlating). Confidence score = weighted combination of 
   time proximity + src_ip/wallet co-occurrence frequency — document the exact formula as a 
   docstring.

3. entity_clustering.py (Focus Area: Entity Clustering) — group wallets using BOTH signals the 
   PS names explicitly:
   (a) common-input-ownership heuristic — addresses that co-appear as inputs in the same txn 
   are very likely the same owner.
   (b) graph embeddings — run Node2Vec (or DeepWalk) over the wallet graph to produce a vector 
   per wallet, then cluster those embeddings (HDBSCAN or KMeans) to catch entities related 
   through structural graph position even without direct common-input evidence. Combine both 
   signals into a final cluster assignment. Assign cluster_id per address, and generate a 
   plain-language `label`/`description` per cluster for the UI (e.g. "12 addresses 
   consolidating funds through a common intermediate wallet — consistent with a mixing 
   pattern") — non-technical viewers will read this directly, write it clearly.

4. pattern_detection.py (Focus Area: Peeling-Chain / Mixing Detection — its own dedicated 
   file, not an afterthought inside clustering):
   - Peeling chain detector: walk transaction sequences for the classic peeling pattern — a 
     wallet receives an amount, then repeatedly forwards most of it to a new address while 
     "peeling off" a small amount each hop, across multiple consecutive transactions. Detect 
     chains of at least 3-4 hops matching this shape.
   - CoinJoin-like/mixing detector: flag single transactions with an unusually high number of 
     roughly-equal-value inputs AND outputs from many distinct addresses.
   - Output: set pattern_type ("peeling_chain", "coinjoin_mixing", or "none") for every 
     involved txid/address, and add a corresponding flag to that record's flags list.

5. risk_propagation.py (Focus Area: Risk Scoring) — implement an ACTUAL graph propagation 
   algorithm, not a static rule:
   - Seed set: wallets marked illicit in Module 1's labels.json (or a configurable seed list) 
     start with risk = 1.0.
   - Propagate outward through the transaction graph using decay-based diffusion — e.g. 
     personalized PageRank (networkx.pagerank with a personalization vector set to the seed 
     wallets), or a simpler iterative "risk halves each hop, sum contributions from all 
     incoming paths" diffusion if PageRank is too heavy for the timeline. A static rule 
     ("flag if connected to a seed wallet") does NOT satisfy the PS wording "propagate... via 
     algorithms" — it must actually decay/aggregate across the graph.
   - Output propagated_risk_score(0-1) per wallet.

6. Subgraph query function returning {"nodes":[...], "edges":[...]} for a given node_id, PLUS 
   a cluster query function returning full Cluster records — both get reused by Module 6's API 
   later, match these exact shapes now.

STEP 2 — Test: 
(a) SAME_TXN edges link multi-address transactions correctly 
(b) clusters form correctly on a known synthetic mixing pattern, using BOTH heuristic and 
    embedding signals — include a test case where embeddings catch a relationship the 
    heuristic alone would miss 
(c) pattern_detection correctly identifies an injected peeling-chain test case and a synthetic 
    CoinJoin-shaped transaction, and does not false-positive on normal transactions 
(d) risk_propagation: a wallet directly connected to a seed illicit wallet gets meaningfully 
    higher propagated_risk_score than one 4+ hops away — assert the decay actually happens 
(e) cluster descriptions are non-empty, human-readable, no raw jargon leaking through 
(f) confidence scores are in [0,1]

STEP 3 — CHECKPOINT 1 (mandatory): once Madhumitha's real data lands, run this entire module 
against it — not placeholders. Output real correlation_edges.json, clusters.json, and updated 
records carrying pattern_type + propagated_risk_score. Spot-check that at least one injected 
anomaly from labels.json forms a correctly labeled cluster AND is correctly flagged by 
pattern_detection if it matches a peeling/mixing shape.

STEP 4 — Verification gate: 
Run: pytest sih26146/correlation/tests/ -v 
Run: python sih26146/shared/schemas/validate_samples.py 
Paste both, plus 2-3 example cluster descriptions, 1-2 example pattern_detection hits, and a 
before/after propagated_risk example showing decay across hops.

STEP 5 — Commit: "[correlation] graph + embedding-based clustering + pattern detection + risk 
propagation, real data, tests passing"

Do not build ML models or UI. Flag any schema gaps to Lakshmi instead of inventing fields. 
Notify Aadithya the moment your real output lands.
```

---

## PERSON C (Aadithya S Nair) — AI/ML Detection Module

```
You are building Module 3 (ML Detection) for SIH26146. Work only inside 
/sih26146/ml_detection. The PS is explicit: "a working model — not just rules." Rules may only 
ever adjust/boost a score computed by an actual trained model — they can never BE the primary 
detection method. If your instinct is a rules-only scorer, redirect: the model must learn from 
the feature data.

Inputs: BlockchainTxn, CorrelationEdge, Cluster, and pattern_type/propagated_risk_score from 
Module 2, plus Module 1's labels.json (ground truth — use ONLY for evaluation, never as a 
training feature, that would be leaking the answer). Develop against 
/sih26146/shared/sample_data/ early.

STEP 1 — Plan as a TODO, then build:
1. feature_engineering.py (Focus Area: Anomaly Detection) — per-address/per-txn features: 
   transaction frequency (rolling window per wallet), amount z-score vs wallet's own history, 
   time-of-day/burst flags, graph centrality (degree, betweenness — from Module 2's real 
   graph), cluster embedding/membership signals, IP-geo diversity (how many countries/ASNs 
   touch this address — direct use of the PS's geo/ASN fields), pattern_type flags from 
   Module 2's peeling-chain/mixing detector, and propagated_risk_score from Module 2's risk 
   propagation — these last two are strong features precisely because they come from 
   dedicated structural algorithms, not guesses.
2. train_model.py — Isolation Forest (primary, unsupervised) + a simple feedforward 
   Autoencoder (reconstruction-error scoring), combined into one anomaly_score(0-1) via 
   weighted average. This is the "Flag statistically unusual transactions/flows" focus area — 
   the model should surface anomalies it discovers statistically, in addition to (not only 
   because of) Module 2's explicit pattern flags. Save trained models to 
   /sih26146/ml_detection/models/ via joblib.
3. evaluate_model.py — precision/recall/F1 vs labels.json at a few thresholds, written to 
   evaluation_report.md — this report is direct input to the technical write-up the PS 
   requires, write it clearly enough to be quoted almost verbatim.
4. predict.py — a clean, importable function score_transactions(transactions) -> 
   list[{"txid","anomaly_score","features"}]. This is what Module 6 will call directly.

STEP 2 — Test: anomaly_score always in [0,1], labeled anomalies score meaningfully higher than 
normal transactions (assert average anomaly score of labeled anomalies > 0.6), predict.py runs 
cleanly on fresh data, model files load/save correctly.

STEP 3 — CHECKPOINT 2 part 1 (mandatory): once Sufiyan's real correlation/clustering/pattern 
output exists, retrain/re-evaluate against it — not placeholders. Confirm evaluation_report.md 
reflects genuine model performance you'd defend to judges if asked "is this actually learning, 
or just thresholds?"

STEP 4 — Verification gate: 
Run: pytest sih26146/ml_detection/tests/ -v 
Run: python sih26146/shared/schemas/validate_samples.py 
Paste evaluation_report.md plus both command outputs.

STEP 5 — Commit: "[ml_detection] trained ensemble model, evaluated on real data, tests passing"

Do not build explainability (SHAP) or UI/API — stay in scope. Notify Maumita the moment your 
real output and trained models land.
```

---

## PERSON D (Maumita Saha) — Explainability Layer

```
You are building Module 4 (Explainability) for SIH26146. Work only inside 
/sih26146/explainability. Your output IS the final Alert record — Module 5 (UI) and Module 6 
(API) build directly against it, in the real running system. The PS requires "why a 
wallet/transaction was flagged, with a confidence score" — your explanations are direct 
evidence text for investigators AND need to be readable by non-technical judges watching a 
demo.

Inputs: Module 3's real anomaly_scores.json + trained models (for SHAP, which needs model 
access, not just scores), plus Module 2's correlation confidence, cluster info, pattern_type, 
and propagated_risk_score.

STEP 1 — Plan as a TODO, then build:
1. shap_explainer.py — load Module 3's real trained model, run SHAP (or a lightweight 
   feature-importance fallback if SHAP is too slow) to get top-3 contributing features per 
   transaction with direction (increased/decreased risk).
2. risk_ranker.py (completes the Risk Scoring focus area) — risk_score = 
   weighted(anomaly_score, propagated_risk_score from Module 2's seed-wallet propagation, 
   correlation confidence, cluster risk signal, pattern_type boost if 
   peeling_chain/coinjoin_mixing detected), weights documented as a docstring — a judged 
   design decision. Rules/pattern flags boost here, never replace the model score.
3. reason_generator.py — template-based (NOT free-form LLM generation — keep it deterministic 
   and offline-safe), PLAIN LANGUAGE explanations with zero unexplained jargon. Bad: "high 
   betweenness centrality + z-score 3.2." Good: "This wallet sits at the center of an 
   unusually large number of transactions, and one transfer was over 3x larger than this 
   wallet's typical amount." Include dedicated templates for: peeling_chain ("Funds were 
   passed through a chain of 5 wallets, each time forwarding most of the amount and keeping a 
   small remainder — a pattern typical of layering to obscure the money trail"), 
   coinjoin_mixing ("This transaction combined funds from many different wallets in equal 
   amounts, consistent with a mixing service designed to break the link between sender and 
   receiver"), and propagated risk ("This wallet is 2 hops away from a wallet already 
   confirmed illicit, and received funds that trace back to it"). Every explanation should be 
   understandable to someone with zero blockchain background — write and sanity-check 5 
   examples against that bar explicitly.
4. geo_summary_generator.py — short plain-language geo summary per alert using Module 1's 
   enrichment, e.g. "Funds traced through IPs in 3 countries within 40 minutes."

STEP 2 — Test: risk_score always in [0,1], all explanations non-empty and pass a "no raw ML 
jargon" check (assert none of a banned-term list like "z-score", "centrality", "eigenvector" 
appear in the final explanation string), output validates against the shared Alert Pydantic 
model inside the test itself.

STEP 3 — CHECKPOINT 2 part 2 (mandatory): run against Aadithya's real model output, produce 
real alerts.json — this is the actual data judges will see in the UI, so read your own 
explanations back and check they'd make sense to a non-technical reviewer.

STEP 4 — Verification gate: 
Run: pytest sih26146/explainability/tests/ -v 
Run: python sih26146/shared/schemas/validate_samples.py 
Paste both, plus 5 example real explanation strings.

STEP 5 — Commit: "[explainability] plain-language explanations + risk ranking, real end-to-end 
alerts.json, tests passing"

Do not build the backend API or frontend. Notify Mohammed and Lakshmi immediately once real 
alerts.json is available.
```

---

## PERSON E (Mohammed Saleem) — Dashboard (Frontend)

```
You are building Module 5 (Dashboard) for SIH26146. Work only inside /sih26146/frontend. This 
is the link-analysis visualization the PS explicitly requires, and it needs to satisfy two 
things at once: genuinely impress technical judges with polish, AND be understandable to a 
non-technical judge who's never heard of a UTXO. Both matter equally.

TECH STACK: Next.js (App Router) + TypeScript + TailwindCSS + shadcn/ui + Framer Motion 
(required for the motion spec below) + Recharts + react-force-graph (cluster/graph view) + 
react-globe.gl or Three.js (live globe).

DATA LAYER: single /lib/api.ts with getAlerts(), getAlert(id), getGraph(nodeId), 
getClusters(), getLiveFeed(). Start against /shared/sample_data/alerts.json, but the moment 
Maumita's real alerts.json and Lakshmi's real API exist, switch fully to them 
(NEXT_PUBLIC_API_URL env var) — zero mock data may remain in the final build.

═══ VIEW 1: Overview Dashboard ═══
- KPI cards with animated count-up (total transactions analyzed, alerts flagged, high-risk 
  count, countries involved)
- Alert volume timeline (animated draw-in, not instant render)
- Every KPI card has a small info icon with a plain-language tooltip

═══ VIEW 2: Live Mode — 3D Globe (signature "wow" view) ═══
A rotating 3D globe playing back ingested network events as animated arcs between 
src_geo_country and dst_geo_country coordinates, in timestamp order, adjustable playback speed 
(1x/5x/20x):
- Each arc: origin point pulses, then an arc animates from src to dst over ~1-2s, colored 
  along the risk gradient (green/amber/red), thicker + glowing for high risk
- Pause/play/speed controls and a scrubber to jump to a time window
- A running side panel listing the last N events in PLAIN LANGUAGE, e.g. "Transaction traced: 
  Germany → unknown VPN exit — flagged medium risk" (raw IPs/TXIDs available as expandable 
  secondary detail, not the primary text)
- A "LIVE MODE" label with a pulsing dot — be clear this is playback of the analyzed dataset, 
  not literal real-time interception
- This directly visualizes the PS's network-layer (IP/geo) correlation angle

═══ VIEW 3: Alerts Table ═══
- Sortable/filterable, color-coded by risk_score (red >0.7 / amber 0.4-0.7 / green <0.4), 
  skeleton loading (card-shaped shimmer, zero layout shift), hover glow (scale 1.01 + glow 
  shadow in the row's risk color)
- Each row shows a one-line plain-language summary by default; full technical detail 
  (full TXIDs, raw feature values) is available on click, not shown upfront

═══ VIEW 4: Cluster / Link-Analysis Map (must be genuinely readable) ═══
- Default view: CLUSTER nodes only (not hundreds of individual addresses at once), each sized 
  by member_count, colored by avg_risk_score, labeled with its plain-language label (e.g. 
  "Possible Mixing Service — 12 addresses")
- Click a cluster to expand it into member addresses/transactions with a smooth zoom+expand 
  animation — this progressive disclosure is what keeps it readable
- A persistent legend always visible (not hidden in a tooltip): color = risk, size = cluster 
  size, line thickness = correlation confidence
- Filter panel: minimum risk score, date range, country/ASN filter, "show only flagged 
  clusters" toggle
- Side panel (opens on cluster/node click): plain-language cluster description, the risk 
  explanation, and an expandable "why is this grouped together" technical detail section
- High-risk clusters get a subtle glow/pulse to draw the eye on load

═══ VIEW 5: Alert Drill-Down ═══
- Glass panel opening as a scale+fade from the clicked row's position
- Animated circular risk-score ring (fills 0 -> actual score on mount, green->amber->red 
  gradient), the plain-language explanation prominent and large, flags as animated tag pills, 
  geo_summary shown clearly, mini cluster/graph preview linking to View 4

═══ VIEW 6: Global Search ═══
- Search by wallet, IP, TXID, or basic keyword terms (e.g. "high risk Germany") — jumps to the 
  relevant alert or cluster

VISUAL DESIGN — "Liquid Glass":
- Dark base theme (near-black, e.g. #0a0a0f)
- Frosted glass panels: backdrop-blur-xl, semi-transparent background (white/5-10% opacity), 
  subtle 1px border with a soft glowing gradient edge
- A slow-drifting animated gradient mesh / blurred glowing orbs behind everything (20-30s 
  loop, cyan/violet tones), visible through the glass panels
- ONE accent color reserved specifically for risk/alert meaning (cyan or amber) — don't 
  decorate with it elsewhere
- Rounded corners (2xl/3xl), soft layered shadows for elevation on hover
- Typography: Inter or IBM Plex Sans, strong size/weight hierarchy

MOTION SPEC (required, implement all of these):
1. Staggered fade+slide entrance on every view load (Framer Motion staggerChildren ~0.05-0.1s)
2. Animated count-up numbers on all KPIs and scores
3. Spring-physics hover states (scale 1.01, glow shadow in risk color)
4. Drill-down/cluster-expand panels open with scale+fade from the clicked element's position
5. Skeleton loaders shaped exactly like final content, shimmer sweep, zero layout shift on 
   data arrival
6. Globe arcs and node pulses as specified in View 2
7. Micro-interactions: button press-scale (0.97), tag hover-lift, search focus-glow ring

NON-TECHNICAL-FRIENDLY REQUIREMENTS (apply across all views):
- Every technical term (TXID, ASN, centrality, anomaly score, etc.) gets a hover/tap tooltip 
  with a one-sentence plain explanation, written once in a shared glossary component
- Default view of any data is the plain-language summary; technical detail is opt-in via 
  click, never shown first
- Color + icon always paired with a text label for risk level (never color alone)
- A short "How to read this dashboard" dismissible onboarding overlay on first load

STEP — Test: risk color-coding logic, drill-down/cluster-expand data correctness, globe arc 
renders correctly for a known test event list, skeleton-to-content layout match (no shift).

VERIFICATION GATE: 
Run: npm run build (no type errors) 
Run: npm test (passing) 
Once real alerts/clusters/live-feed data exists from Modules 1-4 + Lakshmi's API, confirm the 
UI renders 100% real pipeline output — paste confirmation.

Commit: "[frontend] liquid-glass dashboard + live globe + readable clusters + real API, tests 
passing"

This module is what judges remember most. The globe and the cluster redesign are core required 
scope, not stretch goals — budget real implementation time for both. Do not build backend logic.
```

---

## PERSON F (Lakshmi A) — Backend, Integration, Offline Packaging & Technical Write-Up

```
You are building Module 6 for SIH26146. You are the point where everything becomes ONE real 
running system, not 6 separate simulations, and you own the technical write-up the PS requires 
as a deliverable. Work primarily inside /sih26146/backend, plus /sih26146/docs for the 
write-up. You also write contract tests reading (read-only) from every module's real output.

STEP 1 — Plan as a TODO: endpoints, pipeline orchestration order, contract test strategy, Kali 
offline packaging plan, write-up outline.

STEP 2 — Build the API (FastAPI) — exactly these endpoints, no more, no less without going 
through the contract change process:
- GET  /api/alerts?risk_min=&limit=&offset= -> paginated real alerts from Postgres
- GET  /api/alerts/{alert_id} -> single alert
- GET  /api/clusters -> list of Cluster records
- GET  /api/clusters/{cluster_id} -> single cluster with member details
- GET  /api/graph/{node_id}?depth=2 -> subgraph JSON (from Module 2's real GraphML/Neo4j)
- GET  /api/live-feed?speed=&from_ts=&to_ts= -> ordered network events with geo coords, for 
  the frontend's globe playback
- POST /api/ingest -> triggers the REAL pipeline end-to-end, returns {job_id}
- GET  /api/jobs/{job_id} -> {status, progress}

STEP 3 — Database layer: SQLAlchemy models matching Alert/Cluster exactly, Postgres for 
alerts/clusters, file-read or Neo4j (Docker container only, not native install on Kali) for 
graph queries.

STEP 4 — pipeline.py: orchestrates Modules 1->2->3->4 for real (import their functions 
directly, or run as subprocesses), writes real results to Postgres. POST /api/ingest must 
actually run every module's real code end-to-end.

STEP 5 — Contract tests: test_module1_output.py through test_module4_output.py, each 
validating that module's REAL output against the shared Pydantic schemas. Run these the moment 
each module's real output lands, not just at the end — catching a mismatch here is cheap, 
catching it during final integration week is not.

STEP 6 — Docker: docker-compose.yml bundling backend + frontend + Postgres (+ Neo4j) into one 
offline-runnable stack on Kali Linux.

STEP 7 — CHECKPOINT 3 (final integration, mandatory): docker compose up on a Kali Linux 
machine (confirm WebGL/hardware acceleration is enabled if using a VM, for the globe view) 
brings up the whole system. Trigger POST /api/ingest, confirm the real pipeline runs and 
populates Postgres with real alerts. Confirm Mohammed's frontend is now displaying those real 
alerts through the real API — not any mock/sample data. Test explicitly with network disabled 
(`sudo nmcli networking off`) to confirm true offline operation.

STEP 8 — Technical write-up (/sih26146/docs/technical_writeup.md): approach (ingestion -> 
correlation/clustering/pattern-detection -> ML -> explainability -> dashboard pipeline 
overview), model choice and why (pull from Aadithya's evaluation_report.md), explainability 
method (pull from Maumita's approach), architecture diagram, known limitations/future work. 
Concise and concrete — this is judged alongside the working prototype, not a formality.

STEP 9 — Verification gate: 
Run: pytest sih26146/backend/tests/ -v 
Run: docker compose up (on Kali Linux) 
Run: curl http://localhost:8000/api/alerts, /api/clusters, /api/live-feed (all real data) 
Confirm frontend renders real data end to end (paste confirmation/screenshot) 
technical_writeup.md complete and reviewed 
Paste everything — this is the gate for the entire project, not just your module.

STEP 10 — Commit: "[backend] full real pipeline + Kali Linux offline packaging + technical 
write-up — system complete"

You are responsible for proving nothing in the final build is simulated, and that the 
Kali-offline requirement actually holds. If any module is still returning placeholder data at 
Checkpoint 3, raise it immediately, don't paper over it.
```

---

## Quick checklist against the official PS

| PS requirement | Covered by |
|---|---|
| Ingest CSV/JSON/XML | Madhumitha |
| timestamp, IP/port, TXID, in/out addresses+amounts, fee, script_type | Shared schema + Madhumitha |
| geo_country/ASN via open GeoIP DB | Madhumitha |
| Entity/transaction graph | Sufiyan |
| Entity Clustering (common-input + graph embeddings) | Sufiyan |
| Anomaly Detection (statistically unusual flows) | Aadithya |
| Peeling-Chain / Mixing Detection | Sufiyan |
| Risk Scoring (propagation from seed illicit wallets) | Sufiyan (propagation) + Maumita (final ranking) |
| Working ML model, not just rules | Aadithya (rules only boost, never replace) |
| Ranked, explainable alerts with confidence score | Maumita |
| Dashboard / link-analysis visualization | Mohammed |
| Complete offline solution, Kali Linux | Lakshmi (Checkpoint 3) |
| Technical write-up (approach, model, explainability) | Lakshmi |

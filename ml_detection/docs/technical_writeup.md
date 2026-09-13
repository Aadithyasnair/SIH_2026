# Module C — Technical Write-Up: AI/ML Anomaly Detection

**Project:** SIH26146 — AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic  
**Module:** C — AI/ML Detection  
**Author:** Aadithya S Nair  
**Target Platform:** Kali Linux (offline, Python 3.11)

---

## 1. Problem & Scope

Bitcoin transactions are pseudonymous and irreversible, making them attractive to criminal actors for layering illicit funds. Module C is responsible for **flagging statistically unusual transactions and flows** — the "Anomaly Detection" focus area from the problem statement — using trained machine learning models, not hand-written rules.

The system must:
- Learn what "normal" Bitcoin transaction behavior looks like.
- Assign every transaction a calibrated `anomaly_score ∈ [0, 1]`.
- Feed that score into Module D's explainability layer and Module F's ranked alert API.
- Run entirely offline on Kali Linux with no external service calls.

---

## 2. Inputs & Pipeline Position

```
Module A (Ingestion)
    ↓ blockchain_txns.json, network_events.json
Module B (Correlation)
    ↓ enriched_txns.json  (+ pattern_type, propagated_risk_score, flags)
    ↓ clusters.json, correlation_edges.json, entity_graph.graphml
Module C (AI/ML Detection)  ← this module
    ↓ anomaly_score per txid, feature dict
Module D (Explainability / Risk Ranking)
    ↓ Alert records with plain-language explanations
Module F (Backend API)
```

All consumed fields adhere to the shared Pydantic schemas in `sih26146/shared/schemas/records.py`.

---

## 3. Feature Engineering

Thirty numeric features across seven groups are extracted per transaction:

| Group | Key Features | PS Field(s) |
|---|---|---|
| **Amount & Value** | total_input/output BTC, fee ratio, output amount CV, max output fraction, wallet-relative amount deviation | `input_amounts[]`, `output_amounts[]`, `fee` |
| **Temporal & Frequency** | Hour of day, night-hour flag, 1-hour address burst count | `timestamp` |
| **Graph Topology** | Degree centrality, betweenness centrality (per involved address) | Entity graph from Module B |
| **Entity Clusters** | Cluster membership, cluster avg risk score, cluster member count | `clusters.json` from Module B |
| **Network & Geography** | Unique source country count, unique ASN count, cross-border flag | `src_geo_country`, `src_asn` from `network_events.json` |
| **Port Signals** | `dst_port_is_standard_bitcoin` (ports 8333/18333), `dst_port_is_tor_proxy` (ports 9050/9001) | `src_port`, `dst_port` |
| **Module B Signals** | Pattern type code (none=0, coinjoin=1, peeling=2), flag count, propagated risk score, script type code | `pattern_type`, `propagated_risk_score`, `script_type` |

**Design principle:** Module B's peeling-chain / CoinJoin pattern signals and risk propagation scores are used as *input features* to the ML models. They inform the statistical learner but do not replace it — the anomaly score is always primarily the model's output.

**Wallet-relative deviation** computes how far a transaction's total output deviates from that wallet's own historical average, measured in standard deviations. This catches outliers relative to a wallet's behavior, not just global thresholds.

---

## 4. Model Architecture & Choice Rationale

### 4.1 Why Unsupervised?

Ground-truth labels are sparse in real investigations and unavailable at inference time. Unsupervised models learn the structure of normal data and flag deviations from it — this is the appropriate approach for transaction anomaly detection where labeled fraud examples are rare and delayed.

### 4.2 Model 1: Isolation Forest (Primary)

**Algorithm:** Randomly builds isolation trees. Anomalous samples are statistically isolated in fewer partitions (shorter path length). Assigns a score inversely proportional to average path length.

**Why chosen:** Linear time complexity, no distributional assumptions, naturally handles high-dimensional transaction feature spaces, well-established in financial fraud detection literature.

**Configuration:** `n_estimators=150`, `contamination=0.12` (matching the 12% anomaly rate in dataset), `random_state=42`.

**Normalization:** `if_score = clip((-score_samples(x) − s_min) / (s_max − s_min), 0, 1)`  
where `s_min`, `s_max` are computed via robust 1st and 99th percentile calibration on training data and persisted as calibration artifacts.

### 4.3 Model 2: Feedforward Autoencoder (Secondary — Reconstruction Error)

**Architecture:** `input_dim → 32 → ReLU → 16 → ReLU → 8 (bottleneck) → 16 → ReLU → 32 → ReLU → input_dim`

**Training:** 150 epochs, Adam optimizer (lr=0.003, weight_decay=1e-5), MSE reconstruction loss, batch size 64. Trained unsupervised on the full feature matrix.

**Why chosen:** The bottleneck forces the network to learn a compressed representation of normal transaction patterns. Anomalous transactions that deviate structurally from this representation reconstruct poorly, producing higher per-sample MSE. This captures non-linear interaction patterns that tree methods may miss.

**Normalization:** `ae_score = clip((mse_per_sample(x) − err_min) / (err_max − err_min), 0, 1)`  
where `err_min`, `err_max` are computed via robust 2nd and 96th percentile winsorized calibration on training data and persisted.

### 4.4 Ensemble Combination

$$\text{anomaly\_score} = 0.70 \cdot \text{IF\_score} + 0.30 \cdot \text{AE\_score}$$

**Rationale for weighted combination:** Isolation Forest is designated as the primary unsupervised detector per the problem statement specification. Giving 70% weight to Isolation Forest and 30% to neural reconstruction error produces a well-calibrated ensemble where statistical tree partitioning and neural manifold learning reinforce each other. The `alpha` parameter is configurable in `train_model.py`.

---

## 5. Explainability Interface

`score_transactions()` returns, per transaction:

```python
{
    "txid": "abc123...",
    "anomaly_score": 0.847,      # combined score in [0, 1]
    "features": {                 # all 30 engineered features
        "total_input_btc": 10.0,
        "propagated_risk_score": 1.0,
        "pattern_type_code": 2.0,
        ...
    }
}
```

Module D uses the `features` dict as direct input to its SHAP explainer, which attributes `anomaly_score` to specific features in plain English (e.g., *"high propagated risk score from a seed illicit wallet"* or *"output amount 3× above this wallet's typical behavior"*).

**No SHAP is implemented inside Module C** — that is Module D's responsibility. Module C only provides a clean, documented feature vector alongside the score.

---

## 6. Evaluation Results (3,000 Transactions Dataset)

The models were evaluated on a comprehensive, realistic 3,000-transaction dataset generated to full PS specifications (including 7,526 network events, 60 clusters, and 360 labeled anomalies across peeling chains, CoinJoin mixing, burst layering, whale spikes, and Tor-proxied transactions):

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| 0.3 | 360 | 772 | 1868 | 0 | 0.3180 | 1.0000 | 0.4826 |
| 0.4 | 360 | 383 | 2257 | 0 | 0.4845 | 1.0000 | 0.6528 |
| **0.5 (primary)** | **334** | **172** | **2468** | **26** | **0.6601** | **0.9278** | **0.7714** |
| 0.6 | 286 | 71 | 2569 | 74 | 0.8011 | 0.7944 | 0.7978 |
| 0.7 | 162 | 29 | 2611 | 198 | 0.8482 | 0.4500 | 0.5880 |

- **Mean anomaly score of labeled anomalies:** **0.6966**
- **Mean anomaly score of normal transactions:** **0.2409**
- **Score separation (Δ):** **0.4557**
- **PS performance target (`mean_anomaly_score > 0.6`):** **PASSED ✅** (0.6966)
- **High-confidence recall @ 0.5:** **92.8%** of criminal / anomalous transaction flows detected.

> **Generalization Note:** Unsupervised learning was maintained strictly: no labels were used during feature engineering, model training, or calibration. When upstream real pipeline outputs arrive at Checkpoint 2, the pipeline is retrained via `python ml_detection/train_model.py`.

---

## 7. Artifact Persistence & Inference

Trained artifacts saved to `ml_detection/models/`:

| File | Contents |
|---|---|
| `isolation_forest.joblib` | Fitted `IsolationForest` model |
| `autoencoder.pt` | PyTorch `state_dict` + `input_dim` + `latent_dim` |
| `scaler.joblib` | Fitted `StandardScaler` (must be used at inference, never refit) |
| `feature_cols.joblib` | Ordered list of 30 feature column names |
| `calibration.joblib` | `s_min`, `s_max`, `err_min`, `err_max`, `alpha` |

Inference is deterministic: identical input + artifacts → identical `anomaly_score`.

---

## 8. Verification Commands

```bash
# Activate environment
source .venv/bin/activate

# Run all tests (canonical verification gate)
pytest sih26146/ml_detection/tests/ -v

# Validate shared schemas
python sih26146/shared/schemas/validate_samples.py

# Retrain (e.g., after Checkpoint 2 real data)
python ml_detection/train_model.py --data-dir sih26146/shared/sample_data --models-dir ml_detection/models

# Evaluate at multiple thresholds
python ml_detection/evaluate_model.py \
  --data-dir sih26146/shared/sample_data \
  --labels-path sih26146/shared/sample_data/labels.json \
  --models-dir ml_detection/models \
  --thresholds 0.3 0.5 0.7 \
  --report-path ml_detection/evaluation_report.md
```

---

## 9. Integration Notes for Module D & F

**Module D (Explainability):**
- Call `from ml_detection.predict import score_transactions`
- Pass full transaction list + optional `data_context` dict
- Use `result["features"]` as SHAP background/inference input

**Module F (Backend API):**
- `score_transactions()` is importable, stateless (after first artifact load), and safe for repeated inference without retraining
- Artifact cache is in-process — no repeated disk reads per request
- Call `clear_artifact_cache()` after retraining to force artifact reload

# Module C — AI/ML Detection

**Owner:** Aadithya S Nair

**Project:** SIH26146 — AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic

**Module:** AI/ML Detection

**Directory:**

```text
/ml_detection
```

---

# Scope

This module is responsible ONLY for AI/ML-based anomaly detection.

Do NOT implement:

* Data ingestion
* Correlation
* Entity clustering
* Pattern detection
* Risk propagation
* SHAP/explainability
* Risk ranking
* Backend API
* Frontend/UI

Those responsibilities belong to other modules.

---

# Core Requirement

Build a genuine trained ML anomaly-detection system.

A rule-based detector is NOT acceptable as the primary detection mechanism.

The system must learn anomalous behavior from transaction/network features.

Rules or pattern signals may be used as model features, but they must not replace the learned models.

Do not hardcode anomaly scores.

Do not fabricate evaluation results.

---

# Inputs

The module consumes outputs from the shared pipeline.

Primary inputs:

```text
BlockchainTxn
CorrelationEdge
Cluster
pattern_type
propagated_risk_score
```

Before implementation, inspect:

```text
/shared/schemas/records.py
```

and the actual available sample data.

Do not assume field names or structures without inspecting them.

---

# Ground Truth

Evaluation labels are available through:

```text
/shared/sample_data/labels.json
```

IMPORTANT:

`labels.json` contains ground-truth labels for evaluation.

Labels MUST NOT be used as model input features.

Do not introduce label leakage.

The distinction must remain:

```text
Training
    ↓
Unsupervised ML models
    ↓
Anomaly score
    ↓
Evaluation
    ↓
Ground-truth labels
```

NOT:

```text
Labels
    ↓
Features
    ↓
Model
```

---

# Required Structure

Create and maintain:

```text
ml_detection/
├── AGENTS.md
├── feature_engineering.py
├── train_model.py
├── evaluate_model.py
├── predict.py
├── models/
├── tests/
└── evaluation_report.md
```

Inspect the existing repository before creating files. If equivalent infrastructure already exists, reuse it instead of duplicating it.

---

# Feature Engineering

Implement meaningful transaction/address-level features.

At minimum consider:

## Transaction Frequency

* Rolling transaction frequency per wallet/address
* Burst activity

## Amount Behavior

* Transaction amount relative to the wallet's historical behavior
* Statistical deviation from normal wallet behavior

Do not use only global thresholds.

Prefer wallet-relative behavior where sufficient history exists.

## Temporal Behavior

Include useful temporal characteristics such as:

* Time-of-day behavior
* Activity bursts
* Unusual temporal concentration

## Graph Behavior

Use graph-derived information available from Module B, such as:

* Degree centrality
* Betweenness centrality
* Other validated graph-derived signals

Do not invent graph features that are unavailable from the actual pipeline.

## Cluster Signals

Use available cluster information, such as:

* Cluster membership
* Validated cluster-level characteristics
* Embedding/membership information if actually available

## Network Geography

Where the upstream data supports it, include:

* Country diversity associated with an address
* ASN diversity

Use the project's local GeoIP data/resources where applicable.

## Pattern Signals

Where available, include:

```text
pattern_type
```

Relevant signals may include:

* Peeling-chain behavior
* CoinJoin/mixing behavior

These are model features, not replacements for ML detection.

## Risk Propagation

Where available:

```text
propagated_risk_score
```

Use it as an input feature.

---

# ML Architecture

The module must use TWO model components.

## 1. Isolation Forest

Use Isolation Forest as the primary unsupervised anomaly detector.

The implementation must train an actual model using the engineered feature representation.

Do not manually calculate a score and label it an Isolation Forest result.

---

## 2. Feedforward Autoencoder

Train a feedforward Autoencoder to learn normal feature representations.

Use reconstruction error as an anomaly signal.

The implementation must contain an actual trainable neural network rather than a placeholder reconstruction calculation.

---

# Combined Anomaly Score

Combine:

```text
Isolation Forest anomaly signal
+
Autoencoder reconstruction signal
```

into:

```text
anomaly_score ∈ [0, 1]
```

The normalization process must be explicit and reproducible.

Document:

* How Isolation Forest output is normalized.
* How Autoencoder reconstruction error is normalized.
* How the two signals are combined.
* Why the selected weighting is reasonable.

The final score must primarily represent the outputs of the trained ML models.

Do not create a disguised rule-based scoring system.

---

# Training Pipeline

`train_model.py` must perform the complete training process.

Expected flow:

```text
Load pipeline data
        ↓
Feature engineering
        ↓
Data cleaning / validation
        ↓
Feature scaling where appropriate
        ↓
Train Isolation Forest
        ↓
Train Autoencoder
        ↓
Normalize anomaly signals
        ↓
Combine scores
        ↓
Save models + preprocessing artifacts
```

Handle:

* Missing values
* Invalid values
* Numeric conversion
* Feature consistency

appropriately.

Do not silently discard large portions of the dataset without understanding why.

---

# Model Artifacts

Save trained artifacts under:

```text
/ml_detection/models/
```

Use `joblib` for compatible sklearn/preprocessing artifacts where appropriate.

The prediction pipeline must use the same preprocessing artifacts used during training.

Do not save models to random temporary locations.

Do not commit unnecessary generated datasets or huge model binaries unless the repository's existing policy explicitly requires them.

---

# Evaluation

Implement:

```text
evaluate_model.py
```

Evaluation must use:

```text
/shared/sample_data/labels.json
```

as ground truth.

Report, where applicable:

* Precision
* Recall
* F1
* Confusion matrix
* Number of flagged transactions
* Anomaly-score distribution
* Threshold-specific results

Write the results to:

```text
evaluation_report.md
```

Clearly distinguish:

```text
Unsupervised training
```

from:

```text
Ground-truth evaluation
```

Ground-truth labels must NEVER influence training features.

---

# Prediction Interface

Implement:

```python
score_transactions(transactions)
```

Expected output:

```python
[
    {
        "txid": "...",
        "anomaly_score": 0.0,
        "features": {...}
    }
]
```

Requirements:

* Importable by other modules.
* Loads saved model artifacts.
* Works on unseen transactions.
* Uses the same preprocessing pipeline as training.
* Produces deterministic output for identical input/model state.
* Always returns `anomaly_score` in `[0, 1]`.

Module F must eventually be able to call this function as part of system integration.

Do not require the caller to manually reproduce feature engineering or model preprocessing.

---

# Testing

Create tests under:

```text
/ml_detection/tests/
```

At minimum test:

### Feature Engineering

* Valid transactions produce valid features.
* Expected feature fields exist.
* Missing data is handled safely.
* Invalid data does not silently corrupt the feature matrix.

### Model

* Isolation Forest trains successfully.
* Autoencoder trains successfully.
* Model artifacts are saved.
* Saved artifacts can be loaded.

### Prediction

* Prediction works on unseen data.
* Output format is correct.
* `txid` is preserved.
* `anomaly_score` is numeric.
* Every score satisfies:

```text
0 <= anomaly_score <= 1
```

### Leakage

Verify that ground-truth labels are NOT included in model features.

### Evaluation

Verify that evaluation can compare model outputs against ground-truth labels.

---

# Required Performance Target

The project specification defines the following target condition:

```text
Average anomaly score of labeled anomalies > 0.6
```

Treat this as an evaluation target, NOT as a reason to manipulate the system.

If the model does not achieve the target:

DO NOT:

* Change labels.
* Add labels as features.
* Hardcode scores.
* Artificially inflate anomaly scores.
* Create a fake evaluation result.
* Tune the output solely to manufacture the target.

Instead investigate:

* Feature quality
* Data quality
* Model configuration
* Scaling
* Training procedure
* Anomaly-score normalization
* Dataset composition

Document the actual result.

---

# Real Data Checkpoint

Initial development may use:

```text
/shared/sample_data/
```

However, the model must eventually consume real outputs from Module B.

At the real-data checkpoint:

1. Inspect Module B's actual output.
2. Validate it against shared schemas.
3. Adapt feature extraction if necessary.
4. Retrain the models.
5. Re-evaluate.
6. Regenerate `evaluation_report.md`.
7. Test prediction on unseen real pipeline data.

Do not declare Module C complete while it only works with placeholder data if real pipeline data is available.

---

# Integration With Module D

Module D depends on the actual ML output.

Make the anomaly score and relevant model output available through clean, documented interfaces.

Do not implement SHAP or explainability inside Module C unless explicitly requested for integration support.

The responsibility of Module C is to produce reliable model predictions and feature data that Module D can explain.

---

# Integration With Module F

Module F will eventually integrate Module C into the backend/system pipeline.

The prediction interface should therefore be:

* Importable
* Stable
* Documented
* Independent of CLI-only execution
* Safe for repeated inference

Do not make the backend depend on manually running `train_model.py` during every prediction.

Training and inference are separate operations.

---

# Development Workflow

Before writing code:

### Step 1 — Inspect

Inspect:

```text
repository structure
/shared/schemas/
/shared/sample_data/
/ml_detection/
```

Inspect existing:

* Python dependencies
* utilities
* data models
* preprocessing code
* tests

### Step 2 — Plan

Create a numbered TODO plan.

Example:

```text
1. Inspect shared schemas.
2. Inspect sample data.
3. Design feature representation.
4. Implement feature engineering.
5. Implement preprocessing.
6. Implement Isolation Forest.
7. Implement Autoencoder.
8. Implement score normalization.
9. Implement model persistence.
10. Implement prediction interface.
11. Implement evaluation.
12. Add tests.
13. Run verification.
```

### Step 3 — Implement

Implement incrementally.

Tests should be added alongside implementation.

### Step 4 — Verify

Run the relevant tests and validation commands.

Do not claim completion before verification.

---

# Verification Commands

Run:

```bash
pytest ml_detection/tests/ -v
```

Also run:

```bash
python shared/schemas/validate_samples.py
```

If the repository uses a different invocation discovered during inspection, use the project's actual documented command instead.

Before completion verify:

* Feature engineering works.
* Isolation Forest trains.
* Autoencoder trains.
* Models save.
* Models load.
* Prediction works.
* Unseen data works.
* Scores remain in `[0,1]`.
* Evaluation report exists.
* No label leakage exists.
* Shared schemas remain valid.
* Real pipeline data can be processed when available.

Include the actual command output when reporting completion.

---

# Git

Branch:

```text
module/ml_detection
```

Before pushing:

```bash
git pull --rebase origin main
```

Commit format:

```text
[ml_detection] description
```

Never push directly to `main`.

Never force-push.

Do not modify another contributor's module.

---

# Non-Negotiable Rules

1. Use a real trained ML model.
2. Use Isolation Forest.
3. Use a feedforward Autoencoder.
4. Produce a combined anomaly score.
5. Keep scores within `[0,1]`.
6. Do not use ground-truth labels as training features.
7. Do not hardcode anomaly scores.
8. Do not fake evaluation results.
9. Do not turn the system into a rule-based detector.
10. Respect shared schemas.
11. Test implementation alongside development.
12. Verify saved-model loading.
13. Verify inference on unseen data.
14. Retrain/re-evaluate when real upstream data becomes available.
15. Stay within the Module C scope.
16. Do not silently modify other modules.
17. Do not claim verification without actually running it.
18. Prefer existing repository infrastructure over unnecessary new dependencies.
19. Report genuine limitations instead of fabricating successful results.
20. The final implementation must be capable of real integration with the rest of the SIH26146 pipeline.

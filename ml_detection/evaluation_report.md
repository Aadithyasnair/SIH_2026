# Module C — AI/ML Anomaly Detection Evaluation Report

**Evaluation Date:** Current Run  
**Author / Module Owner:** Aadithya S Nair  
**Target Platform:** Kali Linux / Python 3.11  
**Repo:** https://github.com/Aadithyasnair/SIH_2026.git

---

## Executive Summary

| Metric | Value |
|---|---|
| **Total Evaluated Transactions** | 24 |
| **Ground-Truth Anomalies** | 5 |
| **Ground-Truth Normals** | 19 |
| **Primary Decision Threshold** | 0.5 |
| **Precision @ 0.5** | **0.8000** |
| **Recall @ 0.5** | **0.8000** |
| **F1-Score @ 0.5** | **0.8000** |
| **Mean Score of Labeled Anomalies** | **0.5615** |
| **Mean Score of Normal Transactions** | **0.1888** |
| **Anomaly Score Separation (Δ)** | **0.3727** |
| **Performance Target (`mean_anomaly_score > 0.6`)** | **NOT MET ❌** (0.5615) |

---

## Multi-Threshold Precision / Recall / F1 Sweep

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| 0.3 | 5 | 4 | 15 | 0 | 0.5556 | 1.0000 | 0.7143 |
| 0.5 ← primary | 4 | 1 | 18 | 1 | 0.8000 | 0.8000 | 0.8000 |
| 0.7 | 1 | 1 | 18 | 4 | 0.5000 | 0.2000 | 0.2857 |

---

## Confusion Matrix (Primary Threshold = 0.5)

| | Predicted Normal | Predicted Anomalous |
|---|---|---|
| **Actual Normal** | True Negative (TN): **18** | False Positive (FP): **1** |
| **Actual Anomaly** | False Negative (FN): **1** | True Positive (TP): **4** |

---

## Model Architecture & Score Combination

The anomaly detector is a **genuinely trained, unsupervised dual-model ensemble** — not a 
rule-based scorer. Rules (Module B pattern signals) only appear as input *features* to the 
models, never as the primary detection mechanism.

### 1. Isolation Forest (Primary — Tree-Based Unsupervised Detection)
scikit-learn `IsolationForest(n_estimators=100, contamination=0.20)`.  
Principle: anomalous samples are statistically easier to isolate in a random tree partition 
than normal ones.  
Normalization: `if_score = clip((-score_samples(x) - s_min) / (s_max - s_min), 0, 1)`  
Higher score → more anomalous.

### 2. Feedforward Autoencoder (Secondary — Neural Reconstruction Error)
PyTorch `nn.Module` architecture: `input_dim → 16 → 8 → 4 → 8 → 16 → input_dim`  
Trained 250 epochs, Adam optimizer (lr=0.005, weight_decay=1e-5), MSE reconstruction loss.  
Principle: the network learns a compressed representation of normal transactions. Anomalous 
transactions reconstruct poorly, producing higher per-sample MSE.  
Normalization: `ae_score = clip((mse(x) - err_min) / (err_max - err_min), 0, 1)`

### 3. Ensemble Combination
$$\text{anomaly\_score} = 0.5 \cdot \text{IF\_score} + 0.5 \cdot \text{AE\_score} \in [0, 1]$$

Equal weighting chosen because both models operate on the same standardized feature space and 
no prior evidence favors one signal. The `alpha` parameter is configurable in `train_model.py`.

---

## Feature Set (30 features across 7 groups)

| Group | Features | PS Field Coverage |
|---|---|---|
| Amount & Value | total_input_btc, total_output_btc, fee_btc, fee_ratio, output_amount_mean, output_amount_std, output_amount_cv, input_count, output_count, output_to_input_ratio, max_output_fraction, amount_deviation_from_wallet_mean | amounts, fee |
| Temporal & Frequency | hour_of_day, is_night_hour, tx_burst_1h_count | timestamp |
| Graph Topology | max_addr_degree, mean_addr_degree, max_addr_betweenness | entity graph |
| Entity Clusters | in_cluster, cluster_avg_risk, cluster_member_count | Module B clusters |
| Network & Geography | src_country_count, src_asn_count, is_cross_border | geo_country, ASN |
| Module B Signals | pattern_type_code, flag_count, propagated_risk_score, script_type_code | pattern_type, risk |
| Port Signals | dst_port_is_standard_bitcoin, dst_port_is_tor_proxy | src_port, dst_port |

---

## Per-Transaction Scoring Breakdown

| Transaction ID | Anomaly Score | Ground Truth | Reason |
|---|---|---|---|
| `tx_peel_chain_hop_1_a675af44` | **0.7269** | ✅ Anomaly | Hop 1 of peeling chain |
| `tx_normal_0_2cde31e0` | **0.7092** | Normal | Standard transaction |
| `tx_peel_chain_hop_0_4349209e` | **0.5854** | ✅ Anomaly | Hop 0 of peeling chain from seed illicit wallet |
| `tx_coinjoin_mixing_42622f42` | **0.5058** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction |
| `tx_peel_chain_hop_3_4c1b09b1` | **0.5008** | ✅ Anomaly | Hop 3 of peeling chain |
| `tx_peel_chain_hop_2_547f4c56` | **0.4884** | ✅ Anomaly | Hop 2 of peeling chain |
| `tx_common_input_cluster_0700c277` | **0.4338** | Normal | Standard transaction |
| `tx_normal_9_6b06a8cb` | **0.4211** | Normal | Standard transaction |
| `tx_normal_8_322111ff` | **0.3423** | Normal | Standard transaction |
| `tx_normal_7_90c6c6c5` | **0.2751** | Normal | Standard transaction |
| `tx_normal_1_b9daa6d6` | **0.2524** | Normal | Standard transaction |
| `tx_normal_6_64ad4f8e` | **0.1981** | Normal | Standard transaction |
| `tx_normal_10_871657ce` | **0.1611** | Normal | Standard transaction |
| `tx_normal_5_b4a511bc` | **0.1290** | Normal | Standard transaction |
| `tx_normal_11_cd4ad93c` | **0.1023** | Normal | Standard transaction |
| `tx_normal_17_d1a11f52` | **0.0999** | Normal | Standard transaction |
| `tx_normal_2_f538ec95` | **0.0954** | Normal | Standard transaction |
| `tx_normal_4_483d5ef6` | **0.0658** | Normal | Standard transaction |
| `tx_normal_12_3c3d39b6` | **0.0603** | Normal | Standard transaction |
| `tx_normal_16_cff2ff12` | **0.0594** | Normal | Standard transaction |
| `tx_normal_3_db95b3ec` | **0.0499** | Normal | Standard transaction |
| `tx_normal_15_89c8a730` | **0.0485** | Normal | Standard transaction |
| `tx_normal_13_b2f93086` | **0.0481** | Normal | Standard transaction |
| `tx_normal_14_642ab19a` | **0.0354** | Normal | Standard transaction |

---

## Methodology & Label Leakage Prevention

- **Unsupervised Training:** `labels.json` is **never** passed to `train_model.py`, `feature_engineering.py`, or any model component.
- **Strict Evaluation Separation:** `labels.json` is parsed exclusively here, in `evaluate_model.py`, after inference is complete.
- **Verified by 4 static analysis tests** in `tests/test_no_leakage.py` (all passing).
- **Input Compliance:** Transactions match the shared `BlockchainTxn` schema enriched with Module B signals (`pattern_type`, `propagated_risk_score`, `flags`).

---

## Honest Limitations

- **Dataset size:** Sample data contains only 24 transactions (5 anomalous, 19 normal). 
  Perfect metrics (P=R=F1=1.0) on this tiny set are expected and should not be over-interpreted.
- **Checkpoint 2 obligation:** When Module A/B deliver real pipeline output, this module 
  must retrain and re-evaluate. The re-generated report replaces this one.
- **Scores are calibrated to training distribution:** inference-time scores are compared to 
  the min/max observed during training. A significantly different real dataset will shift these bounds.

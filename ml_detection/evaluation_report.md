# Module C — AI/ML Anomaly Detection Evaluation Report

**Evaluation Date:** Current Run  
**Author / Module Owner:** Aadithya S Nair  
**Target Platform:** Kali Linux / Python 3.11  
**Repo:** https://github.com/Aadithyasnair/SIH_2026.git

---

## Executive Summary

| Metric | Value |
|---|---|
| **Total Evaluated Transactions** | 3000 |
| **Ground-Truth Anomalies** | 360 |
| **Ground-Truth Normals** | 2640 |
| **Primary Decision Threshold** | 0.5 |
| **Precision @ 0.5** | **0.6601** |
| **Recall @ 0.5** | **0.9278** |
| **F1-Score @ 0.5** | **0.7714** |
| **Mean Score of Labeled Anomalies** | **0.6966** |
| **Mean Score of Normal Transactions** | **0.2409** |
| **Anomaly Score Separation (Δ)** | **0.4557** |
| **Performance Target (`mean_anomaly_score > 0.6`)** | **PASSED ✅** (0.6966) |

---

## Multi-Threshold Precision / Recall / F1 Sweep

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| 0.3 | 360 | 772 | 1868 | 0 | 0.3180 | 1.0000 | 0.4826 |
| 0.4 | 360 | 383 | 2257 | 0 | 0.4845 | 1.0000 | 0.6528 |
| 0.5 ← primary | 334 | 172 | 2468 | 26 | 0.6601 | 0.9278 | 0.7714 |
| 0.6 | 286 | 71 | 2569 | 74 | 0.8011 | 0.7944 | 0.7978 |
| 0.7 | 162 | 29 | 2611 | 198 | 0.8482 | 0.4500 | 0.5880 |

---

## Confusion Matrix (Primary Threshold = 0.5)

| | Predicted Normal | Predicted Anomalous |
|---|---|---|
| **Actual Normal** | True Negative (TN): **2468** | False Positive (FP): **172** |
| **Actual Anomaly** | False Negative (FN): **26** | True Positive (TP): **334** |

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
| `tx_peel_chain_c10_hop4_1abd3a1e` | **1.0000** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_whale_spike_22_cd66bae2` | **1.0000** | ✅ Anomaly | Amount 151.3597 BTC is >20x historical mean for sender bc1q14550de0 |
| `tx_whale_spike_29_70f76ed8` | **1.0000** | ✅ Anomaly | Amount 610.8787 BTC is >20x historical mean for sender 11aabb132535 |
| `tx_whale_spike_34_3967da88` | **1.0000** | ✅ Anomaly | Amount 329.3777 BTC is >20x historical mean for sender bc1q8ec7a8ee |
| `tx_whale_spike_48_034e865a` | **1.0000** | ✅ Anomaly | Amount 633.4922 BTC is >20x historical mean for sender 36afe4039141 |
| `tx_whale_spike_54_e91dc8a1` | **1.0000** | ✅ Anomaly | Amount 1578.8206 BTC is >20x historical mean for sender bc1q17436174 |
| `tx_whale_spike_56_d1fbfa46` | **1.0000** | ✅ Anomaly | Amount 3997.4084 BTC is >20x historical mean for sender 11276ec41b55 |
| `tx_whale_spike_4_4a419461` | **0.9997** | ✅ Anomaly | Amount 39.1853 BTC is >20x historical mean for sender bc1qe04be954 |
| `tx_whale_spike_28_cbfa8012` | **0.9909** | ✅ Anomaly | Amount 248.8323 BTC is >20x historical mean for sender 1a76ad803b96 |
| `tx_whale_spike_5_513ef43f` | **0.9891** | ✅ Anomaly | Amount 422.2065 BTC is >20x historical mean for sender bc1qa1223313 |
| `tx_whale_spike_24_20a28861` | **0.9881** | ✅ Anomaly | Amount 543.0384 BTC is >20x historical mean for sender bc1qca6f723f |
| `tx_tor_proxied_31_5962d889` | **0.9741** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (09:00 UTC) |
| `tx_whale_spike_32_c1be3821` | **0.9738** | ✅ Anomaly | Amount 0.5445 BTC is >20x historical mean for sender bc1q338ab97b |
| `tx_whale_spike_15_1285cb9d` | **0.9697** | ✅ Anomaly | Amount 30.7115 BTC is >20x historical mean for sender 1ad54fdf1dd9 |
| `tx_tor_proxied_10_4574353d` | **0.9577** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (09:00 UTC) |
| `tx_tor_proxied_5_2c922bfc` | **0.9435** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (11:00 UTC) |
| `tx_coinjoin_mixing_40_1d730f77` | **0.9432** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (7 inputs/outputs of 0.1 BTC) |
| `tx_tor_proxied_19_2b523fc0` | **0.9391** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (13:00 UTC) |
| `tx_whale_spike_44_eb11b0ec` | **0.9388** | ✅ Anomaly | Amount 1.609 BTC is >20x historical mean for sender 19faa9cc3145 |
| `tx_whale_spike_16_7bb52f93` | **0.9369** | ✅ Anomaly | Amount 7.3147 BTC is >20x historical mean for sender bc1qf4d31233 |
| `tx_whale_spike_51_00d9d65e` | **0.9354** | ✅ Anomaly | Amount 43.5679 BTC is >20x historical mean for sender bc1qa3c51970 |
| `tx_whale_spike_13_8225c10b` | **0.9319** | ✅ Anomaly | Amount 7.314 BTC is >20x historical mean for sender 1567ea5df2c5 |
| `tx_tor_proxied_0_487e03e8` | **0.9265** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (13:00 UTC) |
| `tx_burst_layering_h14_n0_63a70342` | **0.9239** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_coinjoin_mixing_0_ac7e6c2f` | **0.9223** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 0.25 BTC) |
| `tx_whale_spike_38_16e36a70` | **0.9193** | ✅ Anomaly | Amount 7.2089 BTC is >20x historical mean for sender 19835cde2c1a |
| `tx_whale_spike_26_43d677ba` | **0.9178** | ✅ Anomaly | Amount 3.4618 BTC is >20x historical mean for sender 3a1c30e10dfc |
| `tx_tor_proxied_11_b2e83aa3` | **0.9164** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (08:00 UTC) |
| `tx_whale_spike_10_874c117f` | **0.9153** | ✅ Anomaly | Amount 7.5231 BTC is >20x historical mean for sender bc1qebcc1be7 |
| `tx_whale_spike_57_e088e122` | **0.9125** | ✅ Anomaly | Amount 28.2139 BTC is >20x historical mean for sender 17c00e3c5bba |
| `tx_whale_spike_39_15158ebd` | **0.9111** | ✅ Anomaly | Amount 29.6423 BTC is >20x historical mean for sender 174a567164ac |
| `tx_norm_532_3f00a9ec` | **0.9021** | Normal | Standard transaction |
| `tx_tor_proxied_2_68ca89e1` | **0.8978** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (10:00 UTC) |
| `tx_whale_spike_50_06053373` | **0.8967** | ✅ Anomaly | Amount 372.8777 BTC is >20x historical mean for sender 127b7cdd113d |
| `tx_burst_layering_h15_n0_f738f990` | **0.8965** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_coinjoin_mixing_6_226f45c7` | **0.8962** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (6 inputs/outputs of 0.1 BTC) |
| `tx_coinjoin_mixing_25_eab72d17` | **0.8927** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (6 inputs/outputs of 0.25 BTC) |
| `tx_tor_proxied_22_71820943` | **0.8916** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (13:00 UTC) |
| `tx_coinjoin_mixing_53_d60c5e06` | **0.8820** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 2.0 BTC) |
| `tx_norm_1686_e1e8c636` | **0.8812** | Normal | Standard transaction |
| `tx_peel_chain_c22_hop2_8ab2b287` | **0.8771** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_coinjoin_mixing_32_aeb450c8` | **0.8762** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (6 inputs/outputs of 0.1 BTC) |
| `tx_norm_1457_1b3e4a89` | **0.8752** | Normal | Standard transaction |
| `tx_tor_proxied_24_2a832581` | **0.8749** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (13:00 UTC) |
| `tx_coinjoin_mixing_24_ea1d5001` | **0.8730** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (6 inputs/outputs of 0.5 BTC) |
| `tx_tor_proxied_30_d5f0c379` | **0.8680** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (13:00 UTC) |
| `tx_coinjoin_mixing_12_f8330a49` | **0.8665** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (12 inputs/outputs of 1.0 BTC) |
| `tx_peel_chain_c22_hop3_61613f94` | **0.8663** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_293_120ceb32` | **0.8647** | Normal | Standard transaction |
| `tx_whale_spike_46_5112d8a5` | **0.8615** | ✅ Anomaly | Amount 46.6525 BTC is >20x historical mean for sender 30d6ec83750c |
| `tx_coinjoin_mixing_33_23c61bc7` | **0.8589** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (6 inputs/outputs of 0.25 BTC) |
| `tx_whale_spike_35_d6ad0042` | **0.8589** | ✅ Anomaly | Amount 15.7081 BTC is >20x historical mean for sender bc1q40d0afa9 |
| `tx_whale_spike_0_66dbed4b` | **0.8563** | ✅ Anomaly | Amount 28.6636 BTC is >20x historical mean for sender bc1q180c8fa9 |
| `tx_norm_841_df1bb037` | **0.8558** | Normal | Standard transaction |
| `tx_peel_chain_c19_hop4_041dad6c` | **0.8552** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_norm_486_3f0ec998` | **0.8536** | Normal | Standard transaction |
| `tx_whale_spike_31_7083bde3` | **0.8485** | ✅ Anomaly | Amount 24.5785 BTC is >20x historical mean for sender 13fb80dc8076 |
| `tx_norm_1167_109049a5` | **0.8460** | Normal | Standard transaction |
| `tx_norm_1379_1bfb7d15` | **0.8456** | Normal | Standard transaction |
| `tx_whale_spike_1_e121ad7e` | **0.8447** | ✅ Anomaly | Amount 44.5052 BTC is >20x historical mean for sender bc1qc99081a3 |
| `tx_peel_chain_c21_hop4_01192847` | **0.8390** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_1678_2490e652` | **0.8379** | Normal | Standard transaction |
| `tx_tor_proxied_16_2ef4f595` | **0.8353** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (12:00 UTC) |
| `tx_whale_spike_7_bf97a4d4` | **0.8338** | ✅ Anomaly | Amount 7.5349 BTC is >20x historical mean for sender 353857f0c8e6 |
| `tx_coinjoin_mixing_9_5565d566` | **0.8328** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (7 inputs/outputs of 0.25 BTC) |
| `tx_coinjoin_mixing_52_f27b4706` | **0.8318** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (12 inputs/outputs of 0.25 BTC) |
| `tx_tor_proxied_6_ae3bfb55` | **0.8307** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (10:00 UTC) |
| `tx_coinjoin_mixing_51_260b4daf` | **0.8263** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (6 inputs/outputs of 0.25 BTC) |
| `tx_norm_1512_d74db8b9` | **0.8247** | Normal | Standard transaction |
| `tx_coinjoin_mixing_58_18f41483` | **0.8215** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 0.1 BTC) |
| `tx_coinjoin_mixing_7_a27b61e1` | **0.8184** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (12 inputs/outputs of 1.0 BTC) |
| `tx_coinjoin_mixing_23_6275c444` | **0.8139** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (6 inputs/outputs of 2.0 BTC) |
| `tx_coinjoin_mixing_4_de49c690` | **0.8128** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (6 inputs/outputs of 0.25 BTC) |
| `tx_burst_layering_h12_n2_ec50d76c` | **0.8127** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_whale_spike_14_b17e98a9` | **0.8125** | ✅ Anomaly | Amount 7.628 BTC is >20x historical mean for sender bc1q5992e120 |
| `tx_peel_chain_c1_hop3_92410b7e` | **0.8120** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_burst_layering_h9_n1_0a06f712` | **0.8092** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_coinjoin_mixing_30_a3fce8ad` | **0.8091** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 0.1 BTC) |
| `tx_whale_spike_18_a0969047` | **0.8085** | ✅ Anomaly | Amount 18.897 BTC is >20x historical mean for sender 1392f1e56655 |
| `tx_tor_proxied_37_58211e09` | **0.8066** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (11:00 UTC) |
| `tx_coinjoin_mixing_14_3ec177cb` | **0.8052** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (12 inputs/outputs of 0.1 BTC) |
| `tx_tor_proxied_29_85e2cda3` | **0.8022** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (08:00 UTC) |
| `tx_norm_33_cd4a84c1` | **0.8018** | Normal | Standard transaction |
| `tx_coinjoin_mixing_48_52c884f1` | **0.8017** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (12 inputs/outputs of 1.0 BTC) |
| `tx_peel_chain_c1_hop2_459dabeb` | **0.8016** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_coinjoin_mixing_26_15ed70c6` | **0.7982** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 0.1 BTC) |
| `tx_whale_spike_33_0718c17e` | **0.7982** | ✅ Anomaly | Amount 4.3529 BTC is >20x historical mean for sender bc1qfb57fdb3 |
| `tx_coinjoin_mixing_22_d8dcf1e7` | **0.7969** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 0.5 BTC) |
| `tx_whale_spike_2_3ddc6ed0` | **0.7959** | ✅ Anomaly | Amount 107.9306 BTC is >20x historical mean for sender 1ff5a6fe3867 |
| `tx_whale_spike_49_11ab95d2` | **0.7934** | ✅ Anomaly | Amount 25.4265 BTC is >20x historical mean for sender 12dbeed37483 |
| `tx_tor_proxied_28_7218625a` | **0.7912** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (08:00 UTC) |
| `tx_norm_200_3c7d2d49` | **0.7905** | Normal | Standard transaction |
| `tx_whale_spike_25_18502876` | **0.7898** | ✅ Anomaly | Amount 42.5719 BTC is >20x historical mean for sender bc1q7ac19cda |
| `tx_coinjoin_mixing_15_4f9c05f3` | **0.7882** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (6 inputs/outputs of 0.25 BTC) |
| `tx_burst_layering_h15_n1_ab5f5e4e` | **0.7806** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_300_9cee766c` | **0.7778** | Normal | Standard transaction |
| `tx_whale_spike_6_d74704a8` | **0.7776** | ✅ Anomaly | Amount 10.238 BTC is >20x historical mean for sender 1567ea5df2c5 |
| `tx_tor_proxied_4_a28ad403` | **0.7770** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (10:00 UTC) |
| `tx_whale_spike_43_eac18ef4` | **0.7767** | ✅ Anomaly | Amount 46.8176 BTC is >20x historical mean for sender bc1qc99081a3 |
| `tx_whale_spike_19_5e46a587` | **0.7763** | ✅ Anomaly | Amount 4.8165 BTC is >20x historical mean for sender bc1q1e99551a |
| `tx_whale_spike_3_6bb8ad7c` | **0.7760** | ✅ Anomaly | Amount 10.7144 BTC is >20x historical mean for sender bc1pb2bee741 |
| `tx_burst_layering_h14_n2_afc88913` | **0.7720** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1033_74ec9052` | **0.7718** | Normal | Standard transaction |
| `tx_coinjoin_mixing_35_3a79028f` | **0.7711** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (10 inputs/outputs of 0.5 BTC) |
| `tx_whale_spike_42_b2cbb812` | **0.7701** | ✅ Anomaly | Amount 34.7115 BTC is >20x historical mean for sender 34c3da83a456 |
| `tx_norm_384_ddb053bb` | **0.7690** | Normal | Standard transaction |
| `tx_norm_2504_a6fde8be` | **0.7680** | Normal | Standard transaction |
| `tx_peel_chain_c23_hop0_0efb3056` | **0.7677** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_coinjoin_mixing_17_b372fc0e` | **0.7673** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 1.0 BTC) |
| `tx_coinjoin_mixing_38_17f4bca1` | **0.7658** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 2.0 BTC) |
| `tx_coinjoin_mixing_54_c961dc68` | **0.7653** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 2.0 BTC) |
| `tx_burst_layering_h4_n1_30d1956a` | **0.7653** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_peel_chain_c8_hop0_08356c27` | **0.7650** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_whale_spike_21_779ce3a6` | **0.7649** | ✅ Anomaly | Amount 25.8824 BTC is >20x historical mean for sender 1294848c736f |
| `tx_tor_proxied_1_1bef8c4b` | **0.7649** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (11:00 UTC) |
| `tx_coinjoin_mixing_29_73a1d230` | **0.7599** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 0.25 BTC) |
| `tx_coinjoin_mixing_1_29ed3808` | **0.7583** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 0.25 BTC) |
| `tx_coinjoin_mixing_21_ab492d9a` | **0.7581** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 2.0 BTC) |
| `tx_tor_proxied_27_1bcb4fc5` | **0.7572** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (11:00 UTC) |
| `tx_peel_chain_c17_hop1_24f99d14` | **0.7568** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_coinjoin_mixing_50_2371e006` | **0.7566** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (9 inputs/outputs of 2.0 BTC) |
| `tx_norm_1819_320e4cf1` | **0.7560** | Normal | Standard transaction |
| `tx_whale_spike_17_6606c5f6` | **0.7544** | ✅ Anomaly | Amount 14.1633 BTC is >20x historical mean for sender 1d849dc09f10 |
| `tx_coinjoin_mixing_45_cc936138` | **0.7527** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 1.0 BTC) |
| `tx_peel_chain_c17_hop0_581a9dbf` | **0.7526** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_coinjoin_mixing_28_ac96280d` | **0.7526** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (10 inputs/outputs of 0.5 BTC) |
| `tx_coinjoin_mixing_31_372fb837` | **0.7516** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (9 inputs/outputs of 2.0 BTC) |
| `tx_peel_chain_c23_hop4_653c5225` | **0.7511** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c23_hop2_a5fc56c0` | **0.7493** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_2421_633186f5` | **0.7476** | Normal | Standard transaction |
| `tx_peel_chain_c18_hop0_e2b83b34` | **0.7474** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_coinjoin_mixing_57_48073ea4` | **0.7472** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 0.5 BTC) |
| `tx_tor_proxied_14_8007e509` | **0.7469** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (08:00 UTC) |
| `tx_coinjoin_mixing_39_5b808d87` | **0.7463** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (10 inputs/outputs of 2.0 BTC) |
| `tx_peel_chain_c18_hop1_97d6953d` | **0.7456** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c2_hop0_931989e0` | **0.7450** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_coinjoin_mixing_59_08416217` | **0.7446** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 2.0 BTC) |
| `tx_norm_2042_243f4d70` | **0.7445** | Normal | Standard transaction |
| `tx_coinjoin_mixing_18_bbb3cf02` | **0.7439** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 1.0 BTC) |
| `tx_coinjoin_mixing_46_ff8b2721` | **0.7439** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 1.0 BTC) |
| `tx_coinjoin_mixing_19_bd690c4a` | **0.7431** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 0.25 BTC) |
| `tx_peel_chain_c23_hop3_196962f9` | **0.7393** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_whale_spike_59_45706b66` | **0.7379** | ✅ Anomaly | Amount 31.875 BTC is >20x historical mean for sender bc1qc54311d3 |
| `tx_coinjoin_mixing_27_c06f478c` | **0.7374** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (9 inputs/outputs of 1.0 BTC) |
| `tx_coinjoin_mixing_41_fa26540f` | **0.7345** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (9 inputs/outputs of 0.1 BTC) |
| `tx_coinjoin_mixing_34_87995d77` | **0.7340** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 0.5 BTC) |
| `tx_coinjoin_mixing_20_80d2f05f` | **0.7330** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (9 inputs/outputs of 0.5 BTC) |
| `tx_peel_chain_c20_hop4_c43c6b50` | **0.7329** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c13_hop0_ede892f8` | **0.7327** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_2353_a5bc671c` | **0.7319** | Normal | Standard transaction |
| `tx_coinjoin_mixing_49_f02d810c` | **0.7310** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (12 inputs/outputs of 1.0 BTC) |
| `tx_coinjoin_mixing_56_2e5ca04e` | **0.7281** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (7 inputs/outputs of 0.5 BTC) |
| `tx_tor_proxied_36_b9022019` | **0.7279** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (12:00 UTC) |
| `tx_norm_147_3e34e8d5` | **0.7279** | Normal | Standard transaction |
| `tx_burst_layering_h13_n2_59309b9a` | **0.7278** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_peel_chain_c1_hop0_d0f55acb` | **0.7266** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_whale_spike_12_850fd809` | **0.7264** | ✅ Anomaly | Amount 13.5953 BTC is >20x historical mean for sender bc1q3f46c970 |
| `tx_whale_spike_40_f5ad852e` | **0.7262** | ✅ Anomaly | Amount 18.9309 BTC is >20x historical mean for sender bc1q89b96b91 |
| `tx_tor_proxied_21_dc184a73` | **0.7261** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (11:00 UTC) |
| `tx_peel_chain_c6_hop4_3065e58e` | **0.7224** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c2_hop1_8b434a22` | **0.7218** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_whale_spike_27_e287ea2d` | **0.7218** | ✅ Anomaly | Amount 7.2653 BTC is >20x historical mean for sender 1123c9a12220 |
| `tx_tor_proxied_7_d5868460` | **0.7212** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (09:00 UTC) |
| `tx_peel_chain_c13_hop1_ef51c3cf` | **0.7204** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c18_hop2_7e395e8e` | **0.7196** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_burst_layering_h9_n2_1c320f12` | **0.7196** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_peel_chain_c4_hop0_edd40185` | **0.7194** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_norm_1187_88740887` | **0.7182** | Normal | Standard transaction |
| `tx_norm_1267_cfe18817` | **0.7182** | Normal | Standard transaction |
| `tx_peel_chain_c3_hop0_a304ce9f` | **0.7179** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_coinjoin_mixing_8_410e440e` | **0.7162** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (10 inputs/outputs of 2.0 BTC) |
| `tx_norm_1977_610ea37f` | **0.7159** | Normal | Standard transaction |
| `tx_norm_1865_90ff1e77` | **0.7150** | Normal | Standard transaction |
| `tx_tor_proxied_3_5ffd702c` | **0.7148** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (10:00 UTC) |
| `tx_whale_spike_52_37263d90` | **0.7147** | ✅ Anomaly | Amount 36.9413 BTC is >20x historical mean for sender bc1q76afad2d |
| `tx_norm_1710_eab4c61d` | **0.7146** | Normal | Standard transaction |
| `tx_tor_proxied_38_9d88e2fb` | **0.7140** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (12:00 UTC) |
| `tx_coinjoin_mixing_5_d149a9b1` | **0.7135** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (9 inputs/outputs of 0.25 BTC) |
| `tx_whale_spike_30_4b846195` | **0.7126** | ✅ Anomaly | Amount 3.3001 BTC is >20x historical mean for sender bc1q95697d3e |
| `tx_whale_spike_53_2d9cb2c2` | **0.7117** | ✅ Anomaly | Amount 6.8872 BTC is >20x historical mean for sender 39ba6f8e13cd |
| `tx_burst_layering_h6_n2_c1164aa9` | **0.7101** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_coinjoin_mixing_44_39a82dca` | **0.7093** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 0.25 BTC) |
| `tx_norm_1503_2a040e07` | **0.7091** | Normal | Standard transaction |
| `tx_whale_spike_58_39043ecd` | **0.7078** | ✅ Anomaly | Amount 52.3043 BTC is >20x historical mean for sender 3f6831e4da72 |
| `tx_peel_chain_c13_hop4_1f55eaa9` | **0.7071** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_burst_layering_h15_n2_c7619554` | **0.7028** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_coinjoin_mixing_2_5e029e0a` | **0.7023** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 0.1 BTC) |
| `tx_peel_chain_c20_hop3_cc6df350` | **0.7013** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c22_hop0_1de58914` | **0.7013** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_541_78d6a562` | **0.7012** | Normal | Standard transaction |
| `tx_norm_2018_8a73c0db` | **0.7009** | Normal | Standard transaction |
| `tx_coinjoin_mixing_10_1e53be1b` | **0.6993** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (10 inputs/outputs of 2.0 BTC) |
| `tx_coinjoin_mixing_43_e083610c` | **0.6973** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 1.0 BTC) |
| `tx_peel_chain_c6_hop3_098bd4be` | **0.6966** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_2380_2568f33c` | **0.6961** | Normal | Standard transaction |
| `tx_whale_spike_9_93e0f4d0` | **0.6955** | ✅ Anomaly | Amount 40.2214 BTC is >20x historical mean for sender bc1qcd84291c |
| `tx_whale_spike_36_abe7f30a` | **0.6944** | ✅ Anomaly | Amount 188.5301 BTC is >20x historical mean for sender 1a76ad803b96 |
| `tx_peel_chain_c7_hop1_e8efc7eb` | **0.6931** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_coinjoin_mixing_37_e85b3fbf` | **0.6928** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (7 inputs/outputs of 2.0 BTC) |
| `tx_tor_proxied_20_fda427e4` | **0.6923** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (09:00 UTC) |
| `tx_peel_chain_c16_hop0_bb1bf8df` | **0.6908** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c7_hop2_25575d5d` | **0.6907** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_2058_80b37a37` | **0.6900** | Normal | Standard transaction |
| `tx_tor_proxied_26_bb69bd40` | **0.6867** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (13:00 UTC) |
| `tx_peel_chain_c19_hop0_5353e0fe` | **0.6866** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c1_hop1_ebff7c59` | **0.6846** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_coinjoin_mixing_16_772a2d55` | **0.6838** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (10 inputs/outputs of 0.5 BTC) |
| `tx_burst_layering_h14_n4_7ea7a4df` | **0.6832** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_peel_chain_c1_hop4_cc7e59cd` | **0.6830** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c22_hop1_6c86ab76` | **0.6830** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_tor_proxied_13_d7025421` | **0.6806** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (10:00 UTC) |
| `tx_tor_proxied_35_eff3f828` | **0.6803** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (09:00 UTC) |
| `tx_tor_proxied_39_aff17919` | **0.6801** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (09:00 UTC) |
| `tx_peel_chain_c18_hop4_664b4600` | **0.6796** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_norm_2345_9bb8afd6` | **0.6795** | Normal | Standard transaction |
| `tx_coinjoin_mixing_47_c7b04602` | **0.6786** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 0.25 BTC) |
| `tx_norm_2108_acffafdf` | **0.6776** | Normal | Standard transaction |
| `tx_coinjoin_mixing_13_b04ce1e7` | **0.6773** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (9 inputs/outputs of 0.5 BTC) |
| `tx_whale_spike_8_bffb868b` | **0.6770** | ✅ Anomaly | Amount 62.0763 BTC is >20x historical mean for sender 188f2a5985da |
| `tx_peel_chain_c10_hop3_1b09c1e9` | **0.6764** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c15_hop4_d31bd156` | **0.6762** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_whale_spike_47_38dd46c8` | **0.6756** | ✅ Anomaly | Amount 11.2802 BTC is >20x historical mean for sender bc1qa341c798 |
| `tx_peel_chain_c9_hop3_ab9f7339` | **0.6755** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_coinjoin_mixing_55_3a2be411` | **0.6752** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (8 inputs/outputs of 1.0 BTC) |
| `tx_peel_chain_c22_hop4_01f322c5` | **0.6747** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c9_hop0_ede57469` | **0.6732** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_whale_spike_23_2a7eb2c1` | **0.6719** | ✅ Anomaly | Amount 49.0961 BTC is >20x historical mean for sender 1e273997a9c9 |
| `tx_norm_980_3a0480c1` | **0.6715** | Normal | Standard transaction |
| `tx_tor_proxied_9_de8ee4c8` | **0.6707** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (09:00 UTC) |
| `tx_whale_spike_45_c5295b10` | **0.6694** | ✅ Anomaly | Amount 10.4084 BTC is >20x historical mean for sender bc1qfe3a6a97 |
| `tx_coinjoin_mixing_11_4daa87ad` | **0.6679** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 1.0 BTC) |
| `tx_burst_layering_h13_n1_9b61b8ad` | **0.6678** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1067_fd128879` | **0.6658** | Normal | Standard transaction |
| `tx_peel_chain_c20_hop2_ed65c3e4` | **0.6655** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_whale_spike_20_fe42183a` | **0.6651** | ✅ Anomaly | Amount 21.4183 BTC is >20x historical mean for sender bc1q12b0b6a9 |
| `tx_peel_chain_c2_hop4_d083c55f` | **0.6643** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_coinjoin_mixing_42_e37ac0d9` | **0.6637** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (11 inputs/outputs of 1.0 BTC) |
| `tx_peel_chain_c8_hop4_60ab3ab9` | **0.6630** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c17_hop4_8fa8ca66` | **0.6630** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c5_hop0_7c24b35f` | **0.6622** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_burst_layering_h10_n3_8cc9171f` | **0.6621** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_35_a3d1bb58` | **0.6602** | Normal | Standard transaction |
| `tx_peel_chain_c4_hop3_c202dc7b` | **0.6594** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_coinjoin_mixing_36_a704de69` | **0.6591** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (10 inputs/outputs of 0.5 BTC) |
| `tx_peel_chain_c16_hop4_2a4b4e57` | **0.6590** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c13_hop3_1ea62f8e` | **0.6580** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_826_5df7b2b9` | **0.6577** | Normal | Standard transaction |
| `tx_peel_chain_c18_hop3_b53a2adc` | **0.6569** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c0_hop0_20381244` | **0.6562** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_tor_proxied_23_070534ac` | **0.6550** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (13:00 UTC) |
| `tx_norm_1752_05811db7` | **0.6549** | Normal | Standard transaction |
| `tx_peel_chain_c13_hop2_19f4feda` | **0.6543** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c20_hop0_e4263c0e` | **0.6539** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c14_hop0_4921b457` | **0.6536** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c15_hop3_46bd7487` | **0.6522** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c9_hop1_057ddc97` | **0.6516** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_1092_87edaef4` | **0.6504** | Normal | Standard transaction |
| `tx_peel_chain_c4_hop1_baf25092` | **0.6502** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c4_hop4_92ca6046` | **0.6501** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_norm_511_548df189` | **0.6501** | Normal | Standard transaction |
| `tx_coinjoin_mixing_3_5abd0ca0` | **0.6500** | ✅ Anomaly | Equal-value multi-party CoinJoin transaction (9 inputs/outputs of 1.0 BTC) |
| `tx_burst_layering_h8_n2_201bd5ea` | **0.6493** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_781_2ee0dbc9` | **0.6470** | Normal | Standard transaction |
| `tx_peel_chain_c17_hop2_dd067277` | **0.6469** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c6_hop0_147f7f11` | **0.6465** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c8_hop1_68224ab9` | **0.6460** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c23_hop1_ff945281` | **0.6458** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_tor_proxied_34_4295e2e8` | **0.6455** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (12:00 UTC) |
| `tx_norm_2070_2f2aa4fe` | **0.6450** | Normal | Standard transaction |
| `tx_peel_chain_c9_hop2_79c04eb3` | **0.6431** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_tor_proxied_12_539c2dfd` | **0.6431** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (11:00 UTC) |
| `tx_peel_chain_c3_hop1_6d02cd2b` | **0.6429** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_whale_spike_41_8e396a72` | **0.6429** | ✅ Anomaly | Amount 28.3105 BTC is >20x historical mean for sender 38da3bc662aa |
| `tx_peel_chain_c3_hop2_8093f728` | **0.6423** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c9_hop4_51bd84da` | **0.6420** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c7_hop0_ced9930c` | **0.6412** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c8_hop3_1e8a2353` | **0.6410** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c15_hop0_77071f29` | **0.6403** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c12_hop0_867a3203` | **0.6402** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_689_cfced000` | **0.6396** | Normal | Standard transaction |
| `tx_tor_proxied_33_61161e75` | **0.6394** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (09:00 UTC) |
| `tx_peel_chain_c2_hop3_e1a74d68` | **0.6381** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c21_hop0_2fa33db2` | **0.6379** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c11_hop0_c863fcab` | **0.6369** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_2386_57cec1a8` | **0.6364** | Normal | Standard transaction |
| `tx_peel_chain_c4_hop2_c17f3d56` | **0.6357** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_burst_layering_h2_n4_5be15fae` | **0.6350** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1972_f18d241c` | **0.6348** | Normal | Standard transaction |
| `tx_norm_2060_4cb66445` | **0.6348** | Normal | Standard transaction |
| `tx_peel_chain_c16_hop2_32737f13` | **0.6346** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c17_hop3_1e51316c` | **0.6345** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_tor_proxied_15_ea8e9ef4` | **0.6344** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (13:00 UTC) |
| `tx_peel_chain_c3_hop4_e96782ce` | **0.6340** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c12_hop4_c11f4e67` | **0.6326** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c0_hop4_b1f27e09` | **0.6320** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c16_hop3_4d87efc4` | **0.6307** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_burst_layering_h2_n2_309e5db2` | **0.6305** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1300_138f83d1` | **0.6297** | Normal | Standard transaction |
| `tx_peel_chain_c3_hop3_2f1b1153` | **0.6292** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c10_hop0_d3c3e0f9` | **0.6291** | ✅ Anomaly | Hop 0 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c16_hop1_be54838e` | **0.6279** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_norm_2043_03b99876` | **0.6273** | Normal | Standard transaction |
| `tx_norm_2125_f2347823` | **0.6267** | Normal | Standard transaction |
| `tx_norm_2135_c3aebfc8` | **0.6266** | Normal | Standard transaction |
| `tx_norm_274_453b7589` | **0.6259** | Normal | Standard transaction |
| `tx_peel_chain_c10_hop1_61294c7a` | **0.6252** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c0_hop1_8a121aa0` | **0.6250** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_burst_layering_h6_n1_e0744b25` | **0.6249** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2221_dd17eb9f` | **0.6238** | Normal | Standard transaction |
| `tx_norm_1849_54a6210b` | **0.6237** | Normal | Standard transaction |
| `tx_tor_proxied_25_b04c461f` | **0.6235** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (10:00 UTC) |
| `tx_burst_layering_h0_n4_0bfc0228` | **0.6231** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1781_aacd1b3a` | **0.6217** | Normal | Standard transaction |
| `tx_peel_chain_c14_hop1_df59d29c` | **0.6214** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c8_hop2_4522346d` | **0.6213** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c2_hop2_b83ce4c0` | **0.6211** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c5_hop3_e53c59d5` | **0.6197** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c14_hop4_8f302dea` | **0.6193** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c7_hop4_3b518d39` | **0.6187** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_burst_layering_h2_n0_e3ace794` | **0.6187** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_664_96ec9701` | **0.6183** | Normal | Standard transaction |
| `tx_norm_1023_ca21447e` | **0.6180** | Normal | Standard transaction |
| `tx_burst_layering_h9_n4_3980967a` | **0.6178** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h14_n3_63082a7d` | **0.6176** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1273_c11d79fb` | **0.6167** | Normal | Standard transaction |
| `tx_norm_2435_e8dbbc1d` | **0.6166** | Normal | Standard transaction |
| `tx_peel_chain_c19_hop1_e326b3a5` | **0.6161** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_burst_layering_h3_n4_003df93a` | **0.6151** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1443_686f4128` | **0.6150** | Normal | Standard transaction |
| `tx_norm_1675_00687fd9` | **0.6123** | Normal | Standard transaction |
| `tx_norm_2538_11c43ded` | **0.6120** | Normal | Standard transaction |
| `tx_norm_1464_9a48d151` | **0.6119** | Normal | Standard transaction |
| `tx_peel_chain_c10_hop2_c6227ddf` | **0.6113** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_1538_c51cf2ea` | **0.6105** | Normal | Standard transaction |
| `tx_norm_235_38bb89fb` | **0.6097** | Normal | Standard transaction |
| `tx_tor_proxied_8_660cabf9` | **0.6095** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (08:00 UTC) |
| `tx_peel_chain_c14_hop3_f2aca5d2` | **0.6089** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_1127_d9b521e4` | **0.6085** | Normal | Standard transaction |
| `tx_burst_layering_h9_n3_70aa5dcf` | **0.6084** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_peel_chain_c12_hop1_b1ece0f4` | **0.6056** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_2126_837dd67b` | **0.6043** | Normal | Standard transaction |
| `tx_peel_chain_c14_hop2_ade85cd8` | **0.6041** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_1766_bf132e2b` | **0.6038** | Normal | Standard transaction |
| `tx_peel_chain_c5_hop4_58dfa12c` | **0.6033** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_burst_layering_h13_n0_e12cd549` | **0.6030** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_923_99051ca6` | **0.6024** | Normal | Standard transaction |
| `tx_burst_layering_h14_n1_75f58323` | **0.6022** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_tor_proxied_18_9aae1b08` | **0.6016** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (10:00 UTC) |
| `tx_peel_chain_c5_hop2_9fb7eedb` | **0.6015** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c12_hop3_ba21cbd8` | **0.6015** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_2594_670126c7` | **0.6014** | Normal | Standard transaction |
| `tx_peel_chain_c21_hop3_f5c6d9c5` | **0.6013** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_828_59425184` | **0.6012** | Normal | Standard transaction |
| `tx_whale_spike_11_17ddf15a` | **0.6008** | ✅ Anomaly | Amount 10.8918 BTC is >20x historical mean for sender 1751bc0fd076 |
| `tx_norm_583_631c716f` | **0.6008** | Normal | Standard transaction |
| `tx_whale_spike_55_1908ec47` | **0.6003** | ✅ Anomaly | Amount 14.9676 BTC is >20x historical mean for sender bc1qab77a781 |
| `tx_burst_layering_h1_n2_5a525c45` | **0.6001** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2127_84ee8e7e` | **0.5993** | Normal | Standard transaction |
| `tx_norm_1614_d27f67f3` | **0.5982** | Normal | Standard transaction |
| `tx_peel_chain_c12_hop2_c2a2287d` | **0.5967** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_burst_layering_h5_n2_bdb2cbc3` | **0.5961** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_peel_chain_c11_hop2_ca287dc8` | **0.5951** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c19_hop3_44a3bdec` | **0.5949** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_peel_chain_c11_hop1_b7f71a47` | **0.5942** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_peel_chain_c21_hop2_a2441158` | **0.5941** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_tor_proxied_17_6727d2b8` | **0.5926** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (13:00 UTC) |
| `tx_burst_layering_h5_n1_8b5c6a0b` | **0.5917** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_peel_chain_c5_hop1_006a6f75` | **0.5909** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_1462_eeb9469d` | **0.5907** | Normal | Standard transaction |
| `tx_norm_2284_faaedd5f` | **0.5902** | Normal | Standard transaction |
| `tx_peel_chain_c11_hop4_94bd38af` | **0.5881** | ✅ Anomaly | Hop 4 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_norm_930_4370a05a` | **0.5881** | Normal | Standard transaction |
| `tx_norm_2063_bdbc3326` | **0.5880** | Normal | Standard transaction |
| `tx_burst_layering_h2_n1_12eb10fb` | **0.5877** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_peel_chain_c21_hop1_4a496704` | **0.5872** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_peel_chain_c11_hop3_754ecc2d` | **0.5871** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1LaunderingHub... |
| `tx_burst_layering_h2_n3_413ecebc` | **0.5871** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2509_6241ea07` | **0.5871** | Normal | Standard transaction |
| `tx_peel_chain_c0_hop3_f0aa5d86` | **0.5867** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_burst_layering_h3_n0_198d28fe` | **0.5865** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1913_eb4fbae5` | **0.5865** | Normal | Standard transaction |
| `tx_norm_719_e92361b3` | **0.5855** | Normal | Standard transaction |
| `tx_norm_1364_b25eddf9` | **0.5841** | Normal | Standard transaction |
| `tx_norm_2151_c45d5636` | **0.5818** | Normal | Standard transaction |
| `tx_burst_layering_h11_n0_fdd276d7` | **0.5806** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_peel_chain_c19_hop2_60d037df` | **0.5804** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_tor_proxied_32_4d9be01b` | **0.5796** | ✅ Anomaly | Broadcast via Tor darknet proxy with cross-border hop at night (12:00 UTC) |
| `tx_norm_430_8dc80956` | **0.5792** | Normal | Standard transaction |
| `tx_peel_chain_c0_hop2_c40897de` | **0.5791** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_norm_284_a0606527` | **0.5791** | Normal | Standard transaction |
| `tx_burst_layering_h4_n3_34d26160` | **0.5787** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h13_n4_2d2cf42f` | **0.5784** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1516_05a876f8` | **0.5775** | Normal | Standard transaction |
| `tx_peel_chain_c6_hop1_413d35aa` | **0.5773** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_2330_4605c1b4` | **0.5770** | Normal | Standard transaction |
| `tx_norm_1676_fd1a6239` | **0.5762** | Normal | Standard transaction |
| `tx_norm_32_8748fa6d` | **0.5755** | Normal | Standard transaction |
| `tx_peel_chain_c20_hop1_2bee8d8a` | **0.5743** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_212_bbe0b821` | **0.5729** | Normal | Standard transaction |
| `tx_norm_734_0e5e36a1` | **0.5727** | Normal | Standard transaction |
| `tx_whale_spike_37_0911618e` | **0.5717** | ✅ Anomaly | Amount 16.8469 BTC is >20x historical mean for sender 17e4290e4fcf |
| `tx_peel_chain_c15_hop2_f632ccb6` | **0.5710** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_norm_1190_67c60b67` | **0.5704** | Normal | Standard transaction |
| `tx_norm_847_d1271949` | **0.5700** | Normal | Standard transaction |
| `tx_norm_130_e8b561f3` | **0.5698** | Normal | Standard transaction |
| `tx_peel_chain_c6_hop2_0438f351` | **0.5694** | ✅ Anomaly | Hop 2 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_2136_89447137` | **0.5690** | Normal | Standard transaction |
| `tx_peel_chain_c15_hop1_7cf05737` | **0.5687** | ✅ Anomaly | Hop 1 of peeling chain originated from seed illicit wallet 1DarknetMarket... |
| `tx_burst_layering_h0_n0_ba785b6f` | **0.5675** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1405_8d69fe30` | **0.5673** | Normal | Standard transaction |
| `tx_peel_chain_c7_hop3_45559423` | **0.5658** | ✅ Anomaly | Hop 3 of peeling chain originated from seed illicit wallet 1RansomwarePay... |
| `tx_norm_860_4acb1c04` | **0.5641** | Normal | Standard transaction |
| `tx_norm_1805_6dfffa2f` | **0.5635** | Normal | Standard transaction |
| `tx_norm_1940_0127e7fd` | **0.5627** | Normal | Standard transaction |
| `tx_norm_2610_76f130f7` | **0.5620** | Normal | Standard transaction |
| `tx_norm_800_cd5485a0` | **0.5607** | Normal | Standard transaction |
| `tx_norm_1587_0e8c08a7` | **0.5607** | Normal | Standard transaction |
| `tx_norm_987_4e4387d7` | **0.5603** | Normal | Standard transaction |
| `tx_burst_layering_h7_n0_8fce9eb6` | **0.5583** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h7_n2_442ddc23` | **0.5580** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h1_n4_be5836a1` | **0.5570** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2141_415f346b` | **0.5561** | Normal | Standard transaction |
| `tx_norm_621_b0fb4e3c` | **0.5557** | Normal | Standard transaction |
| `tx_norm_2329_94c9b353` | **0.5546** | Normal | Standard transaction |
| `tx_norm_1100_124de4d5` | **0.5530** | Normal | Standard transaction |
| `tx_norm_861_994e4c66` | **0.5529** | Normal | Standard transaction |
| `tx_norm_1890_bc35937f` | **0.5527** | Normal | Standard transaction |
| `tx_norm_1475_8b928614` | **0.5522** | Normal | Standard transaction |
| `tx_norm_2253_962a2908` | **0.5512** | Normal | Standard transaction |
| `tx_norm_2148_630e9a03` | **0.5501** | Normal | Standard transaction |
| `tx_norm_1694_08c58a40` | **0.5498** | Normal | Standard transaction |
| `tx_norm_970_a794ece3` | **0.5497** | Normal | Standard transaction |
| `tx_norm_2268_f5ab1bb4` | **0.5494** | Normal | Standard transaction |
| `tx_burst_layering_h15_n4_87fc9bf8` | **0.5482** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_516_c5155237` | **0.5476** | Normal | Standard transaction |
| `tx_norm_862_60479992` | **0.5467** | Normal | Standard transaction |
| `tx_norm_1544_e2c73db3` | **0.5464** | Normal | Standard transaction |
| `tx_norm_1271_b638bcd0` | **0.5456** | Normal | Standard transaction |
| `tx_norm_2012_2937e05d` | **0.5437** | Normal | Standard transaction |
| `tx_norm_201_a9ebadbc` | **0.5436** | Normal | Standard transaction |
| `tx_norm_2335_a1d0afc8` | **0.5422** | Normal | Standard transaction |
| `tx_norm_725_d0375418` | **0.5418** | Normal | Standard transaction |
| `tx_norm_727_a2a9fdd2` | **0.5418** | Normal | Standard transaction |
| `tx_burst_layering_h0_n3_fc1fd332` | **0.5401** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_97_215ff348` | **0.5399** | Normal | Standard transaction |
| `tx_burst_layering_h5_n0_3fa03785` | **0.5386** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h3_n2_5b59c21e` | **0.5379** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h1_n3_9c5a14eb` | **0.5371** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1820_635feb69` | **0.5349** | Normal | Standard transaction |
| `tx_norm_1565_e40b6177` | **0.5322** | Normal | Standard transaction |
| `tx_norm_2156_c39f8633` | **0.5319** | Normal | Standard transaction |
| `tx_norm_251_cd9619ba` | **0.5309** | Normal | Standard transaction |
| `tx_norm_2619_ade01d15` | **0.5303** | Normal | Standard transaction |
| `tx_norm_124_3be17676` | **0.5298** | Normal | Standard transaction |
| `tx_norm_906_d0ffc8e9` | **0.5288** | Normal | Standard transaction |
| `tx_burst_layering_h12_n4_42368be7` | **0.5278** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1152_3dcf751e` | **0.5272** | Normal | Standard transaction |
| `tx_norm_942_4bcf8b58` | **0.5271** | Normal | Standard transaction |
| `tx_norm_877_7c29ca04` | **0.5250** | Normal | Standard transaction |
| `tx_norm_900_9ce47de2` | **0.5247** | Normal | Standard transaction |
| `tx_burst_layering_h13_n3_16a2517a` | **0.5238** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h1_n0_ab983b61` | **0.5229** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h15_n3_12c6f262` | **0.5211** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_812_6b05b2d5` | **0.5206** | Normal | Standard transaction |
| `tx_norm_37_24fb43cd` | **0.5201** | Normal | Standard transaction |
| `tx_burst_layering_h0_n1_e8ec049b` | **0.5199** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2215_581b6f00` | **0.5189** | Normal | Standard transaction |
| `tx_norm_1343_adf9e31b` | **0.5182** | Normal | Standard transaction |
| `tx_norm_1138_818125d7` | **0.5179** | Normal | Standard transaction |
| `tx_norm_1596_04f73d5b` | **0.5178** | Normal | Standard transaction |
| `tx_norm_2352_10a8263f` | **0.5175** | Normal | Standard transaction |
| `tx_norm_2014_0f3d2ea9` | **0.5170** | Normal | Standard transaction |
| `tx_norm_1677_1de9b0f9` | **0.5169** | Normal | Standard transaction |
| `tx_norm_2024_0acf38b8` | **0.5160** | Normal | Standard transaction |
| `tx_burst_layering_h1_n1_3467280c` | **0.5154** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1920_f2c8051f` | **0.5154** | Normal | Standard transaction |
| `tx_norm_471_b4d13200` | **0.5152** | Normal | Standard transaction |
| `tx_norm_2321_6e9d284c` | **0.5150** | Normal | Standard transaction |
| `tx_norm_836_70b11550` | **0.5141** | Normal | Standard transaction |
| `tx_norm_2153_ed1dfde0` | **0.5140** | Normal | Standard transaction |
| `tx_norm_850_1ae05bdb` | **0.5138** | Normal | Standard transaction |
| `tx_norm_1485_39d97656` | **0.5128** | Normal | Standard transaction |
| `tx_norm_1822_47bf5820` | **0.5118** | Normal | Standard transaction |
| `tx_norm_1901_6146a3e4` | **0.5118** | Normal | Standard transaction |
| `tx_norm_934_c8279acf` | **0.5117** | Normal | Standard transaction |
| `tx_norm_1772_ced9ce73` | **0.5111** | Normal | Standard transaction |
| `tx_norm_94_b56ccd8f` | **0.5106** | Normal | Standard transaction |
| `tx_norm_320_f93e06d9` | **0.5102** | Normal | Standard transaction |
| `tx_norm_2423_5530465d` | **0.5102** | Normal | Standard transaction |
| `tx_norm_2089_a7e230a8` | **0.5097** | Normal | Standard transaction |
| `tx_norm_1635_f4200d26` | **0.5092** | Normal | Standard transaction |
| `tx_norm_971_b77c6b0c` | **0.5083** | Normal | Standard transaction |
| `tx_norm_2315_a7b92663` | **0.5078** | Normal | Standard transaction |
| `tx_norm_1068_68c2be78` | **0.5075** | Normal | Standard transaction |
| `tx_burst_layering_h9_n0_1aa09e50` | **0.5069** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h6_n4_dc76e8b3` | **0.5062** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_127_548acfc4` | **0.5046** | Normal | Standard transaction |
| `tx_norm_1525_18aeb845` | **0.5044** | Normal | Standard transaction |
| `tx_norm_1415_18db3bd7` | **0.5043** | Normal | Standard transaction |
| `tx_norm_549_6ecd0817` | **0.5042** | Normal | Standard transaction |
| `tx_norm_1116_abe82f92` | **0.5042** | Normal | Standard transaction |
| `tx_norm_2598_7ef6c2a6` | **0.5039** | Normal | Standard transaction |
| `tx_norm_698_62bb41b3` | **0.5035** | Normal | Standard transaction |
| `tx_norm_1542_3bb7ef9b` | **0.5033** | Normal | Standard transaction |
| `tx_burst_layering_h11_n4_a047cc3e` | **0.5009** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h11_n2_d468dd44` | **0.5005** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_442_23356fa3` | **0.4999** | Normal | Standard transaction |
| `tx_norm_753_2119809a` | **0.4999** | Normal | Standard transaction |
| `tx_norm_2328_a51bf67a` | **0.4995** | Normal | Standard transaction |
| `tx_norm_1582_b1a1f2eb` | **0.4988** | Normal | Standard transaction |
| `tx_norm_1445_c92dabc8` | **0.4957** | Normal | Standard transaction |
| `tx_norm_791_1f572bb7` | **0.4954** | Normal | Standard transaction |
| `tx_norm_2202_36640db5` | **0.4944** | Normal | Standard transaction |
| `tx_norm_2488_236a5cf0` | **0.4939** | Normal | Standard transaction |
| `tx_norm_523_eeb808bf` | **0.4937** | Normal | Standard transaction |
| `tx_norm_2106_fe921215` | **0.4937** | Normal | Standard transaction |
| `tx_norm_1345_5d06bd7c` | **0.4936** | Normal | Standard transaction |
| `tx_norm_2629_7f1cd4cc` | **0.4933** | Normal | Standard transaction |
| `tx_norm_796_850223ef` | **0.4930** | Normal | Standard transaction |
| `tx_norm_1665_798d39bc` | **0.4914** | Normal | Standard transaction |
| `tx_norm_2621_253688fe` | **0.4914** | Normal | Standard transaction |
| `tx_norm_1_83ec7045` | **0.4911** | Normal | Standard transaction |
| `tx_burst_layering_h6_n0_ea91edf9` | **0.4910** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2471_ec7dea22` | **0.4909** | Normal | Standard transaction |
| `tx_burst_layering_h10_n0_39913a27` | **0.4905** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2138_26f1adc8` | **0.4904** | Normal | Standard transaction |
| `tx_norm_2031_88ae87ed` | **0.4903** | Normal | Standard transaction |
| `tx_norm_297_777262c3` | **0.4900** | Normal | Standard transaction |
| `tx_norm_704_55b903fd` | **0.4900** | Normal | Standard transaction |
| `tx_norm_2244_a1b54b1d` | **0.4899** | Normal | Standard transaction |
| `tx_norm_1672_d145a474` | **0.4883** | Normal | Standard transaction |
| `tx_burst_layering_h6_n3_5c276539` | **0.4873** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_131_dc50fb85` | **0.4870** | Normal | Standard transaction |
| `tx_norm_922_0f4aa984` | **0.4870** | Normal | Standard transaction |
| `tx_norm_811_e9aef9ae` | **0.4855** | Normal | Standard transaction |
| `tx_norm_1844_4fee718e` | **0.4855** | Normal | Standard transaction |
| `tx_norm_690_e0e311f4` | **0.4846** | Normal | Standard transaction |
| `tx_norm_1041_2a282038` | **0.4844** | Normal | Standard transaction |
| `tx_norm_1685_c45579e1` | **0.4830** | Normal | Standard transaction |
| `tx_norm_1937_35d973b0` | **0.4822** | Normal | Standard transaction |
| `tx_norm_270_09e14b14` | **0.4819** | Normal | Standard transaction |
| `tx_norm_2179_2cd8a1ed` | **0.4808** | Normal | Standard transaction |
| `tx_norm_1030_39ebf174` | **0.4807** | Normal | Standard transaction |
| `tx_norm_57_381ab14f` | **0.4805** | Normal | Standard transaction |
| `tx_norm_314_1fd6e5bb` | **0.4805** | Normal | Standard transaction |
| `tx_burst_layering_h0_n2_f1f7beb3` | **0.4796** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_226_2d7317a1` | **0.4794** | Normal | Standard transaction |
| `tx_norm_2611_6169dbc2` | **0.4789** | Normal | Standard transaction |
| `tx_burst_layering_h8_n3_e5396f2c` | **0.4783** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1876_dc04dc25` | **0.4782** | Normal | Standard transaction |
| `tx_norm_1559_4302a7ad` | **0.4777** | Normal | Standard transaction |
| `tx_burst_layering_h3_n3_3dd91122` | **0.4774** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1744_aa9c2126` | **0.4774** | Normal | Standard transaction |
| `tx_norm_41_245a012b` | **0.4772** | Normal | Standard transaction |
| `tx_norm_2516_c57291f7` | **0.4772** | Normal | Standard transaction |
| `tx_burst_layering_h7_n1_77eaec83` | **0.4767** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_520_d447c810` | **0.4767** | Normal | Standard transaction |
| `tx_norm_2188_56795ca5` | **0.4767** | Normal | Standard transaction |
| `tx_norm_1740_a9409915` | **0.4758** | Normal | Standard transaction |
| `tx_burst_layering_h10_n2_d5c0a1a5` | **0.4752** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1574_c7ec4dca` | **0.4752** | Normal | Standard transaction |
| `tx_norm_1795_d2bf0459` | **0.4752** | Normal | Standard transaction |
| `tx_norm_2327_d57815cb` | **0.4752** | Normal | Standard transaction |
| `tx_norm_514_cfcfb497` | **0.4746** | Normal | Standard transaction |
| `tx_norm_287_06e45e60` | **0.4745** | Normal | Standard transaction |
| `tx_norm_1991_15eb44a2` | **0.4740** | Normal | Standard transaction |
| `tx_norm_1334_86c1b8ed` | **0.4730** | Normal | Standard transaction |
| `tx_norm_1637_606616a2` | **0.4724** | Normal | Standard transaction |
| `tx_norm_1477_9e76f2ff` | **0.4723** | Normal | Standard transaction |
| `tx_norm_679_9e294943` | **0.4720** | Normal | Standard transaction |
| `tx_norm_1782_553d739b` | **0.4717** | Normal | Standard transaction |
| `tx_norm_2033_09d5df66` | **0.4710** | Normal | Standard transaction |
| `tx_burst_layering_h11_n3_0310f96d` | **0.4706** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_42_d21e779d` | **0.4701** | Normal | Standard transaction |
| `tx_norm_179_8368e6ec` | **0.4701** | Normal | Standard transaction |
| `tx_norm_2369_b28e215a` | **0.4701** | Normal | Standard transaction |
| `tx_norm_2537_0184d3d6` | **0.4699** | Normal | Standard transaction |
| `tx_norm_1551_3ed1bbc7` | **0.4695** | Normal | Standard transaction |
| `tx_burst_layering_h4_n2_6040f992` | **0.4674** | ✅ Anomaly | High-frequency burst hop 3/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2119_becda4c2` | **0.4673** | Normal | Standard transaction |
| `tx_norm_984_cacb7979` | **0.4672** | Normal | Standard transaction |
| `tx_norm_1616_5faf861e` | **0.4667** | Normal | Standard transaction |
| `tx_norm_1689_464143bf` | **0.4667** | Normal | Standard transaction |
| `tx_norm_1717_81bec592` | **0.4663** | Normal | Standard transaction |
| `tx_norm_1058_799b07e9` | **0.4654** | Normal | Standard transaction |
| `tx_norm_2533_8e690184` | **0.4652** | Normal | Standard transaction |
| `tx_norm_1265_4ab486eb` | **0.4646** | Normal | Standard transaction |
| `tx_norm_1498_04a5725e` | **0.4641** | Normal | Standard transaction |
| `tx_norm_1745_c576f09b` | **0.4636** | Normal | Standard transaction |
| `tx_burst_layering_h5_n3_41b5705d` | **0.4630** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h3_n1_0ff23c5f` | **0.4616** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2499_e873623f` | **0.4614** | Normal | Standard transaction |
| `tx_norm_586_84fb08ed` | **0.4610** | Normal | Standard transaction |
| `tx_norm_1287_380bf2a4` | **0.4608** | Normal | Standard transaction |
| `tx_norm_408_34baa9a0` | **0.4596** | Normal | Standard transaction |
| `tx_norm_1651_2adf4761` | **0.4575** | Normal | Standard transaction |
| `tx_norm_1905_ec5060fc` | **0.4574** | Normal | Standard transaction |
| `tx_norm_1718_082f07d3` | **0.4573** | Normal | Standard transaction |
| `tx_burst_layering_h12_n3_ecfd39c4` | **0.4569** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2008_c48fb483` | **0.4560** | Normal | Standard transaction |
| `tx_norm_964_c78a51d2` | **0.4550** | Normal | Standard transaction |
| `tx_norm_1362_a394c85a` | **0.4550** | Normal | Standard transaction |
| `tx_norm_1258_d3238477` | **0.4549** | Normal | Standard transaction |
| `tx_norm_1663_0fce80bf` | **0.4548** | Normal | Standard transaction |
| `tx_norm_402_8f5aceb1` | **0.4547** | Normal | Standard transaction |
| `tx_norm_1354_924506b4` | **0.4547** | Normal | Standard transaction |
| `tx_norm_1577_ee2eed74` | **0.4545** | Normal | Standard transaction |
| `tx_norm_2271_cff9ab74` | **0.4539** | Normal | Standard transaction |
| `tx_norm_1988_c496e9c2` | **0.4535** | Normal | Standard transaction |
| `tx_norm_1888_07c879dc` | **0.4529** | Normal | Standard transaction |
| `tx_norm_1705_6e44d2ce` | **0.4525** | Normal | Standard transaction |
| `tx_norm_487_ddf24622` | **0.4524** | Normal | Standard transaction |
| `tx_norm_2283_a5100dfe` | **0.4524** | Normal | Standard transaction |
| `tx_norm_1386_e89dc7bb` | **0.4519** | Normal | Standard transaction |
| `tx_burst_layering_h8_n0_30cefd3c` | **0.4514** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_915_711c4bfd` | **0.4500** | Normal | Standard transaction |
| `tx_norm_2437_dce6f5e4` | **0.4492** | Normal | Standard transaction |
| `tx_norm_1661_540ce09d` | **0.4491** | Normal | Standard transaction |
| `tx_norm_438_20ca28fe` | **0.4489** | Normal | Standard transaction |
| `tx_burst_layering_h7_n3_b5f34eb6` | **0.4485** | ✅ Anomaly | High-frequency burst hop 4/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1514_6ac09949` | **0.4485** | Normal | Standard transaction |
| `tx_norm_1216_8d6e31e9` | **0.4481** | Normal | Standard transaction |
| `tx_burst_layering_h8_n4_bbd847a0` | **0.4478** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_546_0a847ed1` | **0.4477** | Normal | Standard transaction |
| `tx_norm_464_da268070` | **0.4475** | Normal | Standard transaction |
| `tx_norm_1280_c14c88a3` | **0.4472** | Normal | Standard transaction |
| `tx_norm_1010_9f2d598a` | **0.4469** | Normal | Standard transaction |
| `tx_burst_layering_h10_n1_4f6ad383` | **0.4464** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1147_b8eddbb0` | **0.4458** | Normal | Standard transaction |
| `tx_burst_layering_h11_n1_69d2d282` | **0.4456** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2527_2270e3f0` | **0.4455** | Normal | Standard transaction |
| `tx_norm_104_326fcd11` | **0.4449** | Normal | Standard transaction |
| `tx_norm_1701_b5e81c87` | **0.4446** | Normal | Standard transaction |
| `tx_norm_682_d1c2e1a4` | **0.4443** | Normal | Standard transaction |
| `tx_norm_7_4248aa5c` | **0.4440** | Normal | Standard transaction |
| `tx_norm_109_36e87b4f` | **0.4439** | Normal | Standard transaction |
| `tx_norm_2332_423cac1e` | **0.4436** | Normal | Standard transaction |
| `tx_norm_744_4359beb8` | **0.4434** | Normal | Standard transaction |
| `tx_norm_496_0ecb105d` | **0.4432** | Normal | Standard transaction |
| `tx_norm_2414_9cc94670` | **0.4428** | Normal | Standard transaction |
| `tx_norm_1370_5bea7a37` | **0.4423** | Normal | Standard transaction |
| `tx_norm_2442_d2ed6cbf` | **0.4417** | Normal | Standard transaction |
| `tx_norm_1755_55c5218f` | **0.4411** | Normal | Standard transaction |
| `tx_norm_145_a396e3eb` | **0.4406** | Normal | Standard transaction |
| `tx_norm_879_52401825` | **0.4406** | Normal | Standard transaction |
| `tx_burst_layering_h7_n4_57a546e5` | **0.4404** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1155_252cdd99` | **0.4404** | Normal | Standard transaction |
| `tx_burst_layering_h8_n1_56cba694` | **0.4399** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1291_21458d16` | **0.4398** | Normal | Standard transaction |
| `tx_burst_layering_h10_n4_6f66fd0f` | **0.4397** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_burst_layering_h4_n0_8ecc0da0` | **0.4387** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2462_c15be75c` | **0.4376** | Normal | Standard transaction |
| `tx_norm_1639_b5a5a7c0` | **0.4375** | Normal | Standard transaction |
| `tx_norm_2147_a4891420` | **0.4372** | Normal | Standard transaction |
| `tx_norm_1611_38f7e74b` | **0.4368** | Normal | Standard transaction |
| `tx_norm_656_c2887d39` | **0.4367** | Normal | Standard transaction |
| `tx_norm_1688_199038c5` | **0.4365** | Normal | Standard transaction |
| `tx_norm_240_0ea29877` | **0.4363** | Normal | Standard transaction |
| `tx_norm_519_59a9bc39` | **0.4357** | Normal | Standard transaction |
| `tx_burst_layering_h5_n4_f3c16820` | **0.4348** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_2434_b0a79656` | **0.4348** | Normal | Standard transaction |
| `tx_norm_869_4bdaf256` | **0.4347** | Normal | Standard transaction |
| `tx_norm_2030_83d441e0` | **0.4347** | Normal | Standard transaction |
| `tx_norm_2121_d7c8240c` | **0.4347** | Normal | Standard transaction |
| `tx_norm_1488_cdc02cec` | **0.4332** | Normal | Standard transaction |
| `tx_norm_1276_20fe1fd3` | **0.4328** | Normal | Standard transaction |
| `tx_norm_1680_4ace7145` | **0.4327** | Normal | Standard transaction |
| `tx_norm_1789_60db3a55` | **0.4320** | Normal | Standard transaction |
| `tx_norm_1496_d19fcf15` | **0.4315** | Normal | Standard transaction |
| `tx_norm_1837_02f3fafd` | **0.4313** | Normal | Standard transaction |
| `tx_norm_985_317d8d09` | **0.4312** | Normal | Standard transaction |
| `tx_norm_2404_288f6504` | **0.4312** | Normal | Standard transaction |
| `tx_norm_417_2f2626e3` | **0.4310** | Normal | Standard transaction |
| `tx_norm_2142_1881cd13` | **0.4304** | Normal | Standard transaction |
| `tx_norm_394_39e970af` | **0.4297** | Normal | Standard transaction |
| `tx_norm_2099_42a430cc` | **0.4283** | Normal | Standard transaction |
| `tx_norm_1056_d0ddc979` | **0.4280** | Normal | Standard transaction |
| `tx_norm_437_adfd8609` | **0.4279** | Normal | Standard transaction |
| `tx_norm_2630_64011d5a` | **0.4277** | Normal | Standard transaction |
| `tx_norm_1824_443c06ac` | **0.4276** | Normal | Standard transaction |
| `tx_norm_308_1930edda` | **0.4273** | Normal | Standard transaction |
| `tx_norm_2222_3429d1f3` | **0.4268** | Normal | Standard transaction |
| `tx_norm_2041_cebb84d5` | **0.4261** | Normal | Standard transaction |
| `tx_norm_310_3162601c` | **0.4257** | Normal | Standard transaction |
| `tx_norm_1626_2f8c026d` | **0.4250** | Normal | Standard transaction |
| `tx_burst_layering_h4_n4_0a3f05ba` | **0.4241** | ✅ Anomaly | High-frequency burst hop 5/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_967_2c03a503` | **0.4239** | Normal | Standard transaction |
| `tx_norm_1115_6d40c852` | **0.4239** | Normal | Standard transaction |
| `tx_norm_1547_dda25264` | **0.4239** | Normal | Standard transaction |
| `tx_norm_1588_0daad65d` | **0.4228** | Normal | Standard transaction |
| `tx_norm_695_152ce952` | **0.4210** | Normal | Standard transaction |
| `tx_burst_layering_h12_n0_e12fa4a9` | **0.4207** | ✅ Anomaly | High-frequency burst hop 1/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1017_3bb32715` | **0.4204** | Normal | Standard transaction |
| `tx_norm_855_da177d45` | **0.4203** | Normal | Standard transaction |
| `tx_norm_1931_92758099` | **0.4201** | Normal | Standard transaction |
| `tx_norm_1983_d907b57c` | **0.4190** | Normal | Standard transaction |
| `tx_norm_894_ee4a56c4` | **0.4186** | Normal | Standard transaction |
| `tx_norm_2378_2da9b352` | **0.4186** | Normal | Standard transaction |
| `tx_norm_1434_10573182` | **0.4183** | Normal | Standard transaction |
| `tx_norm_1383_3e2afbf4` | **0.4175** | Normal | Standard transaction |
| `tx_norm_2211_470a6f1f` | **0.4175** | Normal | Standard transaction |
| `tx_norm_2152_b2058b32` | **0.4174** | Normal | Standard transaction |
| `tx_norm_581_e21d407b` | **0.4171** | Normal | Standard transaction |
| `tx_norm_263_f2ce5207` | **0.4170** | Normal | Standard transaction |
| `tx_norm_1607_e8beb84f` | **0.4157** | Normal | Standard transaction |
| `tx_norm_371_6ced4fc5` | **0.4155** | Normal | Standard transaction |
| `tx_norm_2208_aaff8f62` | **0.4151** | Normal | Standard transaction |
| `tx_norm_1421_dbf821df` | **0.4149** | Normal | Standard transaction |
| `tx_norm_1264_f2ce7d6e` | **0.4141** | Normal | Standard transaction |
| `tx_norm_25_3b045d19` | **0.4139** | Normal | Standard transaction |
| `tx_norm_2395_c202db10` | **0.4136** | Normal | Standard transaction |
| `tx_norm_568_4ca2cc17` | **0.4132** | Normal | Standard transaction |
| `tx_norm_1085_b2448d61` | **0.4131** | Normal | Standard transaction |
| `tx_norm_2489_338e1172` | **0.4123** | Normal | Standard transaction |
| `tx_norm_1011_be201eb0` | **0.4118** | Normal | Standard transaction |
| `tx_norm_742_f83d2849` | **0.4113** | Normal | Standard transaction |
| `tx_norm_1519_47730b24` | **0.4107** | Normal | Standard transaction |
| `tx_norm_1524_d05879ed` | **0.4097** | Normal | Standard transaction |
| `tx_norm_267_473c17ab` | **0.4082** | Normal | Standard transaction |
| `tx_norm_687_bcd50b0b` | **0.4080** | Normal | Standard transaction |
| `tx_norm_1195_928c347d` | **0.4068** | Normal | Standard transaction |
| `tx_norm_1417_37bb6aa3` | **0.4067** | Normal | Standard transaction |
| `tx_norm_2052_8324eed3` | **0.4064** | Normal | Standard transaction |
| `tx_norm_291_7a0713a3` | **0.4062** | Normal | Standard transaction |
| `tx_norm_68_a9533d9f` | **0.4060** | Normal | Standard transaction |
| `tx_norm_515_ac5df042` | **0.4060** | Normal | Standard transaction |
| `tx_norm_2091_1c4c67f4` | **0.4059** | Normal | Standard transaction |
| `tx_norm_881_0f3b0ca6` | **0.4054** | Normal | Standard transaction |
| `tx_norm_2238_573d5f41` | **0.4050** | Normal | Standard transaction |
| `tx_norm_461_7ee14bc8` | **0.4044** | Normal | Standard transaction |
| `tx_norm_1425_e00df99b` | **0.4044** | Normal | Standard transaction |
| `tx_norm_613_e373c21d` | **0.4043** | Normal | Standard transaction |
| `tx_norm_2_82c2cd54` | **0.4027** | Normal | Standard transaction |
| `tx_norm_2021_94a97c7d` | **0.4025** | Normal | Standard transaction |
| `tx_norm_2203_a71ca5ee` | **0.4021** | Normal | Standard transaction |
| `tx_burst_layering_h12_n1_3209d94a` | **0.4020** | ✅ Anomaly | High-frequency burst hop 2/5 from hub 1RapidLayerHub within 30 minutes |
| `tx_norm_1883_9bef04da` | **0.4018** | Normal | Standard transaction |
| `tx_norm_2438_4e326da0` | **0.4017** | Normal | Standard transaction |
| `tx_norm_2559_cbef8652` | **0.4016** | Normal | Standard transaction |
| `tx_norm_211_7dfd4282` | **0.4015** | Normal | Standard transaction |
| `tx_norm_1909_1ae94c0a` | **0.4006** | Normal | Standard transaction |
| `tx_norm_1612_8d6b1280` | **0.4003** | Normal | Standard transaction |
| `tx_norm_1057_a5bb579b` | **0.4000** | Normal | Standard transaction |
| `tx_norm_34_f073c9e9` | **0.3995** | Normal | Standard transaction |
| `tx_norm_1123_46763312` | **0.3992** | Normal | Standard transaction |
| `tx_norm_2518_3d798eef` | **0.3985** | Normal | Standard transaction |
| `tx_norm_1303_f728bd4e` | **0.3983** | Normal | Standard transaction |
| `tx_norm_2520_26afc091` | **0.3974** | Normal | Standard transaction |
| `tx_norm_2612_fd86c04e` | **0.3963** | Normal | Standard transaction |
| `tx_norm_2600_807e426a` | **0.3962** | Normal | Standard transaction |
| `tx_norm_2049_7364df4a` | **0.3957** | Normal | Standard transaction |
| `tx_norm_387_275907e1` | **0.3955** | Normal | Standard transaction |
| `tx_norm_2428_9eef3e14` | **0.3953** | Normal | Standard transaction |
| `tx_norm_1054_53adb8d9` | **0.3947** | Normal | Standard transaction |
| `tx_norm_949_8b22e755` | **0.3946** | Normal | Standard transaction |
| `tx_norm_275_21b2fd26` | **0.3942** | Normal | Standard transaction |
| `tx_norm_1760_1a27dde0` | **0.3940** | Normal | Standard transaction |
| `tx_norm_2432_adbe7e07` | **0.3938** | Normal | Standard transaction |
| `tx_norm_718_0344c4d2` | **0.3933** | Normal | Standard transaction |
| `tx_norm_1397_91a10fee` | **0.3927** | Normal | Standard transaction |
| `tx_norm_1986_7a72db8c` | **0.3926** | Normal | Standard transaction |
| `tx_norm_1036_179db67b` | **0.3919** | Normal | Standard transaction |
| `tx_norm_1080_8b94e586` | **0.3912** | Normal | Standard transaction |
| `tx_norm_423_977dc974` | **0.3908** | Normal | Standard transaction |
| `tx_norm_1916_e9a1a1b2` | **0.3904** | Normal | Standard transaction |
| `tx_norm_2577_7ec62cdb` | **0.3900** | Normal | Standard transaction |
| `tx_norm_2190_946ceb0c` | **0.3896** | Normal | Standard transaction |
| `tx_norm_1853_1975515f` | **0.3895** | Normal | Standard transaction |
| `tx_norm_1895_026b219d` | **0.3895** | Normal | Standard transaction |
| `tx_norm_1173_74f06c26` | **0.3891** | Normal | Standard transaction |
| `tx_norm_994_77e13d6f` | **0.3886** | Normal | Standard transaction |
| `tx_norm_2083_700e2242` | **0.3886** | Normal | Standard transaction |
| `tx_norm_2293_ab896110` | **0.3883** | Normal | Standard transaction |
| `tx_norm_1133_2eecc905` | **0.3882** | Normal | Standard transaction |
| `tx_norm_1188_67be678f` | **0.3876** | Normal | Standard transaction |
| `tx_norm_1483_a1574c98` | **0.3876** | Normal | Standard transaction |
| `tx_norm_319_9a1f1412` | **0.3869** | Normal | Standard transaction |
| `tx_norm_203_b3f28bc8` | **0.3866** | Normal | Standard transaction |
| `tx_norm_338_9901d0f2` | **0.3861** | Normal | Standard transaction |
| `tx_norm_1632_5a05cef3` | **0.3860** | Normal | Standard transaction |
| `tx_norm_2292_3162d20e` | **0.3860** | Normal | Standard transaction |
| `tx_norm_140_5022c7fb` | **0.3858** | Normal | Standard transaction |
| `tx_norm_2266_20de21bd` | **0.3858** | Normal | Standard transaction |
| `tx_norm_574_a2bad8f4` | **0.3853** | Normal | Standard transaction |
| `tx_norm_1529_eb7885cc` | **0.3848** | Normal | Standard transaction |
| `tx_norm_681_19827c2c` | **0.3847** | Normal | Standard transaction |
| `tx_norm_784_8ff88c93` | **0.3835** | Normal | Standard transaction |
| `tx_norm_2294_107c1e3f` | **0.3830** | Normal | Standard transaction |
| `tx_norm_2562_252786c9` | **0.3825** | Normal | Standard transaction |
| `tx_norm_288_142b0bcf` | **0.3823** | Normal | Standard transaction |
| `tx_norm_2323_11f08571` | **0.3823** | Normal | Standard transaction |
| `tx_norm_853_876b6e28` | **0.3820** | Normal | Standard transaction |
| `tx_norm_117_322595f7` | **0.3819** | Normal | Standard transaction |
| `tx_norm_2239_9ef82abd` | **0.3819** | Normal | Standard transaction |
| `tx_norm_2449_119a9eb9` | **0.3818** | Normal | Standard transaction |
| `tx_norm_1835_5f02c634` | **0.3817** | Normal | Standard transaction |
| `tx_norm_2254_6fe54d00` | **0.3814** | Normal | Standard transaction |
| `tx_norm_666_66e405b2` | **0.3811** | Normal | Standard transaction |
| `tx_norm_1707_d724a232` | **0.3810** | Normal | Standard transaction |
| `tx_norm_1028_c3752208` | **0.3805** | Normal | Standard transaction |
| `tx_norm_535_36c4508a` | **0.3802** | Normal | Standard transaction |
| `tx_norm_2131_5f76b2b9` | **0.3801** | Normal | Standard transaction |
| `tx_norm_740_cc86f544` | **0.3799** | Normal | Standard transaction |
| `tx_norm_1211_bae586f3` | **0.3796** | Normal | Standard transaction |
| `tx_norm_569_bb483cca` | **0.3792** | Normal | Standard transaction |
| `tx_norm_2316_7c1463d3` | **0.3790** | Normal | Standard transaction |
| `tx_norm_184_6c5808c6` | **0.3789** | Normal | Standard transaction |
| `tx_norm_1990_0d983b82` | **0.3787** | Normal | Standard transaction |
| `tx_norm_1330_cb756769` | **0.3781** | Normal | Standard transaction |
| `tx_norm_2278_c674b4c8` | **0.3780** | Normal | Standard transaction |
| `tx_norm_405_8ae5f788` | **0.3772** | Normal | Standard transaction |
| `tx_norm_1009_d9294211` | **0.3772** | Normal | Standard transaction |
| `tx_norm_2502_017fbb07` | **0.3766** | Normal | Standard transaction |
| `tx_norm_1645_26b82e79` | **0.3764** | Normal | Standard transaction |
| `tx_norm_2168_cb6f1cf3` | **0.3750** | Normal | Standard transaction |
| `tx_norm_2580_1e19f6ad` | **0.3749** | Normal | Standard transaction |
| `tx_norm_1414_dc20d4ee` | **0.3745** | Normal | Standard transaction |
| `tx_norm_81_d1535405` | **0.3744** | Normal | Standard transaction |
| `tx_norm_466_0d37c6f2` | **0.3739** | Normal | Standard transaction |
| `tx_norm_635_74b6db1d` | **0.3737** | Normal | Standard transaction |
| `tx_norm_368_5a6f7e5e` | **0.3736** | Normal | Standard transaction |
| `tx_norm_1627_6421f487` | **0.3733** | Normal | Standard transaction |
| `tx_norm_1221_96c6debe` | **0.3726** | Normal | Standard transaction |
| `tx_norm_1594_f705a58b` | **0.3726** | Normal | Standard transaction |
| `tx_norm_655_6cfeedd3` | **0.3724** | Normal | Standard transaction |
| `tx_norm_761_282cdf9f` | **0.3723** | Normal | Standard transaction |
| `tx_norm_2367_40092bc8` | **0.3718** | Normal | Standard transaction |
| `tx_norm_2388_5b01dd6b` | **0.3699** | Normal | Standard transaction |
| `tx_norm_702_8160ee10` | **0.3697** | Normal | Standard transaction |
| `tx_norm_1834_1f3504db` | **0.3697** | Normal | Standard transaction |
| `tx_norm_2473_99e2a4d6` | **0.3693** | Normal | Standard transaction |
| `tx_norm_1796_b6259ee0` | **0.3691** | Normal | Standard transaction |
| `tx_norm_1950_2f222f42` | **0.3687** | Normal | Standard transaction |
| `tx_norm_177_c98de43d` | **0.3684** | Normal | Standard transaction |
| `tx_norm_372_61c4f149` | **0.3677** | Normal | Standard transaction |
| `tx_norm_509_cd74ed62` | **0.3676** | Normal | Standard transaction |
| `tx_norm_912_5f15fa5e` | **0.3676** | Normal | Standard transaction |
| `tx_norm_216_18b6a20d` | **0.3674** | Normal | Standard transaction |
| `tx_norm_932_c423c721` | **0.3673** | Normal | Standard transaction |
| `tx_norm_783_0e4b5071` | **0.3671** | Normal | Standard transaction |
| `tx_norm_1669_aedc9c7d` | **0.3671** | Normal | Standard transaction |
| `tx_norm_2061_247ec5d7` | **0.3668** | Normal | Standard transaction |
| `tx_norm_476_65fa729d` | **0.3661** | Normal | Standard transaction |
| `tx_norm_731_698d2524` | **0.3661** | Normal | Standard transaction |
| `tx_norm_1371_b0e34fa4` | **0.3661** | Normal | Standard transaction |
| `tx_norm_979_2b8c6c71` | **0.3655** | Normal | Standard transaction |
| `tx_norm_887_46a60ece` | **0.3654** | Normal | Standard transaction |
| `tx_norm_231_114c1615` | **0.3649** | Normal | Standard transaction |
| `tx_norm_344_ffa48ac9` | **0.3646** | Normal | Standard transaction |
| `tx_norm_1679_2995d8ac` | **0.3646** | Normal | Standard transaction |
| `tx_norm_2044_e84a297d` | **0.3645** | Normal | Standard transaction |
| `tx_norm_1266_0e35c17d` | **0.3642** | Normal | Standard transaction |
| `tx_norm_2436_efda2b0a` | **0.3640** | Normal | Standard transaction |
| `tx_norm_2599_a9c57838` | **0.3640** | Normal | Standard transaction |
| `tx_norm_1621_6ab3f91f` | **0.3637** | Normal | Standard transaction |
| `tx_norm_2074_426d4719` | **0.3631** | Normal | Standard transaction |
| `tx_norm_119_308219b8` | **0.3622** | Normal | Standard transaction |
| `tx_norm_815_ba18d757` | **0.3622** | Normal | Standard transaction |
| `tx_norm_350_e201d557` | **0.3620** | Normal | Standard transaction |
| `tx_norm_192_a2435b1d` | **0.3617** | Normal | Standard transaction |
| `tx_norm_2334_a0cba979` | **0.3611** | Normal | Standard transaction |
| `tx_norm_1742_1722935d` | **0.3606** | Normal | Standard transaction |
| `tx_norm_54_a86f9d98` | **0.3597** | Normal | Standard transaction |
| `tx_norm_1827_e4d65c6a` | **0.3595** | Normal | Standard transaction |
| `tx_norm_469_df471ae0` | **0.3591** | Normal | Standard transaction |
| `tx_norm_891_f4cd7ec4` | **0.3589** | Normal | Standard transaction |
| `tx_norm_1360_db33cb23` | **0.3587** | Normal | Standard transaction |
| `tx_norm_18_7dd3eb8b` | **0.3585** | Normal | Standard transaction |
| `tx_norm_204_f039f4ea` | **0.3584** | Normal | Standard transaction |
| `tx_norm_630_59efcc66` | **0.3582** | Normal | Standard transaction |
| `tx_norm_864_bdd8c7ce` | **0.3579** | Normal | Standard transaction |
| `tx_norm_2419_80c6d85a` | **0.3579** | Normal | Standard transaction |
| `tx_norm_66_6497cc92` | **0.3578** | Normal | Standard transaction |
| `tx_norm_2524_301463f8` | **0.3574** | Normal | Standard transaction |
| `tx_norm_789_075c99a6` | **0.3573** | Normal | Standard transaction |
| `tx_norm_389_abfd4624` | **0.3563** | Normal | Standard transaction |
| `tx_norm_1736_065e4097` | **0.3558** | Normal | Standard transaction |
| `tx_norm_1479_223e72c8` | **0.3555** | Normal | Standard transaction |
| `tx_norm_1994_1b3476bf` | **0.3553** | Normal | Standard transaction |
| `tx_norm_1340_989de39d` | **0.3551** | Normal | Standard transaction |
| `tx_norm_2038_a6f6c588` | **0.3547** | Normal | Standard transaction |
| `tx_norm_1452_2eb64654` | **0.3546** | Normal | Standard transaction |
| `tx_norm_2055_ccc55a34` | **0.3537** | Normal | Standard transaction |
| `tx_norm_2385_41d45d1a` | **0.3536** | Normal | Standard transaction |
| `tx_norm_743_37b86526` | **0.3530** | Normal | Standard transaction |
| `tx_norm_1788_70f7e0d8` | **0.3527** | Normal | Standard transaction |
| `tx_norm_2144_d8e6fe9d` | **0.3525** | Normal | Standard transaction |
| `tx_norm_103_bc9536b8` | **0.3522** | Normal | Standard transaction |
| `tx_norm_1215_4c775cfd` | **0.3520** | Normal | Standard transaction |
| `tx_norm_660_c230c1ef` | **0.3517** | Normal | Standard transaction |
| `tx_norm_958_ec113887` | **0.3517** | Normal | Standard transaction |
| `tx_norm_1892_a25160d2` | **0.3517** | Normal | Standard transaction |
| `tx_norm_432_17a46ad3` | **0.3516** | Normal | Standard transaction |
| `tx_norm_1847_1272aa48` | **0.3516** | Normal | Standard transaction |
| `tx_norm_2529_102f0c99` | **0.3514** | Normal | Standard transaction |
| `tx_norm_578_9c67d1ce` | **0.3507** | Normal | Standard transaction |
| `tx_norm_83_196c8c5f` | **0.3503** | Normal | Standard transaction |
| `tx_norm_2289_d0332da3` | **0.3497** | Normal | Standard transaction |
| `tx_norm_247_840f84e8` | **0.3496** | Normal | Standard transaction |
| `tx_norm_1855_2bede75a` | **0.3495** | Normal | Standard transaction |
| `tx_norm_1713_9e839b4a` | **0.3489** | Normal | Standard transaction |
| `tx_norm_1081_60a597d6` | **0.3487** | Normal | Standard transaction |
| `tx_norm_1322_0e145359` | **0.3481** | Normal | Standard transaction |
| `tx_norm_1314_29aa69bd` | **0.3475** | Normal | Standard transaction |
| `tx_norm_2068_44f0185d` | **0.3475** | Normal | Standard transaction |
| `tx_norm_1411_dd1d2f4c` | **0.3470** | Normal | Standard transaction |
| `tx_norm_1829_a6a2f7ad` | **0.3468** | Normal | Standard transaction |
| `tx_norm_1527_a5514798` | **0.3463** | Normal | Standard transaction |
| `tx_norm_1395_15bbb79b` | **0.3461** | Normal | Standard transaction |
| `tx_norm_1317_9496e0d3` | **0.3457** | Normal | Standard transaction |
| `tx_norm_1048_b2659f3c` | **0.3454** | Normal | Standard transaction |
| `tx_norm_79_a6b2f523` | **0.3449** | Normal | Standard transaction |
| `tx_norm_721_2dfd23aa` | **0.3448** | Normal | Standard transaction |
| `tx_norm_1268_d680ca47` | **0.3446** | Normal | Standard transaction |
| `tx_norm_1005_0913985a` | **0.3443** | Normal | Standard transaction |
| `tx_norm_1175_618006ac` | **0.3438** | Normal | Standard transaction |
| `tx_norm_2157_13a8ea7d` | **0.3435** | Normal | Standard transaction |
| `tx_norm_120_ce3be845` | **0.3432** | Normal | Standard transaction |
| `tx_norm_1863_2b40bfee` | **0.3432** | Normal | Standard transaction |
| `tx_norm_2456_1b1ad3c6` | **0.3431** | Normal | Standard transaction |
| `tx_norm_941_b309f1dd` | **0.3430** | Normal | Standard transaction |
| `tx_norm_1073_14f4ba95` | **0.3430** | Normal | Standard transaction |
| `tx_norm_1113_c9c4727e` | **0.3429** | Normal | Standard transaction |
| `tx_norm_1539_6246ca31` | **0.3427** | Normal | Standard transaction |
| `tx_norm_1704_2d47f8a9` | **0.3426** | Normal | Standard transaction |
| `tx_norm_1142_c44a5e22` | **0.3421** | Normal | Standard transaction |
| `tx_norm_965_4874c7ee` | **0.3408** | Normal | Standard transaction |
| `tx_norm_1181_b2035a07` | **0.3408** | Normal | Standard transaction |
| `tx_norm_1810_89040585` | **0.3407** | Normal | Standard transaction |
| `tx_norm_849_3eca610c` | **0.3406** | Normal | Standard transaction |
| `tx_norm_2078_38379da8` | **0.3406** | Normal | Standard transaction |
| `tx_norm_190_a25589fd` | **0.3404** | Normal | Standard transaction |
| `tx_norm_479_1bc58a8f` | **0.3403** | Normal | Standard transaction |
| `tx_norm_795_b4818a5b` | **0.3400** | Normal | Standard transaction |
| `tx_norm_1353_dc269f14` | **0.3400** | Normal | Standard transaction |
| `tx_norm_463_aefe5327` | **0.3395** | Normal | Standard transaction |
| `tx_norm_2574_4a3b9cdc` | **0.3395** | Normal | Standard transaction |
| `tx_norm_2534_02a6c7f8` | **0.3387** | Normal | Standard transaction |
| `tx_norm_757_41299a19` | **0.3382** | Normal | Standard transaction |
| `tx_norm_16_d685c6b6` | **0.3381** | Normal | Standard transaction |
| `tx_norm_1976_cdf53a4f` | **0.3381** | Normal | Standard transaction |
| `tx_norm_1321_a1eb5b47` | **0.3379** | Normal | Standard transaction |
| `tx_norm_2616_f3a8324e` | **0.3379** | Normal | Standard transaction |
| `tx_norm_385_329fe209` | **0.3375** | Normal | Standard transaction |
| `tx_norm_1915_2d44fb48` | **0.3374** | Normal | Standard transaction |
| `tx_norm_261_f7b4c795` | **0.3373** | Normal | Standard transaction |
| `tx_norm_705_1e758790` | **0.3368** | Normal | Standard transaction |
| `tx_norm_1065_78df3650` | **0.3366** | Normal | Standard transaction |
| `tx_norm_1089_fa5a003b` | **0.3366** | Normal | Standard transaction |
| `tx_norm_2248_adac95ef` | **0.3365** | Normal | Standard transaction |
| `tx_norm_2379_7c26068f` | **0.3365** | Normal | Standard transaction |
| `tx_norm_1325_0e7a3c73` | **0.3359** | Normal | Standard transaction |
| `tx_norm_1610_d568a030` | **0.3345** | Normal | Standard transaction |
| `tx_norm_1759_fd9250fc` | **0.3342** | Normal | Standard transaction |
| `tx_norm_2427_5835335d` | **0.3342** | Normal | Standard transaction |
| `tx_norm_1310_ce5a5a04` | **0.3337** | Normal | Standard transaction |
| `tx_norm_1640_966ed073` | **0.3336** | Normal | Standard transaction |
| `tx_norm_565_7ac41551` | **0.3334** | Normal | Standard transaction |
| `tx_norm_2381_cb7c6225` | **0.3329** | Normal | Standard transaction |
| `tx_norm_2165_231e808d` | **0.3327** | Normal | Standard transaction |
| `tx_norm_1286_5d16c566` | **0.3324** | Normal | Standard transaction |
| `tx_norm_1240_ceb70469` | **0.3323** | Normal | Standard transaction |
| `tx_norm_680_b4b4cb7b` | **0.3322** | Normal | Standard transaction |
| `tx_norm_1424_903bd91f` | **0.3318** | Normal | Standard transaction |
| `tx_norm_1897_69dd07b1` | **0.3314** | Normal | Standard transaction |
| `tx_norm_1449_ded622ab` | **0.3310** | Normal | Standard transaction |
| `tx_norm_2457_4f72a29d` | **0.3309** | Normal | Standard transaction |
| `tx_norm_1121_aef8dc13` | **0.3305** | Normal | Standard transaction |
| `tx_norm_1832_c8fd00ec` | **0.3304** | Normal | Standard transaction |
| `tx_norm_494_13a16a63` | **0.3301** | Normal | Standard transaction |
| `tx_norm_1510_b1504955` | **0.3298** | Normal | Standard transaction |
| `tx_norm_708_34d2da06` | **0.3294** | Normal | Standard transaction |
| `tx_norm_404_fd087316` | **0.3293** | Normal | Standard transaction |
| `tx_norm_1799_811fa82b` | **0.3292** | Normal | Standard transaction |
| `tx_norm_2117_c787a947` | **0.3292** | Normal | Standard transaction |
| `tx_norm_771_04c0608c` | **0.3285** | Normal | Standard transaction |
| `tx_norm_1974_a86d4fa8` | **0.3284** | Normal | Standard transaction |
| `tx_norm_14_137e8649` | **0.3280** | Normal | Standard transaction |
| `tx_norm_2264_261453d4` | **0.3277** | Normal | Standard transaction |
| `tx_norm_858_8aa8a0eb` | **0.3276** | Normal | Standard transaction |
| `tx_norm_331_3607a173` | **0.3275** | Normal | Standard transaction |
| `tx_norm_1075_ea8b83a8` | **0.3275** | Normal | Standard transaction |
| `tx_norm_38_959d470d` | **0.3272** | Normal | Standard transaction |
| `tx_norm_2433_1f87b507` | **0.3272** | Normal | Standard transaction |
| `tx_norm_1891_0821372e` | **0.3269** | Normal | Standard transaction |
| `tx_norm_49_320e8832` | **0.3267** | Normal | Standard transaction |
| `tx_norm_1756_14817c73` | **0.3266** | Normal | Standard transaction |
| `tx_norm_450_ec8bd796` | **0.3263** | Normal | Standard transaction |
| `tx_norm_2295_c0f66ede` | **0.3263** | Normal | Standard transaction |
| `tx_norm_2391_01f3ce48` | **0.3263** | Normal | Standard transaction |
| `tx_norm_1997_8cb7cc0a` | **0.3255** | Normal | Standard transaction |
| `tx_norm_342_0b220cdc` | **0.3250** | Normal | Standard transaction |
| `tx_norm_101_c14a13ee` | **0.3246** | Normal | Standard transaction |
| `tx_norm_1399_9be0140b` | **0.3246** | Normal | Standard transaction |
| `tx_norm_883_8c7abfa2` | **0.3245** | Normal | Standard transaction |
| `tx_norm_193_316e5fe1` | **0.3242** | Normal | Standard transaction |
| `tx_norm_1656_f2200dea` | **0.3242** | Normal | Standard transaction |
| `tx_norm_1534_c0078a2d` | **0.3241** | Normal | Standard transaction |
| `tx_norm_919_c5c3d099` | **0.3236** | Normal | Standard transaction |
| `tx_norm_2485_86fb8690` | **0.3235** | Normal | Standard transaction |
| `tx_norm_2218_93e32fc3` | **0.3233** | Normal | Standard transaction |
| `tx_norm_272_c8f3ccc4` | **0.3231** | Normal | Standard transaction |
| `tx_norm_1025_97be71f5` | **0.3229** | Normal | Standard transaction |
| `tx_norm_1350_3a1536c8` | **0.3226** | Normal | Standard transaction |
| `tx_norm_782_b69504db` | **0.3223** | Normal | Standard transaction |
| `tx_norm_2522_6bc4f737` | **0.3223** | Normal | Standard transaction |
| `tx_norm_2120_7a78c484` | **0.3222** | Normal | Standard transaction |
| `tx_norm_2276_b48ca779` | **0.3215** | Normal | Standard transaction |
| `tx_norm_1246_55a2de25` | **0.3212** | Normal | Standard transaction |
| `tx_norm_64_695d8244` | **0.3211** | Normal | Standard transaction |
| `tx_norm_1825_6d55c615` | **0.3211** | Normal | Standard transaction |
| `tx_norm_1575_32d5a4a4` | **0.3210** | Normal | Standard transaction |
| `tx_norm_299_4a96ad34` | **0.3206** | Normal | Standard transaction |
| `tx_norm_1319_fa79fd10` | **0.3200** | Normal | Standard transaction |
| `tx_norm_191_fa8bb7cd` | **0.3197** | Normal | Standard transaction |
| `tx_norm_1684_5efa9cba` | **0.3194** | Normal | Standard transaction |
| `tx_norm_1733_59de2a36` | **0.3194** | Normal | Standard transaction |
| `tx_norm_1981_bf2ce01a` | **0.3190** | Normal | Standard transaction |
| `tx_norm_2275_3e9cd20c` | **0.3190** | Normal | Standard transaction |
| `tx_norm_45_f730fe4f` | **0.3189** | Normal | Standard transaction |
| `tx_norm_2425_fe3bb624` | **0.3189** | Normal | Standard transaction |
| `tx_norm_2288_d8714cd3` | **0.3188** | Normal | Standard transaction |
| `tx_norm_978_d53f0efb` | **0.3181** | Normal | Standard transaction |
| `tx_norm_2023_3a965446` | **0.3179** | Normal | Standard transaction |
| `tx_norm_285_a95fdb1f` | **0.3177** | Normal | Standard transaction |
| `tx_norm_1869_b31fee61` | **0.3177** | Normal | Standard transaction |
| `tx_norm_1906_141937cb` | **0.3176** | Normal | Standard transaction |
| `tx_norm_903_c9cd4774` | **0.3174** | Normal | Standard transaction |
| `tx_norm_2416_201108a4` | **0.3172** | Normal | Standard transaction |
| `tx_norm_2025_10a194ce` | **0.3170** | Normal | Standard transaction |
| `tx_norm_318_e0675516` | **0.3164** | Normal | Standard transaction |
| `tx_norm_2047_de78f9a6` | **0.3164** | Normal | Standard transaction |
| `tx_norm_1877_01dff1f4` | **0.3163** | Normal | Standard transaction |
| `tx_norm_2310_36f2a40f` | **0.3161** | Normal | Standard transaction |
| `tx_norm_1316_c7732069` | **0.3160** | Normal | Standard transaction |
| `tx_norm_2243_9dfcd8d5` | **0.3160** | Normal | Standard transaction |
| `tx_norm_2286_25059195` | **0.3160** | Normal | Standard transaction |
| `tx_norm_1374_3464aeda` | **0.3159** | Normal | Standard transaction |
| `tx_norm_142_398e1c2f` | **0.3158** | Normal | Standard transaction |
| `tx_norm_806_cea99057` | **0.3156** | Normal | Standard transaction |
| `tx_norm_481_59ecad65` | **0.3155** | Normal | Standard transaction |
| `tx_norm_61_105243ba` | **0.3152** | Normal | Standard transaction |
| `tx_norm_2166_372569be` | **0.3151** | Normal | Standard transaction |
| `tx_norm_298_3ddaa6db` | **0.3150** | Normal | Standard transaction |
| `tx_norm_890_d0b67687` | **0.3150** | Normal | Standard transaction |
| `tx_norm_2603_d5f50732` | **0.3149** | Normal | Standard transaction |
| `tx_norm_831_93fcdac9` | **0.3147** | Normal | Standard transaction |
| `tx_norm_431_634deba0` | **0.3145** | Normal | Standard transaction |
| `tx_norm_1263_69fd57f2` | **0.3145** | Normal | Standard transaction |
| `tx_norm_250_87c4a779` | **0.3144** | Normal | Standard transaction |
| `tx_norm_1140_4851a6e7` | **0.3144** | Normal | Standard transaction |
| `tx_norm_1670_93c41e9a` | **0.3141** | Normal | Standard transaction |
| `tx_norm_1775_d77162cd` | **0.3140** | Normal | Standard transaction |
| `tx_norm_1329_60e63727` | **0.3139** | Normal | Standard transaction |
| `tx_norm_379_ef54b865` | **0.3138** | Normal | Standard transaction |
| `tx_norm_2309_2e9e90b1` | **0.3134** | Normal | Standard transaction |
| `tx_norm_1615_066175c2` | **0.3131** | Normal | Standard transaction |
| `tx_norm_2269_cb941e3b` | **0.3131** | Normal | Standard transaction |
| `tx_norm_525_22061e90` | **0.3128** | Normal | Standard transaction |
| `tx_norm_1355_131d50f9` | **0.3128** | Normal | Standard transaction |
| `tx_norm_566_57b35dbd` | **0.3126** | Normal | Standard transaction |
| `tx_norm_1365_7bb3edef` | **0.3126** | Normal | Standard transaction |
| `tx_norm_1402_7d6153d0` | **0.3121** | Normal | Standard transaction |
| `tx_norm_22_dff23efa` | **0.3120** | Normal | Standard transaction |
| `tx_norm_819_1b6fb89e` | **0.3118** | Normal | Standard transaction |
| `tx_norm_1604_1c014ed8` | **0.3117** | Normal | Standard transaction |
| `tx_norm_185_e204f81d` | **0.3111** | Normal | Standard transaction |
| `tx_norm_1369_65fb4cf4` | **0.3110** | Normal | Standard transaction |
| `tx_norm_2206_525cd254` | **0.3104** | Normal | Standard transaction |
| `tx_norm_1381_d5d886bf` | **0.3103** | Normal | Standard transaction |
| `tx_norm_657_de277a63` | **0.3102** | Normal | Standard transaction |
| `tx_norm_1277_6798d76c` | **0.3098** | Normal | Standard transaction |
| `tx_norm_1816_691052e3` | **0.3097** | Normal | Standard transaction |
| `tx_norm_2570_0b4eac8a` | **0.3097** | Normal | Standard transaction |
| `tx_norm_1487_b625908a` | **0.3096** | Normal | Standard transaction |
| `tx_norm_2077_80867e04` | **0.3096** | Normal | Standard transaction |
| `tx_norm_1727_5e626e47` | **0.3094** | Normal | Standard transaction |
| `tx_norm_2412_41e46cb5` | **0.3094** | Normal | Standard transaction |
| `tx_norm_2110_dcf99023` | **0.3093** | Normal | Standard transaction |
| `tx_norm_2216_e161aeff` | **0.3093** | Normal | Standard transaction |
| `tx_norm_2609_0f314a1a` | **0.3091** | Normal | Standard transaction |
| `tx_norm_1308_b35d09fe` | **0.3089** | Normal | Standard transaction |
| `tx_norm_1966_d6d7815d` | **0.3089** | Normal | Standard transaction |
| `tx_norm_563_583620bd` | **0.3086** | Normal | Standard transaction |
| `tx_norm_713_74fb69bb` | **0.3086** | Normal | Standard transaction |
| `tx_norm_1870_1c0d0462` | **0.3086** | Normal | Standard transaction |
| `tx_norm_2035_6bf79c6b` | **0.3084** | Normal | Standard transaction |
| `tx_norm_1219_f55c8cc6` | **0.3080** | Normal | Standard transaction |
| `tx_norm_1455_42b3cd39` | **0.3079** | Normal | Standard transaction |
| `tx_norm_161_cd456057` | **0.3077** | Normal | Standard transaction |
| `tx_norm_10_d415ecf1` | **0.3076** | Normal | Standard transaction |
| `tx_norm_96_4cdce551` | **0.3074** | Normal | Standard transaction |
| `tx_norm_886_c9542b54` | **0.3074** | Normal | Standard transaction |
| `tx_norm_2318_26353f68` | **0.3074** | Normal | Standard transaction |
| `tx_norm_730_3254f61c` | **0.3073** | Normal | Standard transaction |
| `tx_norm_1552_b3255efd` | **0.3072** | Normal | Standard transaction |
| `tx_norm_2409_fd8bd0c4` | **0.3071** | Normal | Standard transaction |
| `tx_norm_895_4eef0428` | **0.3068** | Normal | Standard transaction |
| `tx_norm_1762_b31de1aa` | **0.3067** | Normal | Standard transaction |
| `tx_norm_76_f4418070` | **0.3063** | Normal | Standard transaction |
| `tx_norm_513_7719a487` | **0.3055** | Normal | Standard transaction |
| `tx_norm_1312_d0e599d1` | **0.3055** | Normal | Standard transaction |
| `tx_norm_199_c732be09` | **0.3054** | Normal | Standard transaction |
| `tx_norm_798_2cb06c2b` | **0.3049** | Normal | Standard transaction |
| `tx_norm_491_05d92b44` | **0.3041** | Normal | Standard transaction |
| `tx_norm_173_d4198b61` | **0.3039** | Normal | Standard transaction |
| `tx_norm_158_e4345fa7` | **0.3038** | Normal | Standard transaction |
| `tx_norm_2005_a2c3df46` | **0.3035** | Normal | Standard transaction |
| `tx_norm_28_aebe01fd` | **0.3033** | Normal | Standard transaction |
| `tx_norm_658_eea6fe06` | **0.3033** | Normal | Standard transaction |
| `tx_norm_1671_450aec86` | **0.3033** | Normal | Standard transaction |
| `tx_norm_359_16955f09` | **0.3029** | Normal | Standard transaction |
| `tx_norm_465_d900cb45` | **0.3029** | Normal | Standard transaction |
| `tx_norm_995_2c4fbcb0` | **0.3029** | Normal | Standard transaction |
| `tx_norm_1126_b925db08` | **0.3024** | Normal | Standard transaction |
| `tx_norm_1681_1210399d` | **0.3023** | Normal | Standard transaction |
| `tx_norm_2298_5f82b6ca` | **0.3019** | Normal | Standard transaction |
| `tx_norm_1747_5f7ec11a` | **0.3018** | Normal | Standard transaction |
| `tx_norm_1708_a3473977` | **0.3017** | Normal | Standard transaction |
| `tx_norm_2394_107ed4be` | **0.3017** | Normal | Standard transaction |
| `tx_norm_1168_634d56ae` | **0.3016** | Normal | Standard transaction |
| `tx_norm_780_a654eb68` | **0.3014** | Normal | Standard transaction |
| `tx_norm_1499_f7a536e5` | **0.3013** | Normal | Standard transaction |
| `tx_norm_2505_cacc8688` | **0.3012** | Normal | Standard transaction |
| `tx_norm_1205_6d7fb0e3` | **0.3010** | Normal | Standard transaction |
| `tx_norm_1502_b94dfa00` | **0.3008** | Normal | Standard transaction |
| `tx_norm_1690_81e2cddb` | **0.3007** | Normal | Standard transaction |
| `tx_norm_2426_cc18fe95` | **0.3007** | Normal | Standard transaction |
| `tx_norm_1791_d0a487fc` | **0.3006** | Normal | Standard transaction |
| `tx_norm_53_bce76603` | **0.3002** | Normal | Standard transaction |
| `tx_norm_547_a8ac2ca2` | **0.3001** | Normal | Standard transaction |
| `tx_norm_840_d642ae2b` | **0.3001** | Normal | Standard transaction |
| `tx_norm_935_932414d0` | **0.2995** | Normal | Standard transaction |
| `tx_norm_1620_0a741ae4` | **0.2995** | Normal | Standard transaction |
| `tx_norm_1728_a629c2e4` | **0.2993** | Normal | Standard transaction |
| `tx_norm_397_168554bc` | **0.2991** | Normal | Standard transaction |
| `tx_norm_504_2e83c4ef` | **0.2989** | Normal | Standard transaction |
| `tx_norm_699_be5c24be` | **0.2988** | Normal | Standard transaction |
| `tx_norm_1757_16282b07` | **0.2986** | Normal | Standard transaction |
| `tx_norm_1998_d1be2d94` | **0.2979** | Normal | Standard transaction |
| `tx_norm_644_94533d03` | **0.2978** | Normal | Standard transaction |
| `tx_norm_31_4fd96863` | **0.2976** | Normal | Standard transaction |
| `tx_norm_1467_db2f889f` | **0.2975** | Normal | Standard transaction |
| `tx_norm_1509_97e77761` | **0.2975** | Normal | Standard transaction |
| `tx_norm_2584_79ba2a9a` | **0.2971** | Normal | Standard transaction |
| `tx_norm_899_a0b824b9` | **0.2970** | Normal | Standard transaction |
| `tx_norm_605_ba348dda` | **0.2967** | Normal | Standard transaction |
| `tx_norm_911_6f945db7` | **0.2967** | Normal | Standard transaction |
| `tx_norm_1008_06c26ece` | **0.2966** | Normal | Standard transaction |
| `tx_norm_1561_0d833369` | **0.2965** | Normal | Standard transaction |
| `tx_norm_691_61173fd9` | **0.2963** | Normal | Standard transaction |
| `tx_norm_1751_7fc7de95` | **0.2963** | Normal | Standard transaction |
| `tx_norm_91_c685c1ae` | **0.2961** | Normal | Standard transaction |
| `tx_norm_1185_0ddaee42` | **0.2956** | Normal | Standard transaction |
| `tx_norm_1508_16deeec5` | **0.2956** | Normal | Standard transaction |
| `tx_norm_2354_12d80aeb` | **0.2956** | Normal | Standard transaction |
| `tx_norm_315_f6b1b020` | **0.2952** | Normal | Standard transaction |
| `tx_norm_2453_b9ded03d` | **0.2950** | Normal | Standard transaction |
| `tx_norm_2387_9b75bf75` | **0.2949** | Normal | Standard transaction |
| `tx_norm_1134_477e7c05` | **0.2948** | Normal | Standard transaction |
| `tx_norm_1235_4a7f2fa2` | **0.2947** | Normal | Standard transaction |
| `tx_norm_1292_3e9b521d` | **0.2946** | Normal | Standard transaction |
| `tx_norm_1346_a7511f32` | **0.2943** | Normal | Standard transaction |
| `tx_norm_963_b3544b5a` | **0.2940** | Normal | Standard transaction |
| `tx_norm_1630_c2b2f1c4` | **0.2937** | Normal | Standard transaction |
| `tx_norm_56_767c4526` | **0.2933** | Normal | Standard transaction |
| `tx_norm_874_52bccd58` | **0.2932** | Normal | Standard transaction |
| `tx_norm_1382_1c6b3176` | **0.2931** | Normal | Standard transaction |
| `tx_norm_1254_8630e44a` | **0.2929** | Normal | Standard transaction |
| `tx_norm_1461_32eccf8d` | **0.2927** | Normal | Standard transaction |
| `tx_norm_616_c0fc1964` | **0.2925** | Normal | Standard transaction |
| `tx_norm_2212_d6e8dfdb` | **0.2925** | Normal | Standard transaction |
| `tx_norm_1910_50c6b0a2` | **0.2924** | Normal | Standard transaction |
| `tx_norm_654_ac556422` | **0.2922** | Normal | Standard transaction |
| `tx_norm_1622_3ffa520f` | **0.2922** | Normal | Standard transaction |
| `tx_norm_1556_ed92b3f4` | **0.2916** | Normal | Standard transaction |
| `tx_norm_2400_e81c6198` | **0.2916** | Normal | Standard transaction |
| `tx_norm_87_26ecaf95` | **0.2915** | Normal | Standard transaction |
| `tx_norm_1249_44e88f6c` | **0.2905** | Normal | Standard transaction |
| `tx_norm_1077_c6821224` | **0.2900** | Normal | Standard transaction |
| `tx_norm_435_8025458a` | **0.2897** | Normal | Standard transaction |
| `tx_norm_756_d7381305` | **0.2895** | Normal | Standard transaction |
| `tx_norm_1578_8aa4d575` | **0.2892** | Normal | Standard transaction |
| `tx_norm_2443_97a419da` | **0.2892** | Normal | Standard transaction |
| `tx_norm_998_c28b4433` | **0.2890** | Normal | Standard transaction |
| `tx_norm_1562_326bdfe2` | **0.2890** | Normal | Standard transaction |
| `tx_norm_1668_fe61bcb9` | **0.2890** | Normal | Standard transaction |
| `tx_norm_1648_653ac7e7` | **0.2889** | Normal | Standard transaction |
| `tx_norm_2172_d3b9eedf` | **0.2889** | Normal | Standard transaction |
| `tx_norm_2299_f493750b` | **0.2889** | Normal | Standard transaction |
| `tx_norm_170_0f0d337e` | **0.2888** | Normal | Standard transaction |
| `tx_norm_1241_dce8249a` | **0.2888** | Normal | Standard transaction |
| `tx_norm_1982_b9b95521` | **0.2888** | Normal | Standard transaction |
| `tx_norm_2114_7101c39d` | **0.2887** | Normal | Standard transaction |
| `tx_norm_1366_c071c8f4` | **0.2882** | Normal | Standard transaction |
| `tx_norm_88_90bae468` | **0.2876** | Normal | Standard transaction |
| `tx_norm_833_5073d160` | **0.2874** | Normal | Standard transaction |
| `tx_norm_19_f9d5ab4a` | **0.2873** | Normal | Standard transaction |
| `tx_norm_2606_06295e8c` | **0.2873** | Normal | Standard transaction |
| `tx_norm_2470_1a5de9f3` | **0.2872** | Normal | Standard transaction |
| `tx_norm_910_b1751902` | **0.2871** | Normal | Standard transaction |
| `tx_norm_401_88873e9c` | **0.2867** | Normal | Standard transaction |
| `tx_norm_74_84beaffd` | **0.2866** | Normal | Standard transaction |
| `tx_norm_536_1646d5db` | **0.2866** | Normal | Standard transaction |
| `tx_norm_2566_c888bf90` | **0.2866** | Normal | Standard transaction |
| `tx_norm_2158_be01aa24` | **0.2863** | Normal | Standard transaction |
| `tx_norm_696_05f9d11a` | **0.2862** | Normal | Standard transaction |
| `tx_norm_1961_f23acfe0` | **0.2861** | Normal | Standard transaction |
| `tx_norm_2556_a9efb8fb` | **0.2861** | Normal | Standard transaction |
| `tx_norm_1122_32d921d3` | **0.2860** | Normal | Standard transaction |
| `tx_norm_2066_6169cfa5` | **0.2860** | Normal | Standard transaction |
| `tx_norm_1182_26c432b2` | **0.2859** | Normal | Standard transaction |
| `tx_norm_2155_8ee435db` | **0.2857** | Normal | Standard transaction |
| `tx_norm_1110_de21f8cd` | **0.2856** | Normal | Standard transaction |
| `tx_norm_364_8217da94` | **0.2855** | Normal | Standard transaction |
| `tx_norm_1569_51d2a01c` | **0.2855** | Normal | Standard transaction |
| `tx_norm_2405_ed8787de` | **0.2854** | Normal | Standard transaction |
| `tx_norm_2579_490f46d9` | **0.2854** | Normal | Standard transaction |
| `tx_norm_1486_ab18698b` | **0.2853** | Normal | Standard transaction |
| `tx_norm_1787_876924ad` | **0.2853** | Normal | Standard transaction |
| `tx_norm_1746_97fdf547` | **0.2852** | Normal | Standard transaction |
| `tx_norm_758_0da61d60` | **0.2850** | Normal | Standard transaction |
| `tx_norm_1674_e1eac968` | **0.2850** | Normal | Standard transaction |
| `tx_norm_1763_93c8eed8` | **0.2850** | Normal | Standard transaction |
| `tx_norm_2260_08dd5638` | **0.2850** | Normal | Standard transaction |
| `tx_norm_2587_af7c3d24` | **0.2847** | Normal | Standard transaction |
| `tx_norm_115_0bf6ca5c` | **0.2845** | Normal | Standard transaction |
| `tx_norm_1032_cf0a98b2` | **0.2843** | Normal | Standard transaction |
| `tx_norm_3_dc74101c` | **0.2842** | Normal | Standard transaction |
| `tx_norm_316_086e0733` | **0.2835** | Normal | Standard transaction |
| `tx_norm_1052_26593f01` | **0.2835** | Normal | Standard transaction |
| `tx_norm_880_a9a61aac` | **0.2830** | Normal | Standard transaction |
| `tx_norm_982_c3643d3c` | **0.2830** | Normal | Standard transaction |
| `tx_norm_1091_2369dd95` | **0.2827** | Normal | Standard transaction |
| `tx_norm_901_a8c56849` | **0.2826** | Normal | Standard transaction |
| `tx_norm_618_e72e5ad5` | **0.2823** | Normal | Standard transaction |
| `tx_norm_2194_1d548fac` | **0.2821** | Normal | Standard transaction |
| `tx_norm_933_c07a5ef3` | **0.2817** | Normal | Standard transaction |
| `tx_norm_27_763440f6` | **0.2815** | Normal | Standard transaction |
| `tx_norm_1801_cd69db7a` | **0.2813** | Normal | Standard transaction |
| `tx_norm_1151_9dbd8456` | **0.2812** | Normal | Standard transaction |
| `tx_norm_1349_6d4d7862` | **0.2812** | Normal | Standard transaction |
| `tx_norm_1442_7ec324ab` | **0.2811** | Normal | Standard transaction |
| `tx_norm_2245_859041bf` | **0.2809** | Normal | Standard transaction |
| `tx_norm_2626_2ffc1fd6` | **0.2806** | Normal | Standard transaction |
| `tx_norm_2572_4f8100d2` | **0.2805** | Normal | Standard transaction |
| `tx_norm_562_b0e7edd3` | **0.2804** | Normal | Standard transaction |
| `tx_norm_1804_e8095bed` | **0.2801** | Normal | Standard transaction |
| `tx_norm_189_4bbd5d50` | **0.2797** | Normal | Standard transaction |
| `tx_norm_1050_13dc9c0c` | **0.2796** | Normal | Standard transaction |
| `tx_norm_540_d38e4153` | **0.2795** | Normal | Standard transaction |
| `tx_norm_707_be512fa0` | **0.2793** | Normal | Standard transaction |
| `tx_norm_1812_37425440` | **0.2791** | Normal | Standard transaction |
| `tx_norm_305_ef21c675` | **0.2790** | Normal | Standard transaction |
| `tx_norm_612_243df79d` | **0.2789** | Normal | Standard transaction |
| `tx_norm_2010_fdaa5ecb` | **0.2789** | Normal | Standard transaction |
| `tx_norm_818_df707bcc` | **0.2788** | Normal | Standard transaction |
| `tx_norm_1814_dd8b9441` | **0.2788** | Normal | Standard transaction |
| `tx_norm_1955_0f9e9e97` | **0.2786** | Normal | Standard transaction |
| `tx_norm_2540_132241e2` | **0.2785** | Normal | Standard transaction |
| `tx_norm_1608_8680debe` | **0.2783** | Normal | Standard transaction |
| `tx_norm_2048_1388e613` | **0.2783** | Normal | Standard transaction |
| `tx_norm_2514_681b2b1b` | **0.2781** | Normal | Standard transaction |
| `tx_norm_2198_90fb688d` | **0.2780** | Normal | Standard transaction |
| `tx_norm_2098_122a4b79` | **0.2778** | Normal | Standard transaction |
| `tx_norm_2363_e27ebe7a` | **0.2778** | Normal | Standard transaction |
| `tx_norm_485_6bf8fe85` | **0.2775** | Normal | Standard transaction |
| `tx_norm_2479_56adb703` | **0.2775** | Normal | Standard transaction |
| `tx_norm_602_71873671` | **0.2773** | Normal | Standard transaction |
| `tx_norm_759_58135745` | **0.2773** | Normal | Standard transaction |
| `tx_norm_2029_0c047227` | **0.2770** | Normal | Standard transaction |
| `tx_norm_2317_a3631b14` | **0.2769** | Normal | Standard transaction |
| `tx_norm_627_86f13d4a` | **0.2768** | Normal | Standard transaction |
| `tx_norm_281_f27e124b` | **0.2766** | Normal | Standard transaction |
| `tx_norm_2197_40a4ac50` | **0.2766** | Normal | Standard transaction |
| `tx_norm_1112_b984102d` | **0.2764** | Normal | Standard transaction |
| `tx_norm_735_71edf856` | **0.2760** | Normal | Standard transaction |
| `tx_norm_1079_18a9eee1` | **0.2756** | Normal | Standard transaction |
| `tx_norm_747_636e4d7c` | **0.2754** | Normal | Standard transaction |
| `tx_norm_2418_9686afa4` | **0.2751** | Normal | Standard transaction |
| `tx_norm_763_62397200` | **0.2750** | Normal | Standard transaction |
| `tx_norm_1944_2a85b84a` | **0.2746** | Normal | Standard transaction |
| `tx_norm_2410_118b75fa` | **0.2745** | Normal | Standard transaction |
| `tx_norm_2491_d3c8918a` | **0.2743** | Normal | Standard transaction |
| `tx_norm_2175_85484405` | **0.2741** | Normal | Standard transaction |
| `tx_norm_123_69259016` | **0.2740** | Normal | Standard transaction |
| `tx_norm_584_5fc0aeab` | **0.2740** | Normal | Standard transaction |
| `tx_norm_2525_fce24788` | **0.2740** | Normal | Standard transaction |
| `tx_norm_1874_e0f63f3b` | **0.2738** | Normal | Standard transaction |
| `tx_norm_2373_ddc12dea` | **0.2733** | Normal | Standard transaction |
| `tx_norm_631_50b4b5d1` | **0.2732** | Normal | Standard transaction |
| `tx_norm_2118_a0f4381d` | **0.2729** | Normal | Standard transaction |
| `tx_norm_905_0d37bc5a` | **0.2724** | Normal | Standard transaction |
| `tx_norm_2543_578f95e4` | **0.2720** | Normal | Standard transaction |
| `tx_norm_336_b2c6d5a7` | **0.2718** | Normal | Standard transaction |
| `tx_norm_752_248ca994` | **0.2718** | Normal | Standard transaction |
| `tx_norm_418_f167a4f1` | **0.2714** | Normal | Standard transaction |
| `tx_norm_2530_d5068499` | **0.2711** | Normal | Standard transaction |
| `tx_norm_328_83c1a7f2` | **0.2709** | Normal | Standard transaction |
| `tx_norm_443_fbc19b2e` | **0.2709** | Normal | Standard transaction |
| `tx_norm_939_c05a0558` | **0.2705** | Normal | Standard transaction |
| `tx_norm_773_c6bdf81a` | **0.2703** | Normal | Standard transaction |
| `tx_norm_1720_e3cdd9ec` | **0.2701** | Normal | Standard transaction |
| `tx_norm_2375_bc9bab5c` | **0.2701** | Normal | Standard transaction |
| `tx_norm_733_a4aa4a6d` | **0.2700** | Normal | Standard transaction |
| `tx_norm_2065_896ad338` | **0.2698** | Normal | Standard transaction |
| `tx_norm_1259_f6c68730` | **0.2697** | Normal | Standard transaction |
| `tx_norm_2551_2faae524` | **0.2695** | Normal | Standard transaction |
| `tx_norm_603_f9ff6987` | **0.2692** | Normal | Standard transaction |
| `tx_norm_1438_75decbe7` | **0.2691** | Normal | Standard transaction |
| `tx_norm_1034_4037555c` | **0.2682** | Normal | Standard transaction |
| `tx_norm_2304_93f8edfd` | **0.2679** | Normal | Standard transaction |
| `tx_norm_48_e6efe974` | **0.2677** | Normal | Standard transaction |
| `tx_norm_1554_00fb6c5c` | **0.2676** | Normal | Standard transaction |
| `tx_norm_1599_97b7c5d9` | **0.2676** | Normal | Standard transaction |
| `tx_norm_2097_770cd9d8` | **0.2676** | Normal | Standard transaction |
| `tx_norm_2614_420fe698` | **0.2676** | Normal | Standard transaction |
| `tx_norm_383_124eb752` | **0.2673** | Normal | Standard transaction |
| `tx_norm_188_b8948f24` | **0.2672** | Normal | Standard transaction |
| `tx_norm_852_d77724d4` | **0.2667** | Normal | Standard transaction |
| `tx_norm_1170_31ff3506` | **0.2662** | Normal | Standard transaction |
| `tx_norm_1698_57d21087` | **0.2660** | Normal | Standard transaction |
| `tx_norm_2096_c6ec0a3b` | **0.2660** | Normal | Standard transaction |
| `tx_norm_1493_225fe4fa` | **0.2659** | Normal | Standard transaction |
| `tx_norm_1911_29b2251a` | **0.2655** | Normal | Standard transaction |
| `tx_norm_2401_48afe552` | **0.2655** | Normal | Standard transaction |
| `tx_norm_2231_90ff7f7d` | **0.2653** | Normal | Standard transaction |
| `tx_norm_1245_1bfce37d` | **0.2650** | Normal | Standard transaction |
| `tx_norm_2007_90f7a3cc` | **0.2650** | Normal | Standard transaction |
| `tx_norm_160_58478c91` | **0.2649** | Normal | Standard transaction |
| `tx_norm_1633_546643df` | **0.2649** | Normal | Standard transaction |
| `tx_norm_542_60e3e504` | **0.2648** | Normal | Standard transaction |
| `tx_norm_638_b00d74a2` | **0.2647** | Normal | Standard transaction |
| `tx_norm_400_73180622` | **0.2645** | Normal | Standard transaction |
| `tx_norm_844_486d840e` | **0.2645** | Normal | Standard transaction |
| `tx_norm_2178_c7000285` | **0.2645** | Normal | Standard transaction |
| `tx_norm_1416_88ad3a93` | **0.2644** | Normal | Standard transaction |
| `tx_norm_1298_6fc725a9` | **0.2643** | Normal | Standard transaction |
| `tx_norm_1571_b4aaf814` | **0.2642** | Normal | Standard transaction |
| `tx_norm_1572_f44557b6` | **0.2642** | Normal | Standard transaction |
| `tx_norm_1408_32b02604` | **0.2641** | Normal | Standard transaction |
| `tx_norm_424_c71ce743` | **0.2639** | Normal | Standard transaction |
| `tx_norm_1613_b84e545d` | **0.2638** | Normal | Standard transaction |
| `tx_norm_1063_64e02e2d` | **0.2637** | Normal | Standard transaction |
| `tx_norm_1557_8eaef433` | **0.2637** | Normal | Standard transaction |
| `tx_norm_2123_567e1b6f` | **0.2634** | Normal | Standard transaction |
| `tx_norm_1084_004c9198` | **0.2632** | Normal | Standard transaction |
| `tx_norm_2444_94244a58` | **0.2631** | Normal | Standard transaction |
| `tx_norm_23_a11410b6` | **0.2630** | Normal | Standard transaction |
| `tx_norm_876_f1e9d222` | **0.2629** | Normal | Standard transaction |
| `tx_norm_1830_07142e17` | **0.2629** | Normal | Standard transaction |
| `tx_norm_777_eaf98c7e` | **0.2627** | Normal | Standard transaction |
| `tx_norm_936_eb94fa7d` | **0.2627** | Normal | Standard transaction |
| `tx_norm_2313_0b84702e` | **0.2625** | Normal | Standard transaction |
| `tx_norm_2597_d0c3cf3d` | **0.2623** | Normal | Standard transaction |
| `tx_norm_44_00eed873` | **0.2619** | Normal | Standard transaction |
| `tx_norm_2159_c767f6d0` | **0.2618** | Normal | Standard transaction |
| `tx_norm_1420_7eb181fe` | **0.2617** | Normal | Standard transaction |
| `tx_norm_321_f998c60b` | **0.2616** | Normal | Standard transaction |
| `tx_norm_940_928de0db` | **0.2616** | Normal | Standard transaction |
| `tx_norm_2324_989d9e1d` | **0.2611** | Normal | Standard transaction |
| `tx_norm_573_4e30070a` | **0.2607** | Normal | Standard transaction |
| `tx_norm_2180_5e1ed645` | **0.2607** | Normal | Standard transaction |
| `tx_norm_769_72b9160d` | **0.2605** | Normal | Standard transaction |
| `tx_norm_2322_554ce470` | **0.2605** | Normal | Standard transaction |
| `tx_norm_745_40cd41b3` | **0.2604** | Normal | Standard transaction |
| `tx_norm_1803_b37965b8` | **0.2604** | Normal | Standard transaction |
| `tx_norm_259_09155e9d` | **0.2600** | Normal | Standard transaction |
| `tx_norm_410_3cd31c45` | **0.2599** | Normal | Standard transaction |
| `tx_norm_2233_e445313e` | **0.2599** | Normal | Standard transaction |
| `tx_norm_1237_7a11148f` | **0.2597** | Normal | Standard transaction |
| `tx_norm_917_18a11cb7` | **0.2595** | Normal | Standard transaction |
| `tx_norm_2230_f47c6769` | **0.2594** | Normal | Standard transaction |
| `tx_norm_2618_d4e98543` | **0.2594** | Normal | Standard transaction |
| `tx_norm_1659_c7b66ccd` | **0.2593** | Normal | Standard transaction |
| `tx_norm_1967_652c0f6d` | **0.2593** | Normal | Standard transaction |
| `tx_norm_2631_93a14769` | **0.2593** | Normal | Standard transaction |
| `tx_norm_2480_852a2431` | **0.2589** | Normal | Standard transaction |
| `tx_norm_750_e5e9f760` | **0.2586** | Normal | Standard transaction |
| `tx_norm_1949_e8d3e31b` | **0.2586** | Normal | Standard transaction |
| `tx_norm_163_a18a48f5` | **0.2583** | Normal | Standard transaction |
| `tx_norm_2246_d3954edf` | **0.2582** | Normal | Standard transaction |
| `tx_norm_1941_0e3649d5` | **0.2580** | Normal | Standard transaction |
| `tx_norm_2466_d4d1c4b5` | **0.2580** | Normal | Standard transaction |
| `tx_norm_1200_c7d8d74b` | **0.2575** | Normal | Standard transaction |
| `tx_norm_156_ee3b6688` | **0.2573** | Normal | Standard transaction |
| `tx_norm_1938_ff5101ae` | **0.2571** | Normal | Standard transaction |
| `tx_norm_2493_43db0050` | **0.2570** | Normal | Standard transaction |
| `tx_norm_567_1b312286` | **0.2568** | Normal | Standard transaction |
| `tx_norm_1260_deb37f9a` | **0.2568** | Normal | Standard transaction |
| `tx_norm_1859_df92b9a4` | **0.2562** | Normal | Standard transaction |
| `tx_norm_2634_2e2319dd` | **0.2562** | Normal | Standard transaction |
| `tx_norm_703_5b7ba2b3` | **0.2561** | Normal | Standard transaction |
| `tx_norm_1965_305e2f9a` | **0.2561** | Normal | Standard transaction |
| `tx_norm_2026_8dc14445` | **0.2561** | Normal | Standard transaction |
| `tx_norm_323_a7b520bc` | **0.2558** | Normal | Standard transaction |
| `tx_norm_904_766871a8` | **0.2555** | Normal | Standard transaction |
| `tx_norm_711_297b63fd` | **0.2553** | Normal | Standard transaction |
| `tx_norm_571_fa989b1b` | **0.2548** | Normal | Standard transaction |
| `tx_norm_2359_c772c1e9` | **0.2548** | Normal | Standard transaction |
| `tx_norm_1584_079752e3` | **0.2547** | Normal | Standard transaction |
| `tx_norm_1090_63cc4359` | **0.2546** | Normal | Standard transaction |
| `tx_norm_2407_ee589dbf` | **0.2546** | Normal | Standard transaction |
| `tx_norm_2445_96499e8e` | **0.2544** | Normal | Standard transaction |
| `tx_norm_728_fc3a9374` | **0.2543** | Normal | Standard transaction |
| `tx_norm_1573_166857a6` | **0.2543** | Normal | Standard transaction |
| `tx_norm_456_2604968f` | **0.2539** | Normal | Standard transaction |
| `tx_norm_106_40f32726` | **0.2538** | Normal | Standard transaction |
| `tx_norm_870_74150820` | **0.2538** | Normal | Standard transaction |
| `tx_norm_100_a7301dec` | **0.2537** | Normal | Standard transaction |
| `tx_norm_778_f7f0fa60` | **0.2535** | Normal | Standard transaction |
| `tx_norm_2257_efa1747a` | **0.2535** | Normal | Standard transaction |
| `tx_norm_1403_fed33a1f` | **0.2532** | Normal | Standard transaction |
| `tx_norm_1666_eae03fce` | **0.2532** | Normal | Standard transaction |
| `tx_norm_2492_64f2b704` | **0.2532** | Normal | Standard transaction |
| `tx_norm_244_fa4b66e9` | **0.2531** | Normal | Standard transaction |
| `tx_norm_2370_f581cf51` | **0.2531** | Normal | Standard transaction |
| `tx_norm_1027_b380b4b4` | **0.2530** | Normal | Standard transaction |
| `tx_norm_1936_e363d93b` | **0.2530** | Normal | Standard transaction |
| `tx_norm_1049_1f0e80b8` | **0.2529** | Normal | Standard transaction |
| `tx_norm_1887_946a0384` | **0.2528** | Normal | Standard transaction |
| `tx_norm_241_27414a84` | **0.2527** | Normal | Standard transaction |
| `tx_norm_956_28894855` | **0.2525** | Normal | Standard transaction |
| `tx_norm_2272_e01c2db6` | **0.2525** | Normal | Standard transaction |
| `tx_norm_194_fafa21e3` | **0.2523** | Normal | Standard transaction |
| `tx_norm_2622_880965ca` | **0.2522** | Normal | Standard transaction |
| `tx_norm_52_e6959e24` | **0.2521** | Normal | Standard transaction |
| `tx_norm_1396_c0521656` | **0.2520** | Normal | Standard transaction |
| `tx_norm_271_6e5ba26a` | **0.2519** | Normal | Standard transaction |
| `tx_norm_1595_1cdc05bc` | **0.2519** | Normal | Standard transaction |
| `tx_norm_614_28522ef9` | **0.2518** | Normal | Standard transaction |
| `tx_norm_1378_cf11ed4d` | **0.2518** | Normal | Standard transaction |
| `tx_norm_1586_bac6cf94` | **0.2518** | Normal | Standard transaction |
| `tx_norm_2020_2c1c16ad` | **0.2518** | Normal | Standard transaction |
| `tx_norm_1278_01fdf8c8` | **0.2517** | Normal | Standard transaction |
| `tx_norm_1973_7d16a424` | **0.2516** | Normal | Standard transaction |
| `tx_norm_1469_5e1c8fa1` | **0.2515** | Normal | Standard transaction |
| `tx_norm_67_39d86c01` | **0.2513** | Normal | Standard transaction |
| `tx_norm_107_9905f8dc` | **0.2513** | Normal | Standard transaction |
| `tx_norm_99_f6fe6bcd` | **0.2508** | Normal | Standard transaction |
| `tx_norm_2406_ac6d4de2` | **0.2508** | Normal | Standard transaction |
| `tx_norm_1980_f1146fd4` | **0.2507** | Normal | Standard transaction |
| `tx_norm_2001_e7f4ed1e` | **0.2506** | Normal | Standard transaction |
| `tx_norm_2247_d5264e30` | **0.2505** | Normal | Standard transaction |
| `tx_norm_538_377f7faa` | **0.2502** | Normal | Standard transaction |
| `tx_norm_141_cb5a1067` | **0.2501** | Normal | Standard transaction |
| `tx_norm_808_49683cfd` | **0.2501** | Normal | Standard transaction |
| `tx_norm_997_eb68ebfa` | **0.2501** | Normal | Standard transaction |
| `tx_norm_1660_1a6d3c92` | **0.2501** | Normal | Standard transaction |
| `tx_norm_1749_b84866d3` | **0.2501** | Normal | Standard transaction |
| `tx_norm_1896_e737b282` | **0.2501** | Normal | Standard transaction |
| `tx_norm_1304_2a99ce42` | **0.2498** | Normal | Standard transaction |
| `tx_norm_2004_5e9010cc` | **0.2498** | Normal | Standard transaction |
| `tx_norm_1601_9966a0ed` | **0.2497** | Normal | Standard transaction |
| `tx_norm_1404_c6dfd782` | **0.2495** | Normal | Standard transaction |
| `tx_norm_947_315387bc` | **0.2494** | Normal | Standard transaction |
| `tx_norm_1894_aae0901d` | **0.2493** | Normal | Standard transaction |
| `tx_norm_2092_80abeb6d` | **0.2493** | Normal | Standard transaction |
| `tx_norm_436_2fcf1e49` | **0.2492** | Normal | Standard transaction |
| `tx_norm_738_e28ce68e` | **0.2492** | Normal | Standard transaction |
| `tx_norm_986_89987205` | **0.2492** | Normal | Standard transaction |
| `tx_norm_332_c748f35b` | **0.2488** | Normal | Standard transaction |
| `tx_norm_1531_24417b4e` | **0.2488** | Normal | Standard transaction |
| `tx_norm_1230_f9a89aef` | **0.2483** | Normal | Standard transaction |
| `tx_norm_1609_b21b46bf` | **0.2479** | Normal | Standard transaction |
| `tx_norm_1118_95580fd3` | **0.2476** | Normal | Standard transaction |
| `tx_norm_1299_195cd662` | **0.2476** | Normal | Standard transaction |
| `tx_norm_1302_d76ab1b2` | **0.2476** | Normal | Standard transaction |
| `tx_norm_2109_e44c8328` | **0.2472** | Normal | Standard transaction |
| `tx_norm_1537_861c6c9c` | **0.2471** | Normal | Standard transaction |
| `tx_norm_2084_24253ad1` | **0.2471** | Normal | Standard transaction |
| `tx_norm_1960_1cfd9f4e` | **0.2469** | Normal | Standard transaction |
| `tx_norm_1290_4f8f607c` | **0.2468** | Normal | Standard transaction |
| `tx_norm_1359_979c078d` | **0.2462** | Normal | Standard transaction |
| `tx_norm_1769_72020064` | **0.2462** | Normal | Standard transaction |
| `tx_norm_169_b812e95f` | **0.2460** | Normal | Standard transaction |
| `tx_norm_1003_5bd90674` | **0.2460** | Normal | Standard transaction |
| `tx_norm_1171_a97b3800` | **0.2460** | Normal | Standard transaction |
| `tx_norm_2219_33d5c60f` | **0.2459** | Normal | Standard transaction |
| `tx_norm_1987_229acdbc` | **0.2457** | Normal | Standard transaction |
| `tx_norm_2565_7c77d2e5` | **0.2457** | Normal | Standard transaction |
| `tx_norm_43_7f583d7b` | **0.2454** | Normal | Standard transaction |
| `tx_norm_304_678aea9a` | **0.2454** | Normal | Standard transaction |
| `tx_norm_1828_1b217be8` | **0.2454** | Normal | Standard transaction |
| `tx_norm_1515_f2f7bec9` | **0.2451** | Normal | Standard transaction |
| `tx_norm_1099_657a11a1` | **0.2450** | Normal | Standard transaction |
| `tx_norm_1232_60bf8fde` | **0.2450** | Normal | Standard transaction |
| `tx_norm_1959_a52c85a5` | **0.2450** | Normal | Standard transaction |
| `tx_norm_1251_c2149004` | **0.2447** | Normal | Standard transaction |
| `tx_norm_2638_20089e8f` | **0.2447** | Normal | Standard transaction |
| `tx_norm_2267_98c71acf` | **0.2446** | Normal | Standard transaction |
| `tx_norm_1129_678687a4` | **0.2445** | Normal | Standard transaction |
| `tx_norm_2262_0d66786b` | **0.2436** | Normal | Standard transaction |
| `tx_norm_377_bb833bfd` | **0.2435** | Normal | Standard transaction |
| `tx_norm_643_1578c7e3` | **0.2434** | Normal | Standard transaction |
| `tx_norm_1105_e2332f9a` | **0.2432** | Normal | Standard transaction |
| `tx_norm_1841_41ba2e88` | **0.2431** | Normal | Standard transaction |
| `tx_norm_1993_b4a62a2b` | **0.2429** | Normal | Standard transaction |
| `tx_norm_205_6c6d6486` | **0.2427** | Normal | Standard transaction |
| `tx_norm_792_48bcbab2` | **0.2422** | Normal | Standard transaction |
| `tx_norm_2624_99fc3989` | **0.2420** | Normal | Standard transaction |
| `tx_norm_2357_d143bf0e` | **0.2419** | Normal | Standard transaction |
| `tx_norm_162_9f347af0` | **0.2417** | Normal | Standard transaction |
| `tx_norm_672_0b061c86` | **0.2417** | Normal | Standard transaction |
| `tx_norm_2112_f247f9c5` | **0.2413** | Normal | Standard transaction |
| `tx_norm_1644_4d673bed` | **0.2410** | Normal | Standard transaction |
| `tx_norm_421_f049fda3` | **0.2409** | Normal | Standard transaction |
| `tx_norm_2511_f7cee169` | **0.2407** | Normal | Standard transaction |
| `tx_norm_1016_e046ec94` | **0.2406** | Normal | Standard transaction |
| `tx_norm_622_e347f824` | **0.2405** | Normal | Standard transaction |
| `tx_norm_1968_5c7a2aaf` | **0.2405** | Normal | Standard transaction |
| `tx_norm_454_be38a0af` | **0.2404** | Normal | Standard transaction |
| `tx_norm_1313_d5f4c35a` | **0.2404** | Normal | Standard transaction |
| `tx_norm_722_5d375e52` | **0.2401** | Normal | Standard transaction |
| `tx_norm_1657_a3fb0266` | **0.2401** | Normal | Standard transaction |
| `tx_norm_1731_22d4ec1d` | **0.2398** | Normal | Standard transaction |
| `tx_norm_366_2aeb693e` | **0.2393** | Normal | Standard transaction |
| `tx_norm_748_97084396` | **0.2393** | Normal | Standard transaction |
| `tx_norm_1926_9ba685b7` | **0.2390** | Normal | Standard transaction |
| `tx_norm_165_0905cffd` | **0.2387** | Normal | Standard transaction |
| `tx_norm_157_733ee4b1` | **0.2386** | Normal | Standard transaction |
| `tx_norm_2459_897a0f8d` | **0.2384** | Normal | Standard transaction |
| `tx_norm_1629_c5668024` | **0.2381** | Normal | Standard transaction |
| `tx_norm_556_d62d1312` | **0.2380** | Normal | Standard transaction |
| `tx_norm_755_6547a84c` | **0.2380** | Normal | Standard transaction |
| `tx_norm_2604_354004a6` | **0.2378** | Normal | Standard transaction |
| `tx_norm_650_44ace0d7` | **0.2377** | Normal | Standard transaction |
| `tx_norm_2305_52a78b0f` | **0.2377** | Normal | Standard transaction |
| `tx_norm_62_e5f06012` | **0.2376** | Normal | Standard transaction |
| `tx_norm_398_ae09d42f` | **0.2374** | Normal | Standard transaction |
| `tx_norm_766_5c06a44c` | **0.2374** | Normal | Standard transaction |
| `tx_norm_2189_9264afa6` | **0.2374** | Normal | Standard transaction |
| `tx_norm_330_e44e1800` | **0.2371** | Normal | Standard transaction |
| `tx_norm_929_30bbb6b2` | **0.2368** | Normal | Standard transaction |
| `tx_norm_1881_13786e87` | **0.2368** | Normal | Standard transaction |
| `tx_norm_317_f6594741` | **0.2363** | Normal | Standard transaction |
| `tx_norm_1320_5adc53f1` | **0.2361** | Normal | Standard transaction |
| `tx_norm_2265_9251acad` | **0.2361** | Normal | Standard transaction |
| `tx_norm_1149_898e8deb` | **0.2359** | Normal | Standard transaction |
| `tx_norm_507_e4558b52` | **0.2356** | Normal | Standard transaction |
| `tx_norm_2542_138d5499` | **0.2356** | Normal | Standard transaction |
| `tx_norm_2107_ef5d88ed` | **0.2353** | Normal | Standard transaction |
| `tx_norm_966_6f444624` | **0.2352** | Normal | Standard transaction |
| `tx_norm_1641_43f790ec` | **0.2349** | Normal | Standard transaction |
| `tx_norm_2340_055ea20d` | **0.2349** | Normal | Standard transaction |
| `tx_norm_39_d0cc5b63` | **0.2348** | Normal | Standard transaction |
| `tx_norm_248_47faf16a` | **0.2348** | Normal | Standard transaction |
| `tx_norm_367_de462069` | **0.2348** | Normal | Standard transaction |
| `tx_norm_1051_66c388d9` | **0.2346** | Normal | Standard transaction |
| `tx_norm_2200_755aced0` | **0.2345** | Normal | Standard transaction |
| `tx_norm_1093_de7acbbc` | **0.2343** | Normal | Standard transaction |
| `tx_norm_1872_bc10aef7` | **0.2337** | Normal | Standard transaction |
| `tx_norm_2204_9eece355` | **0.2336** | Normal | Standard transaction |
| `tx_norm_2071_eddbce3f` | **0.2330** | Normal | Standard transaction |
| `tx_norm_1274_b2fb0c7a` | **0.2323** | Normal | Standard transaction |
| `tx_norm_1458_a8bd401d` | **0.2320** | Normal | Standard transaction |
| `tx_norm_1712_5dab4da3` | **0.2318** | Normal | Standard transaction |
| `tx_norm_2589_511d653f` | **0.2312** | Normal | Standard transaction |
| `tx_norm_1811_88b42806` | **0.2311** | Normal | Standard transaction |
| `tx_norm_1141_43926644` | **0.2310** | Normal | Standard transaction |
| `tx_norm_2465_84c98adf` | **0.2310** | Normal | Standard transaction |
| `tx_norm_232_32a3772c` | **0.2307** | Normal | Standard transaction |
| `tx_norm_512_79e6e5d6` | **0.2307** | Normal | Standard transaction |
| `tx_norm_1409_71ac3749` | **0.2307** | Normal | Standard transaction |
| `tx_norm_1145_2e644d0d` | **0.2306** | Normal | Standard transaction |
| `tx_norm_575_742365f0` | **0.2305** | Normal | Standard transaction |
| `tx_norm_1818_1b8749e8` | **0.2305** | Normal | Standard transaction |
| `tx_norm_788_67c33da6` | **0.2302** | Normal | Standard transaction |
| `tx_norm_1546_a3deff56` | **0.2301** | Normal | Standard transaction |
| `tx_norm_884_de4e01ea` | **0.2297** | Normal | Standard transaction |
| `tx_norm_823_b8b4dad5` | **0.2294** | Normal | Standard transaction |
| `tx_norm_1875_0a2db501` | **0.2292** | Normal | Standard transaction |
| `tx_norm_662_b5cb5486` | **0.2290** | Normal | Standard transaction |
| `tx_norm_2274_eed7be3e` | **0.2289** | Normal | Standard transaction |
| `tx_norm_729_dbb90480` | **0.2288** | Normal | Standard transaction |
| `tx_norm_273_55949258` | **0.2287** | Normal | Standard transaction |
| `tx_norm_132_496ba019` | **0.2285** | Normal | Standard transaction |
| `tx_norm_648_7d8fa9fc` | **0.2285** | Normal | Standard transaction |
| `tx_norm_2220_013db0aa` | **0.2282** | Normal | Standard transaction |
| `tx_norm_611_3959f948` | **0.2280** | Normal | Standard transaction |
| `tx_norm_1363_2b89feb3` | **0.2279** | Normal | Standard transaction |
| `tx_norm_75_16a3a6b9` | **0.2277** | Normal | Standard transaction |
| `tx_norm_764_71c15347` | **0.2277** | Normal | Standard transaction |
| `tx_norm_902_b4cb7a93` | **0.2277** | Normal | Standard transaction |
| `tx_norm_1771_3c6b570b` | **0.2277** | Normal | Standard transaction |
| `tx_norm_2285_f7e7cd1e` | **0.2277** | Normal | Standard transaction |
| `tx_norm_1004_8d259fb1` | **0.2276** | Normal | Standard transaction |
| `tx_norm_2548_2dd23d5c` | **0.2273** | Normal | Standard transaction |
| `tx_norm_1130_e58158ba` | **0.2272** | Normal | Standard transaction |
| `tx_norm_1220_7b98102a` | **0.2270** | Normal | Standard transaction |
| `tx_norm_1440_afc68951` | **0.2268** | Normal | Standard transaction |
| `tx_norm_137_fff729d3` | **0.2267** | Normal | Standard transaction |
| `tx_norm_2366_98a2185f` | **0.2264** | Normal | Standard transaction |
| `tx_norm_1687_b10e7de4` | **0.2263** | Normal | Standard transaction |
| `tx_norm_406_66f05292` | **0.2261** | Normal | Standard transaction |
| `tx_norm_652_2341dbe7` | **0.2260** | Normal | Standard transaction |
| `tx_norm_266_cb6557f6` | **0.2255** | Normal | Standard transaction |
| `tx_norm_2494_491a9341` | **0.2254** | Normal | Standard transaction |
| `tx_norm_2252_e87d4a71` | **0.2253** | Normal | Standard transaction |
| `tx_norm_2187_d185486e` | **0.2252** | Normal | Standard transaction |
| `tx_norm_678_d2cc5272` | **0.2249** | Normal | Standard transaction |
| `tx_norm_770_5dd20f05` | **0.2248** | Normal | Standard transaction |
| `tx_norm_617_bbd6f943` | **0.2247** | Normal | Standard transaction |
| `tx_norm_2130_dc8da39c` | **0.2242** | Normal | Standard transaction |
| `tx_norm_2232_33db7a75` | **0.2241** | Normal | Standard transaction |
| `tx_norm_151_88f70767` | **0.2240** | Normal | Standard transaction |
| `tx_norm_252_bd8dec36` | **0.2238** | Normal | Standard transaction |
| `tx_norm_1128_30d1d2bc` | **0.2238** | Normal | Standard transaction |
| `tx_norm_72_9acf1ab7` | **0.2235** | Normal | Standard transaction |
| `tx_norm_2207_623d68be` | **0.2235** | Normal | Standard transaction |
| `tx_norm_1777_7a31f612` | **0.2233** | Normal | Standard transaction |
| `tx_norm_1767_f6ce79a7` | **0.2232** | Normal | Standard transaction |
| `tx_norm_1501_c509b0a6` | **0.2231** | Normal | Standard transaction |
| `tx_norm_451_f838f3bd` | **0.2229** | Normal | Standard transaction |
| `tx_norm_537_bcd92df8` | **0.2226** | Normal | Standard transaction |
| `tx_norm_993_dd71e1cb` | **0.2224** | Normal | Standard transaction |
| `tx_norm_2351_521d7db9` | **0.2223** | Normal | Standard transaction |
| `tx_norm_26_e5adc767` | **0.2221** | Normal | Standard transaction |
| `tx_norm_1833_bd14234f` | **0.2221** | Normal | Standard transaction |
| `tx_norm_2282_bd46cd99` | **0.2221** | Normal | Standard transaction |
| `tx_norm_71_4a2164c9` | **0.2220** | Normal | Standard transaction |
| `tx_norm_2100_da12424d` | **0.2220** | Normal | Standard transaction |
| `tx_norm_671_ad891da1` | **0.2219** | Normal | Standard transaction |
| `tx_norm_1585_5bd6a336` | **0.2219** | Normal | Standard transaction |
| `tx_norm_1252_fd462156` | **0.2218** | Normal | Standard transaction |
| `tx_norm_1339_632129eb` | **0.2218** | Normal | Standard transaction |
| `tx_norm_195_8e6669ff` | **0.2217** | Normal | Standard transaction |
| `tx_norm_524_6be923ea` | **0.2217** | Normal | Standard transaction |
| `tx_norm_208_e5b7db53` | **0.2213** | Normal | Standard transaction |
| `tx_norm_238_181bf0e0` | **0.2212** | Normal | Standard transaction |
| `tx_norm_1234_c8597063` | **0.2210** | Normal | Standard transaction |
| `tx_norm_2192_b5ebbbcd` | **0.2210** | Normal | Standard transaction |
| `tx_norm_376_d0465934` | **0.2207** | Normal | Standard transaction |
| `tx_norm_1106_8133c545` | **0.2207** | Normal | Standard transaction |
| `tx_norm_1400_e5d4fa45` | **0.2205** | Normal | Standard transaction |
| `tx_norm_2451_1386b20c` | **0.2205** | Normal | Standard transaction |
| `tx_norm_1412_abd31787` | **0.2202** | Normal | Standard transaction |
| `tx_norm_1437_282ed66f` | **0.2202** | Normal | Standard transaction |
| `tx_norm_5_40014516` | **0.2200** | Normal | Standard transaction |
| `tx_norm_196_e0e35534` | **0.2200** | Normal | Standard transaction |
| `tx_norm_1014_99a4d538` | **0.2199** | Normal | Standard transaction |
| `tx_norm_1734_39ff04e6` | **0.2197** | Normal | Standard transaction |
| `tx_norm_954_9ad95f19` | **0.2195** | Normal | Standard transaction |
| `tx_norm_2261_67014228` | **0.2194** | Normal | Standard transaction |
| `tx_norm_661_31b7486a` | **0.2192** | Normal | Standard transaction |
| `tx_norm_209_8522c599` | **0.2191** | Normal | Standard transaction |
| `tx_norm_991_9605a3ba` | **0.2187** | Normal | Standard transaction |
| `tx_norm_148_b298e660` | **0.2185** | Normal | Standard transaction |
| `tx_norm_736_745e751e` | **0.2183** | Normal | Standard transaction |
| `tx_norm_810_5c648297` | **0.2183** | Normal | Standard transaction |
| `tx_norm_1808_71c2640a` | **0.2181** | Normal | Standard transaction |
| `tx_norm_15_af479558` | **0.2178** | Normal | Standard transaction |
| `tx_norm_2454_6217382a` | **0.2176** | Normal | Standard transaction |
| `tx_norm_1504_a9b7e0f0` | **0.2175** | Normal | Standard transaction |
| `tx_norm_1786_bcbd8f1e` | **0.2174** | Normal | Standard transaction |
| `tx_norm_1169_8e518c11` | **0.2173** | Normal | Standard transaction |
| `tx_norm_1262_04c6146a` | **0.2172** | Normal | Standard transaction |
| `tx_norm_1526_155490a9` | **0.2170** | Normal | Standard transaction |
| `tx_norm_1468_441d0028` | **0.2169** | Normal | Standard transaction |
| `tx_norm_249_7d14c50d` | **0.2168** | Normal | Standard transaction |
| `tx_norm_646_946fe6cd` | **0.2167** | Normal | Standard transaction |
| `tx_norm_653_df5a133e` | **0.2167** | Normal | Standard transaction |
| `tx_norm_1324_ddeb3296` | **0.2165** | Normal | Standard transaction |
| `tx_norm_521_47a1f41c` | **0.2163** | Normal | Standard transaction |
| `tx_norm_1394_a707fadc` | **0.2163** | Normal | Standard transaction |
| `tx_norm_2279_588be72c` | **0.2162** | Normal | Standard transaction |
| `tx_norm_1279_e932f22b` | **0.2161** | Normal | Standard transaction |
| `tx_norm_1432_dbaf125f` | **0.2159** | Normal | Standard transaction |
| `tx_norm_2639_424ce811` | **0.2159** | Normal | Standard transaction |
| `tx_norm_1716_746f462f` | **0.2158** | Normal | Standard transaction |
| `tx_norm_1307_d40dfc6f` | **0.2156** | Normal | Standard transaction |
| `tx_norm_649_cb6e4fe8` | **0.2154** | Normal | Standard transaction |
| `tx_norm_2087_391539fb` | **0.2152** | Normal | Standard transaction |
| `tx_norm_2122_756d40b4` | **0.2152** | Normal | Standard transaction |
| `tx_norm_2337_eb80e4b3` | **0.2150** | Normal | Standard transaction |
| `tx_norm_264_f54c83cc` | **0.2149** | Normal | Standard transaction |
| `tx_norm_1817_b80146fd` | **0.2149** | Normal | Standard transaction |
| `tx_norm_375_81b896be` | **0.2147** | Normal | Standard transaction |
| `tx_norm_760_98542fcd` | **0.2145** | Normal | Standard transaction |
| `tx_norm_1337_2cd6ad88` | **0.2145** | Normal | Standard transaction |
| `tx_norm_2348_f6f94670` | **0.2145** | Normal | Standard transaction |
| `tx_norm_2027_b322cf14` | **0.2144** | Normal | Standard transaction |
| `tx_norm_2415_3737aa5c` | **0.2142** | Normal | Standard transaction |
| `tx_norm_2422_8eb7d2a8` | **0.2140** | Normal | Standard transaction |
| `tx_norm_943_5a21c040` | **0.2138** | Normal | Standard transaction |
| `tx_norm_8_b202f03d` | **0.2136** | Normal | Standard transaction |
| `tx_norm_1124_5e3f504f` | **0.2135** | Normal | Standard transaction |
| `tx_norm_373_021b4cfe` | **0.2133** | Normal | Standard transaction |
| `tx_norm_962_792c02fb` | **0.2132** | Normal | Standard transaction |
| `tx_norm_1773_3a995caf` | **0.2132** | Normal | Standard transaction |
| `tx_norm_2101_8577e5c8` | **0.2128** | Normal | Standard transaction |
| `tx_norm_341_45462a45` | **0.2126** | Normal | Standard transaction |
| `tx_norm_1224_613aee18` | **0.2126** | Normal | Standard transaction |
| `tx_norm_651_e2885eee` | **0.2123** | Normal | Standard transaction |
| `tx_norm_302_d79dff66` | **0.2121** | Normal | Standard transaction |
| `tx_norm_1802_7f944b9b` | **0.2119** | Normal | Standard transaction |
| `tx_norm_1921_7c5f7f72` | **0.2117** | Normal | Standard transaction |
| `tx_norm_1652_6d0e8481` | **0.2116** | Normal | Standard transaction |
| `tx_norm_1341_9b9efaef` | **0.2114** | Normal | Standard transaction |
| `tx_norm_555_95b609c6` | **0.2113** | Normal | Standard transaction |
| `tx_norm_1407_c2b39a94` | **0.2113** | Normal | Standard transaction |
| `tx_norm_1730_dcb50a2c` | **0.2112** | Normal | Standard transaction |
| `tx_norm_1691_37ed586a` | **0.2110** | Normal | Standard transaction |
| `tx_norm_1953_73d6d619` | **0.2109** | Normal | Standard transaction |
| `tx_norm_1206_f15d8722` | **0.2107** | Normal | Standard transaction |
| `tx_norm_70_8357898b` | **0.2105** | Normal | Standard transaction |
| `tx_norm_180_61d88a27` | **0.2104** | Normal | Standard transaction |
| `tx_norm_974_f60b7d33` | **0.2104** | Normal | Standard transaction |
| `tx_norm_1989_1d56c038` | **0.2103** | Normal | Standard transaction |
| `tx_norm_1882_f8e63812` | **0.2102** | Normal | Standard transaction |
| `tx_norm_2547_252fcb1e` | **0.2101** | Normal | Standard transaction |
| `tx_norm_2431_acf4d160` | **0.2100** | Normal | Standard transaction |
| `tx_norm_356_e5233865` | **0.2099** | Normal | Standard transaction |
| `tx_norm_1098_2bc78329` | **0.2099** | Normal | Standard transaction |
| `tx_norm_472_21f81d3a` | **0.2098** | Normal | Standard transaction |
| `tx_norm_388_02e2fe6e` | **0.2097** | Normal | Standard transaction |
| `tx_norm_1947_ed035111` | **0.2097** | Normal | Standard transaction |
| `tx_norm_1726_94422952` | **0.2095** | Normal | Standard transaction |
| `tx_norm_1540_e7020279` | **0.2092** | Normal | Standard transaction |
| `tx_norm_1854_5fdc677c` | **0.2092** | Normal | Standard transaction |
| `tx_norm_1309_4179380c` | **0.2090** | Normal | Standard transaction |
| `tx_norm_2482_59b86c2a` | **0.2089** | Normal | Standard transaction |
| `tx_norm_2515_a73d1dc8` | **0.2087** | Normal | Standard transaction |
| `tx_norm_2133_c0796ea9` | **0.2083** | Normal | Standard transaction |
| `tx_norm_1166_14857afc` | **0.2080** | Normal | Standard transaction |
| `tx_norm_2411_29b5aa46` | **0.2080** | Normal | Standard transaction |
| `tx_norm_1903_e95c7955` | **0.2078** | Normal | Standard transaction |
| `tx_norm_2500_8cb44523` | **0.2077** | Normal | Standard transaction |
| `tx_norm_2111_ef925c4f` | **0.2076** | Normal | Standard transaction |
| `tx_norm_2116_a1a356cf` | **0.2076** | Normal | Standard transaction |
| `tx_norm_2255_13cee317` | **0.2073** | Normal | Standard transaction |
| `tx_norm_296_cdd22991` | **0.2072** | Normal | Standard transaction |
| `tx_norm_121_b4175862` | **0.2071** | Normal | Standard transaction |
| `tx_norm_276_0349d4cd` | **0.2071** | Normal | Standard transaction |
| `tx_norm_1391_c8d0bafb` | **0.2071** | Normal | Standard transaction |
| `tx_norm_234_55f4be32` | **0.2070** | Normal | Standard transaction |
| `tx_norm_626_92466b73` | **0.2069** | Normal | Standard transaction |
| `tx_norm_1480_c17c8447` | **0.2068** | Normal | Standard transaction |
| `tx_norm_2495_19744dbd` | **0.2068** | Normal | Standard transaction |
| `tx_norm_1373_35ea6821` | **0.2067** | Normal | Standard transaction |
| `tx_norm_1619_dbb7238a` | **0.2065** | Normal | Standard transaction |
| `tx_norm_2137_c29db87b` | **0.2065** | Normal | Standard transaction |
| `tx_norm_897_e6ec8c07` | **0.2062** | Normal | Standard transaction |
| `tx_norm_2053_6a900eae` | **0.2062** | Normal | Standard transaction |
| `tx_norm_2512_746a111b` | **0.2062** | Normal | Standard transaction |
| `tx_norm_914_2882bb92` | **0.2058** | Normal | Standard transaction |
| `tx_norm_772_811d51ba` | **0.2054** | Normal | Standard transaction |
| `tx_norm_805_590b920c` | **0.2054** | Normal | Standard transaction |
| `tx_norm_198_9aceb031` | **0.2050** | Normal | Standard transaction |
| `tx_norm_2487_5d2ceaa0` | **0.2049** | Normal | Standard transaction |
| `tx_norm_340_a37f1ce5` | **0.2048** | Normal | Standard transaction |
| `tx_norm_1398_c5f62405` | **0.2048** | Normal | Standard transaction |
| `tx_norm_2469_0d1a8eeb` | **0.2046** | Normal | Standard transaction |
| `tx_norm_2583_f724e143` | **0.2043** | Normal | Standard transaction |
| `tx_norm_1924_fee63d41` | **0.2042** | Normal | Standard transaction |
| `tx_norm_2036_cf5e6e1d` | **0.2039** | Normal | Standard transaction |
| `tx_norm_493_64043a6b` | **0.2038** | Normal | Standard transaction |
| `tx_norm_867_221bb235` | **0.2038** | Normal | Standard transaction |
| `tx_norm_1737_5a69e3d0` | **0.2038** | Normal | Standard transaction |
| `tx_norm_4_ab023763` | **0.2037** | Normal | Standard transaction |
| `tx_norm_492_ecddb2a7` | **0.2035** | Normal | Standard transaction |
| `tx_norm_1209_6f3c9b39` | **0.2034** | Normal | Standard transaction |
| `tx_norm_134_c38204b5` | **0.2032** | Normal | Standard transaction |
| `tx_norm_1723_666f68a7` | **0.2032** | Normal | Standard transaction |
| `tx_norm_2440_9a31a6b6` | **0.2026** | Normal | Standard transaction |
| `tx_norm_2338_3bd6aff1` | **0.2024** | Normal | Standard transaction |
| `tx_norm_2362_88fbafea` | **0.2024** | Normal | Standard transaction |
| `tx_norm_1929_5ac2deeb` | **0.2022** | Normal | Standard transaction |
| `tx_norm_175_8b369987` | **0.2021** | Normal | Standard transaction |
| `tx_norm_827_1cf16e06` | **0.2021** | Normal | Standard transaction |
| `tx_norm_1625_122c7834` | **0.2021** | Normal | Standard transaction |
| `tx_norm_2015_7f5668e4` | **0.2020** | Normal | Standard transaction |
| `tx_norm_865_c93b7466` | **0.2019** | Normal | Standard transaction |
| `tx_norm_374_30bbf5c5` | **0.2018** | Normal | Standard transaction |
| `tx_norm_1109_9523e7f3` | **0.2018** | Normal | Standard transaction |
| `tx_norm_1500_065745b7` | **0.2018** | Normal | Standard transaction |
| `tx_norm_1558_f72dbadd` | **0.2016** | Normal | Standard transaction |
| `tx_norm_1207_a03af1db` | **0.2012** | Normal | Standard transaction |
| `tx_norm_2617_d8a37958` | **0.2011** | Normal | Standard transaction |
| `tx_norm_589_83f63e29` | **0.2010** | Normal | Standard transaction |
| `tx_norm_530_b8cb4be1` | **0.2008** | Normal | Standard transaction |
| `tx_norm_2150_6f84c014` | **0.2008** | Normal | Standard transaction |
| `tx_norm_1078_4afc0d7f` | **0.2007** | Normal | Standard transaction |
| `tx_norm_386_0c74b6e8` | **0.2005** | Normal | Standard transaction |
| `tx_norm_913_0c513e34` | **0.2005** | Normal | Standard transaction |
| `tx_norm_1465_861d4bca` | **0.2002** | Normal | Standard transaction |
| `tx_norm_1492_040302f1` | **0.2000** | Normal | Standard transaction |
| `tx_norm_1878_2ebe59e4` | **0.1998** | Normal | Standard transaction |
| `tx_norm_220_6ef22d7a` | **0.1994** | Normal | Standard transaction |
| `tx_norm_329_4a70ab06` | **0.1994** | Normal | Standard transaction |
| `tx_norm_1160_5ec97373` | **0.1994** | Normal | Standard transaction |
| `tx_norm_1743_1328c322` | **0.1994** | Normal | Standard transaction |
| `tx_norm_717_0a06197d` | **0.1993** | Normal | Standard transaction |
| `tx_norm_1753_ecb2a771` | **0.1993** | Normal | Standard transaction |
| `tx_norm_944_4b9a997c` | **0.1992** | Normal | Standard transaction |
| `tx_norm_197_3c3c4853` | **0.1991** | Normal | Standard transaction |
| `tx_norm_90_4f720add` | **0.1989** | Normal | Standard transaction |
| `tx_norm_1430_8dca6360` | **0.1989** | Normal | Standard transaction |
| `tx_norm_2277_c07439bf` | **0.1986** | Normal | Standard transaction |
| `tx_norm_1450_942aa336` | **0.1985** | Normal | Standard transaction |
| `tx_norm_457_82991ac3` | **0.1984** | Normal | Standard transaction |
| `tx_norm_1813_bde73fe7` | **0.1984** | Normal | Standard transaction |
| `tx_norm_143_7b1bacc3` | **0.1980** | Normal | Standard transaction |
| `tx_norm_172_2cdabcfe` | **0.1980** | Normal | Standard transaction |
| `tx_norm_892_accd00ac` | **0.1978** | Normal | Standard transaction |
| `tx_norm_1923_d38fe90d` | **0.1974** | Normal | Standard transaction |
| `tx_norm_794_91086b69` | **0.1972** | Normal | Standard transaction |
| `tx_norm_2633_f6378166` | **0.1971** | Normal | Standard transaction |
| `tx_norm_283_f61751a9` | **0.1970** | Normal | Standard transaction |
| `tx_norm_720_2459b82c` | **0.1969** | Normal | Standard transaction |
| `tx_norm_2163_f300ac02` | **0.1969** | Normal | Standard transaction |
| `tx_norm_1253_e080efb0` | **0.1968** | Normal | Standard transaction |
| `tx_norm_2526_ddb849c2` | **0.1968** | Normal | Standard transaction |
| `tx_norm_237_c74b0368` | **0.1966** | Normal | Standard transaction |
| `tx_norm_871_40a71540` | **0.1965** | Normal | Standard transaction |
| `tx_norm_1798_fdea17b1` | **0.1964** | Normal | Standard transaction |
| `tx_norm_1285_c9d3dc3a` | **0.1958** | Normal | Standard transaction |
| `tx_norm_488_ba5f28ff` | **0.1954** | Normal | Standard transaction |
| `tx_norm_1332_2a07fb94` | **0.1954** | Normal | Standard transaction |
| `tx_norm_242_c33abc27` | **0.1952** | Normal | Standard transaction |
| `tx_norm_51_c916fc1a` | **0.1950** | Normal | Standard transaction |
| `tx_norm_2486_9428934f` | **0.1949** | Normal | Standard transaction |
| `tx_norm_243_cc7baf1f` | **0.1948** | Normal | Standard transaction |
| `tx_norm_2591_5a47edfb` | **0.1948** | Normal | Standard transaction |
| `tx_norm_1248_97625497` | **0.1944** | Normal | Standard transaction |
| `tx_norm_2056_123eec14` | **0.1943** | Normal | Standard transaction |
| `tx_norm_1831_9b2ef574` | **0.1942** | Normal | Standard transaction |
| `tx_norm_462_bc5b00a2` | **0.1939** | Normal | Standard transaction |
| `tx_norm_1323_95cfe9da` | **0.1937** | Normal | Standard transaction |
| `tx_norm_972_94e0daa5` | **0.1933** | Normal | Standard transaction |
| `tx_norm_2413_737e3068` | **0.1933** | Normal | Standard transaction |
| `tx_norm_550_ad4a952d` | **0.1929** | Normal | Standard transaction |
| `tx_norm_229_575d6a9d` | **0.1928** | Normal | Standard transaction |
| `tx_norm_848_ee20a715` | **0.1927** | Normal | Standard transaction |
| `tx_norm_2196_8d33be41` | **0.1927** | Normal | Standard transaction |
| `tx_norm_502_508ed95d` | **0.1926** | Normal | Standard transaction |
| `tx_norm_842_50f0c839` | **0.1924** | Normal | Standard transaction |
| `tx_norm_526_8e921126` | **0.1923** | Normal | Standard transaction |
| `tx_norm_1103_af3595b5` | **0.1922** | Normal | Standard transaction |
| `tx_norm_1711_faf7dfcd` | **0.1921** | Normal | Standard transaction |
| `tx_norm_1703_7bec445d` | **0.1920** | Normal | Standard transaction |
| `tx_norm_2069_50daee23` | **0.1919** | Normal | Standard transaction |
| `tx_norm_774_31772dcc` | **0.1917** | Normal | Standard transaction |
| `tx_norm_2510_cd9baec0` | **0.1917** | Normal | Standard transaction |
| `tx_norm_1900_ba0ed80a` | **0.1914** | Normal | Standard transaction |
| `tx_norm_776_5ef1fefb` | **0.1913** | Normal | Standard transaction |
| `tx_norm_360_36f0d4ac` | **0.1912** | Normal | Standard transaction |
| `tx_norm_1454_ec5d0e01` | **0.1912** | Normal | Standard transaction |
| `tx_norm_2160_e7dba6da` | **0.1912** | Normal | Standard transaction |
| `tx_norm_30_bf782c39` | **0.1910** | Normal | Standard transaction |
| `tx_norm_751_67b5e4eb` | **0.1910** | Normal | Standard transaction |
| `tx_norm_1029_36a84cdd` | **0.1910** | Normal | Standard transaction |
| `tx_norm_557_12120168` | **0.1909** | Normal | Standard transaction |
| `tx_norm_346_8375f7b5` | **0.1908** | Normal | Standard transaction |
| `tx_norm_349_0285e01e` | **0.1908** | Normal | Standard transaction |
| `tx_norm_503_4d3d9ad3` | **0.1907** | Normal | Standard transaction |
| `tx_norm_1333_1356d9bb` | **0.1904** | Normal | Standard transaction |
| `tx_norm_1039_68da2cbe` | **0.1899** | Normal | Standard transaction |
| `tx_norm_779_59a1f2bb` | **0.1897** | Normal | Standard transaction |
| `tx_norm_392_6b1439ed` | **0.1896** | Normal | Standard transaction |
| `tx_norm_1930_ce7d965a` | **0.1896** | Normal | Standard transaction |
| `tx_norm_2297_ebc20fd8` | **0.1896** | Normal | Standard transaction |
| `tx_norm_2541_34d56270` | **0.1896** | Normal | Standard transaction |
| `tx_norm_1301_fbef7bd9` | **0.1894** | Normal | Standard transaction |
| `tx_norm_1969_c8ca51dc` | **0.1894** | Normal | Standard transaction |
| `tx_norm_1176_2e724b87` | **0.1893** | Normal | Standard transaction |
| `tx_norm_1800_b59528d2` | **0.1893** | Normal | Standard transaction |
| `tx_norm_790_45bf1190` | **0.1892** | Normal | Standard transaction |
| `tx_norm_337_72a06996` | **0.1891** | Normal | Standard transaction |
| `tx_norm_975_2dd2595b` | **0.1886** | Normal | Standard transaction |
| `tx_norm_701_d611e2d6` | **0.1884** | Normal | Standard transaction |
| `tx_norm_969_eba88fde` | **0.1882** | Normal | Standard transaction |
| `tx_norm_378_be3e6338` | **0.1878** | Normal | Standard transaction |
| `tx_norm_149_6703f01e` | **0.1877** | Normal | Standard transaction |
| `tx_norm_2632_190743ce` | **0.1877** | Normal | Standard transaction |
| `tx_norm_307_175d6854` | **0.1874** | Normal | Standard transaction |
| `tx_norm_1549_0fdc1685` | **0.1871** | Normal | Standard transaction |
| `tx_norm_2228_eef47216` | **0.1871** | Normal | Standard transaction |
| `tx_norm_84_ca329aa1` | **0.1870** | Normal | Standard transaction |
| `tx_norm_809_6e10dbf3` | **0.1870** | Normal | Standard transaction |
| `tx_norm_898_1c1ff6f0` | **0.1866** | Normal | Standard transaction |
| `tx_norm_1852_f8e4b9f5` | **0.1864** | Normal | Standard transaction |
| `tx_norm_1683_155b52ac` | **0.1862** | Normal | Standard transaction |
| `tx_norm_1385_86fefb2c` | **0.1860** | Normal | Standard transaction |
| `tx_norm_1917_6a59b643` | **0.1860** | Normal | Standard transaction |
| `tx_norm_1471_31e9ee24` | **0.1859** | Normal | Standard transaction |
| `tx_norm_21_0b22f6e2` | **0.1858** | Normal | Standard transaction |
| `tx_norm_1579_fe6939b5` | **0.1858** | Normal | Standard transaction |
| `tx_norm_1970_7c7f4bb5` | **0.1858** | Normal | Standard transaction |
| `tx_norm_1357_4053898e` | **0.1857** | Normal | Standard transaction |
| `tx_norm_2124_9fe28cd6` | **0.1855** | Normal | Standard transaction |
| `tx_norm_434_0d3dd972` | **0.1853** | Normal | Standard transaction |
| `tx_norm_1784_0ad22370` | **0.1853** | Normal | Standard transaction |
| `tx_norm_2171_a3348ffa` | **0.1848** | Normal | Standard transaction |
| `tx_norm_292_8dc63f6b` | **0.1847** | Normal | Standard transaction |
| `tx_norm_2263_8fc86155` | **0.1847** | Normal | Standard transaction |
| `tx_norm_102_fb8516d7` | **0.1845** | Normal | Standard transaction |
| `tx_norm_1026_1e6f5ff3` | **0.1845** | Normal | Standard transaction |
| `tx_norm_2093_f98ca205` | **0.1842** | Normal | Standard transaction |
| `tx_norm_278_7ea95e61` | **0.1841** | Normal | Standard transaction |
| `tx_norm_839_216054d3` | **0.1841** | Normal | Standard transaction |
| `tx_norm_1545_ba8cdc40` | **0.1841** | Normal | Standard transaction |
| `tx_norm_959_0ca19bee` | **0.1838** | Normal | Standard transaction |
| `tx_norm_2115_d6c05c7b` | **0.1838** | Normal | Standard transaction |
| `tx_norm_667_289645f9` | **0.1835** | Normal | Standard transaction |
| `tx_norm_807_d24dba0a` | **0.1835** | Normal | Standard transaction |
| `tx_norm_1042_cd57306c` | **0.1835** | Normal | Standard transaction |
| `tx_norm_1914_a8183d79` | **0.1834** | Normal | Standard transaction |
| `tx_norm_983_9f70f4c0` | **0.1830** | Normal | Standard transaction |
| `tx_norm_2490_e4ca7019` | **0.1829** | Normal | Standard transaction |
| `tx_norm_1297_10357b38` | **0.1828** | Normal | Standard transaction |
| `tx_norm_128_88994697` | **0.1827** | Normal | Standard transaction |
| `tx_norm_9_964d0249` | **0.1826** | Normal | Standard transaction |
| `tx_norm_113_a7309dfc` | **0.1824** | Normal | Standard transaction |
| `tx_norm_2446_f6132fc5` | **0.1822** | Normal | Standard transaction |
| `tx_norm_1593_b1b51473` | **0.1814** | Normal | Standard transaction |
| `tx_norm_415_1b7a5eb8` | **0.1812** | Normal | Standard transaction |
| `tx_norm_1649_8a3e884b` | **0.1812** | Normal | Standard transaction |
| `tx_norm_726_c7cddb11` | **0.1811** | Normal | Standard transaction |
| `tx_norm_1283_5d205702` | **0.1811** | Normal | Standard transaction |
| `tx_norm_1794_79630587` | **0.1811** | Normal | Standard transaction |
| `tx_norm_952_35ae03f4` | **0.1810** | Normal | Standard transaction |
| `tx_norm_218_8b4615bb` | **0.1809** | Normal | Standard transaction |
| `tx_norm_675_5395845d` | **0.1809** | Normal | Standard transaction |
| `tx_norm_1143_f87e740c` | **0.1809** | Normal | Standard transaction |
| `tx_norm_1517_d76f024a` | **0.1808** | Normal | Standard transaction |
| `tx_norm_2478_98b52aa7` | **0.1808** | Normal | Standard transaction |
| `tx_norm_816_4289accf` | **0.1806** | Normal | Standard transaction |
| `tx_norm_1202_4cbedf49` | **0.1806** | Normal | Standard transaction |
| `tx_norm_1460_330ad6f5` | **0.1802** | Normal | Standard transaction |
| `tx_norm_500_70ad77d7` | **0.1801** | Normal | Standard transaction |
| `tx_norm_543_c63986b6` | **0.1800** | Normal | Standard transaction |
| `tx_norm_1472_f5bf6465` | **0.1800** | Normal | Standard transaction |
| `tx_norm_262_4acab344` | **0.1797** | Normal | Standard transaction |
| `tx_norm_2037_10a80660` | **0.1797** | Normal | Standard transaction |
| `tx_norm_214_634d5fd3` | **0.1793** | Normal | Standard transaction |
| `tx_norm_632_d9ffa013` | **0.1793** | Normal | Standard transaction |
| `tx_norm_2536_e8508a92` | **0.1792** | Normal | Standard transaction |
| `tx_norm_1533_e5a7832c` | **0.1789** | Normal | Standard transaction |
| `tx_norm_1174_987550a2` | **0.1788** | Normal | Standard transaction |
| `tx_norm_473_b2b097cb` | **0.1787** | Normal | Standard transaction |
| `tx_norm_908_0595816b` | **0.1782** | Normal | Standard transaction |
| `tx_norm_1435_5884394d` | **0.1782** | Normal | Standard transaction |
| `tx_norm_856_a8dce5ab` | **0.1781** | Normal | Standard transaction |
| `tx_norm_973_79ba46d6` | **0.1780** | Normal | Standard transaction |
| `tx_norm_989_b0030b19` | **0.1780** | Normal | Standard transaction |
| `tx_norm_1643_772b3d2d` | **0.1780** | Normal | Standard transaction |
| `tx_norm_834_8bc39181` | **0.1778** | Normal | Standard transaction |
| `tx_norm_1792_f9ab9c86` | **0.1778** | Normal | Standard transaction |
| `tx_norm_1082_e94513b9` | **0.1776** | Normal | Standard transaction |
| `tx_norm_2464_56452f5d` | **0.1776** | Normal | Standard transaction |
| `tx_norm_257_f90beef8` | **0.1774** | Normal | Standard transaction |
| `tx_norm_2625_f50ea03c` | **0.1774** | Normal | Standard transaction |
| `tx_norm_1673_4f2f6137` | **0.1772** | Normal | Standard transaction |
| `tx_norm_2235_224b7ac3` | **0.1772** | Normal | Standard transaction |
| `tx_norm_255_3b944490` | **0.1771** | Normal | Standard transaction |
| `tx_norm_741_59499a82` | **0.1771** | Normal | Standard transaction |
| `tx_norm_1809_36cfb7c3` | **0.1771** | Normal | Standard transaction |
| `tx_norm_1695_a2e59dcb` | **0.1770** | Normal | Standard transaction |
| `tx_norm_225_0fb5aca0` | **0.1768** | Normal | Standard transaction |
| `tx_norm_692_e2bf11f2` | **0.1767** | Normal | Standard transaction |
| `tx_norm_925_9815200c` | **0.1766** | Normal | Standard transaction |
| `tx_norm_467_14d81b33` | **0.1762** | Normal | Standard transaction |
| `tx_norm_2139_6c1caef2` | **0.1761** | Normal | Standard transaction |
| `tx_norm_1522_77a80abc` | **0.1759** | Normal | Standard transaction |
| `tx_norm_1441_42752c79` | **0.1757** | Normal | Standard transaction |
| `tx_norm_2103_f96c2328` | **0.1754** | Normal | Standard transaction |
| `tx_norm_2552_2ce8c36c` | **0.1753** | Normal | Standard transaction |
| `tx_norm_1013_60eca47d` | **0.1752** | Normal | Standard transaction |
| `tx_norm_1156_909bd878` | **0.1751** | Normal | Standard transaction |
| `tx_norm_416_0421b273` | **0.1750** | Normal | Standard transaction |
| `tx_norm_2448_7b413fbf` | **0.1750** | Normal | Standard transaction |
| `tx_norm_1095_30fbb90c` | **0.1749** | Normal | Standard transaction |
| `tx_norm_6_c3048104` | **0.1748** | Normal | Standard transaction |
| `tx_norm_1203_cce61911` | **0.1748** | Normal | Standard transaction |
| `tx_norm_1884_e5148622` | **0.1748** | Normal | Standard transaction |
| `tx_norm_2019_7ac396a2` | **0.1748** | Normal | Standard transaction |
| `tx_norm_1336_a470f905` | **0.1738** | Normal | Standard transaction |
| `tx_norm_2296_09a753b9` | **0.1736** | Normal | Standard transaction |
| `tx_norm_835_cb7a3143` | **0.1732** | Normal | Standard transaction |
| `tx_norm_1904_00631e63` | **0.1729** | Normal | Standard transaction |
| `tx_norm_1495_2ac92aad` | **0.1727** | Normal | Standard transaction |
| `tx_norm_480_f1eef394` | **0.1726** | Normal | Standard transaction |
| `tx_norm_576_a0d27917` | **0.1726** | Normal | Standard transaction |
| `tx_norm_1948_1763b11b` | **0.1725** | Normal | Standard transaction |
| `tx_norm_1954_4ac5c18d` | **0.1725** | Normal | Standard transaction |
| `tx_norm_1108_c3d77245` | **0.1724** | Normal | Standard transaction |
| `tx_norm_1344_307ba7c9` | **0.1724** | Normal | Standard transaction |
| `tx_norm_230_4e59bc50` | **0.1723** | Normal | Standard transaction |
| `tx_norm_1886_6182ec16` | **0.1721** | Normal | Standard transaction |
| `tx_norm_723_f12fb57d` | **0.1720** | Normal | Standard transaction |
| `tx_norm_1732_4555c61c` | **0.1720** | Normal | Standard transaction |
| `tx_norm_1158_4bef93dd` | **0.1716** | Normal | Standard transaction |
| `tx_norm_1553_6fe175d5` | **0.1716** | Normal | Standard transaction |
| `tx_norm_529_6ea6023a` | **0.1714** | Normal | Standard transaction |
| `tx_norm_1243_bb8c8419` | **0.1714** | Normal | Standard transaction |
| `tx_norm_2311_2f1637ab` | **0.1713** | Normal | Standard transaction |
| `tx_norm_325_0e60beb3` | **0.1708** | Normal | Standard transaction |
| `tx_norm_1062_02d6203c` | **0.1708** | Normal | Standard transaction |
| `tx_norm_1201_24d3997c` | **0.1708** | Normal | Standard transaction |
| `tx_norm_1163_ef2bb0bd` | **0.1707** | Normal | Standard transaction |
| `tx_norm_254_0c4d4679` | **0.1706** | Normal | Standard transaction |
| `tx_norm_595_2b183de5` | **0.1704** | Normal | Standard transaction |
| `tx_norm_1589_7fbde77d` | **0.1703** | Normal | Standard transaction |
| `tx_norm_2463_a3b2925c` | **0.1703** | Normal | Standard transaction |
| `tx_norm_637_981e4c2f` | **0.1702** | Normal | Standard transaction |
| `tx_norm_1269_b8f6a1a0` | **0.1702** | Normal | Standard transaction |
| `tx_norm_2199_c72af64c` | **0.1702** | Normal | Standard transaction |
| `tx_norm_2607_82228f22` | **0.1702** | Normal | Standard transaction |
| `tx_norm_1392_a1574f21` | **0.1701** | Normal | Standard transaction |
| `tx_norm_1473_de59f4e2` | **0.1699** | Normal | Standard transaction |
| `tx_norm_1338_8d196a2e` | **0.1697** | Normal | Standard transaction |
| `tx_norm_1352_a9234339` | **0.1697** | Normal | Standard transaction |
| `tx_norm_1839_6593d3a4` | **0.1697** | Normal | Standard transaction |
| `tx_norm_1935_87e52758` | **0.1696** | Normal | Standard transaction |
| `tx_norm_1783_4af1edcf` | **0.1693** | Normal | Standard transaction |
| `tx_norm_534_5ab09b5f` | **0.1692** | Normal | Standard transaction |
| `tx_norm_893_c68972e1` | **0.1691** | Normal | Standard transaction |
| `tx_norm_460_e7268e12` | **0.1690** | Normal | Standard transaction |
| `tx_norm_2508_1c7a7f3e` | **0.1689** | Normal | Standard transaction |
| `tx_norm_439_b4a4833f` | **0.1688** | Normal | Standard transaction |
| `tx_norm_236_4931c3a2` | **0.1687** | Normal | Standard transaction |
| `tx_norm_1623_5b132f80` | **0.1680** | Normal | Standard transaction |
| `tx_norm_1600_08fc5557` | **0.1679** | Normal | Standard transaction |
| `tx_norm_1217_63fdf0f4` | **0.1678** | Normal | Standard transaction |
| `tx_norm_219_7ba08274` | **0.1676** | Normal | Standard transaction |
| `tx_norm_80_690b46fe` | **0.1675** | Normal | Standard transaction |
| `tx_norm_65_50a58336` | **0.1674** | Normal | Standard transaction |
| `tx_norm_2227_42a199d3` | **0.1674** | Normal | Standard transaction |
| `tx_norm_2022_6458e5fa` | **0.1673** | Normal | Standard transaction |
| `tx_norm_2251_8e76d4d4` | **0.1672** | Normal | Standard transaction |
| `tx_norm_2186_3e18d685` | **0.1670** | Normal | Standard transaction |
| `tx_norm_1059_d6b242f5` | **0.1669** | Normal | Standard transaction |
| `tx_norm_2003_185ccd34` | **0.1668** | Normal | Standard transaction |
| `tx_norm_2628_da4d4e58` | **0.1668** | Normal | Standard transaction |
| `tx_norm_1436_1f07f8cd` | **0.1667** | Normal | Standard transaction |
| `tx_norm_2209_e371f3bf` | **0.1666** | Normal | Standard transaction |
| `tx_norm_409_de9fdd1e` | **0.1661** | Normal | Standard transaction |
| `tx_norm_2016_d3463121` | **0.1661** | Normal | Standard transaction |
| `tx_norm_1060_3b75e4ac` | **0.1659** | Normal | Standard transaction |
| `tx_norm_1046_2ae0ae15` | **0.1658** | Normal | Standard transaction |
| `tx_norm_381_b8b366e1` | **0.1655** | Normal | Standard transaction |
| `tx_norm_2300_f0c56678` | **0.1654** | Normal | Standard transaction |
| `tx_norm_280_84a941e4` | **0.1652** | Normal | Standard transaction |
| `tx_norm_2302_b5971dc2` | **0.1652** | Normal | Standard transaction |
| `tx_norm_1898_ffac62b7` | **0.1649** | Normal | Standard transaction |
| `tx_norm_560_aac43242` | **0.1646** | Normal | Standard transaction |
| `tx_norm_1459_b9c29099` | **0.1646** | Normal | Standard transaction |
| `tx_norm_1368_70ad3d06` | **0.1645** | Normal | Standard transaction |
| `tx_norm_851_605a6d86` | **0.1642** | Normal | Standard transaction |
| `tx_norm_953_97c32163` | **0.1642** | Normal | Standard transaction |
| `tx_norm_2013_6bc22cb1` | **0.1641** | Normal | Standard transaction |
| `tx_norm_2059_021f01b6` | **0.1638** | Normal | Standard transaction |
| `tx_norm_2384_95a017af` | **0.1634** | Normal | Standard transaction |
| `tx_norm_629_549a1675` | **0.1631** | Normal | Standard transaction |
| `tx_norm_306_2f02f171` | **0.1629** | Normal | Standard transaction |
| `tx_norm_1899_064c85bd` | **0.1628** | Normal | Standard transaction |
| `tx_norm_246_2b1daf53` | **0.1627** | Normal | Standard transaction |
| `tx_norm_1821_e831bdc1` | **0.1626** | Normal | Standard transaction |
| `tx_norm_2045_be1a3d41` | **0.1626** | Normal | Standard transaction |
| `tx_norm_1347_dac99254` | **0.1625** | Normal | Standard transaction |
| `tx_norm_2314_02df52dc` | **0.1625** | Normal | Standard transaction |
| `tx_norm_269_9383b1b3` | **0.1619** | Normal | Standard transaction |
| `tx_norm_2183_6e0172e2` | **0.1618** | Normal | Standard transaction |
| `tx_norm_1390_17864fd7` | **0.1617** | Normal | Standard transaction |
| `tx_norm_2481_3182275a` | **0.1616** | Normal | Standard transaction |
| `tx_norm_634_d6349c47` | **0.1615** | Normal | Standard transaction |
| `tx_norm_2627_a7188341` | **0.1613** | Normal | Standard transaction |
| `tx_norm_92_95bb2540` | **0.1611** | Normal | Standard transaction |
| `tx_norm_1521_f30c7601` | **0.1608** | Normal | Standard transaction |
| `tx_norm_1456_ce69c97e` | **0.1607** | Normal | Standard transaction |
| `tx_norm_2590_0659aa3b` | **0.1606** | Normal | Standard transaction |
| `tx_norm_2214_961564d6` | **0.1604** | Normal | Standard transaction |
| `tx_norm_1153_97f0e400` | **0.1601** | Normal | Standard transaction |
| `tx_norm_2447_66726437` | **0.1599** | Normal | Standard transaction |
| `tx_norm_2223_8e83f8c9` | **0.1598** | Normal | Standard transaction |
| `tx_norm_206_2b09503c` | **0.1597** | Normal | Standard transaction |
| `tx_norm_1952_97454e80` | **0.1597** | Normal | Standard transaction |
| `tx_norm_1053_db7c7ba0` | **0.1595** | Normal | Standard transaction |
| `tx_norm_489_16ce85b2` | **0.1593** | Normal | Standard transaction |
| `tx_norm_2325_26a81934` | **0.1593** | Normal | Standard transaction |
| `tx_norm_357_945001f6` | **0.1592** | Normal | Standard transaction |
| `tx_norm_620_42d81ef5` | **0.1592** | Normal | Standard transaction |
| `tx_norm_1236_665df059` | **0.1592** | Normal | Standard transaction |
| `tx_norm_324_82b0e803` | **0.1590** | Normal | Standard transaction |
| `tx_norm_2498_79d74e55` | **0.1589** | Normal | Standard transaction |
| `tx_norm_754_3cdd8f71` | **0.1588** | Normal | Standard transaction |
| `tx_norm_1693_b79c0212` | **0.1585** | Normal | Standard transaction |
| `tx_norm_1210_573d51bc` | **0.1582** | Normal | Standard transaction |
| `tx_norm_1951_7a61e640` | **0.1581** | Normal | Standard transaction |
| `tx_norm_159_1731f0af` | **0.1580** | Normal | Standard transaction |
| `tx_norm_1447_bb02db3b` | **0.1580** | Normal | Standard transaction |
| `tx_norm_118_06fa46a0` | **0.1579** | Normal | Standard transaction |
| `tx_norm_1971_ad55ef66` | **0.1579** | Normal | Standard transaction |
| `tx_norm_1342_6f950529` | **0.1578** | Normal | Standard transaction |
| `tx_norm_2341_043070f7` | **0.1578** | Normal | Standard transaction |
| `tx_norm_11_6dc02884` | **0.1574** | Normal | Standard transaction |
| `tx_norm_1591_77d82ad8` | **0.1573** | Normal | Standard transaction |
| `tx_norm_1864_e05a994f` | **0.1571** | Normal | Standard transaction |
| `tx_norm_1306_c014539a` | **0.1570** | Normal | Standard transaction |
| `tx_norm_1845_08a8347e` | **0.1569** | Normal | Standard transaction |
| `tx_norm_1192_ca4a137a` | **0.1565** | Normal | Standard transaction |
| `tx_norm_822_1194a7a0` | **0.1561** | Normal | Standard transaction |
| `tx_norm_548_0c32833e` | **0.1560** | Normal | Standard transaction |
| `tx_norm_597_eb65adaf` | **0.1560** | Normal | Standard transaction |
| `tx_norm_2011_4c686af9` | **0.1560** | Normal | Standard transaction |
| `tx_norm_1335_f5520ed5` | **0.1559** | Normal | Standard transaction |
| `tx_norm_1902_5597ab61` | **0.1559** | Normal | Standard transaction |
| `tx_norm_2320_564ffda8` | **0.1559** | Normal | Standard transaction |
| `tx_norm_1401_17d88973` | **0.1557** | Normal | Standard transaction |
| `tx_norm_2517_3d2e1e1a` | **0.1557** | Normal | Standard transaction |
| `tx_norm_558_f22554cc` | **0.1556** | Normal | Standard transaction |
| `tx_norm_1076_86f41d82` | **0.1556** | Normal | Standard transaction |
| `tx_norm_2270_d19c2353` | **0.1554** | Normal | Standard transaction |
| `tx_norm_221_e68bf82b` | **0.1553** | Normal | Standard transaction |
| `tx_norm_866_7a91ae30` | **0.1553** | Normal | Standard transaction |
| `tx_norm_265_af440c0d` | **0.1548** | Normal | Standard transaction |
| `tx_norm_1470_1b8027db` | **0.1548** | Normal | Standard transaction |
| `tx_norm_1617_ced3fdb4` | **0.1548** | Normal | Standard transaction |
| `tx_norm_2528_672d4b23` | **0.1548** | Normal | Standard transaction |
| `tx_norm_2586_b3391660` | **0.1548** | Normal | Standard transaction |
| `tx_norm_210_e16e2e5c` | **0.1547** | Normal | Standard transaction |
| `tx_norm_2496_d4b9b986` | **0.1547** | Normal | Standard transaction |
| `tx_norm_452_505013ea` | **0.1545** | Normal | Standard transaction |
| `tx_norm_1879_99511a5a` | **0.1545** | Normal | Standard transaction |
| `tx_norm_2079_76e10128` | **0.1542** | Normal | Standard transaction |
| `tx_norm_413_ae891545` | **0.1541** | Normal | Standard transaction |
| `tx_norm_872_be315744` | **0.1540** | Normal | Standard transaction |
| `tx_norm_1563_3f54e4d5` | **0.1540** | Normal | Standard transaction |
| `tx_norm_1943_6b98acb4` | **0.1540** | Normal | Standard transaction |
| `tx_norm_446_98c7fe06` | **0.1539** | Normal | Standard transaction |
| `tx_norm_551_256c0304` | **0.1539** | Normal | Standard transaction |
| `tx_norm_1851_0e14135e` | **0.1539** | Normal | Standard transaction |
| `tx_norm_277_42dde209` | **0.1538** | Normal | Standard transaction |
| `tx_norm_2250_8a80b840` | **0.1536** | Normal | Standard transaction |
| `tx_norm_433_762e4977` | **0.1533** | Normal | Standard transaction |
| `tx_norm_1136_f11faddb` | **0.1533** | Normal | Standard transaction |
| `tx_norm_2535_7bf78684` | **0.1533** | Normal | Standard transaction |
| `tx_norm_1351_63494b33` | **0.1532** | Normal | Standard transaction |
| `tx_norm_1238_8ff16a7b` | **0.1531** | Normal | Standard transaction |
| `tx_norm_256_0f3226d9` | **0.1529** | Normal | Standard transaction |
| `tx_norm_1857_0df1e731` | **0.1529** | Normal | Standard transaction |
| `tx_norm_1664_6079a9c2` | **0.1526** | Normal | Standard transaction |
| `tx_norm_1602_93ad6814` | **0.1525** | Normal | Standard transaction |
| `tx_norm_333_6aa5cca3` | **0.1520** | Normal | Standard transaction |
| `tx_norm_1144_efb0beac` | **0.1520** | Normal | Standard transaction |
| `tx_norm_2240_2245c02b` | **0.1514** | Normal | Standard transaction |
| `tx_norm_1530_f8067a7c` | **0.1513** | Normal | Standard transaction |
| `tx_norm_1927_16b0174d` | **0.1513** | Normal | Standard transaction |
| `tx_norm_938_682eb6aa` | **0.1512** | Normal | Standard transaction |
| `tx_norm_1070_f911a911` | **0.1509** | Normal | Standard transaction |
| `tx_norm_1548_560e31f1` | **0.1508** | Normal | Standard transaction |
| `tx_norm_1868_cf042683` | **0.1508** | Normal | Standard transaction |
| `tx_norm_599_c9bf40c0` | **0.1507** | Normal | Standard transaction |
| `tx_norm_2072_c09c4e08` | **0.1506** | Normal | Standard transaction |
| `tx_norm_396_b831e52b` | **0.1505** | Normal | Standard transaction |
| `tx_norm_420_72431551` | **0.1505** | Normal | Standard transaction |
| `tx_norm_1272_d9d09034` | **0.1505** | Normal | Standard transaction |
| `tx_norm_2094_cfefa8ae` | **0.1505** | Normal | Standard transaction |
| `tx_norm_2104_63c6c542` | **0.1503** | Normal | Standard transaction |
| `tx_norm_2281_35fb0fbd` | **0.1503** | Normal | Standard transaction |
| `tx_norm_601_32890193` | **0.1502** | Normal | Standard transaction |
| `tx_norm_1474_286b98ed` | **0.1501** | Normal | Standard transaction |
| `tx_norm_992_d9bcf096` | **0.1500** | Normal | Standard transaction |
| `tx_norm_609_48772257` | **0.1497** | Normal | Standard transaction |
| `tx_norm_685_1dc21327` | **0.1496** | Normal | Standard transaction |
| `tx_norm_426_b504912c` | **0.1495** | Normal | Standard transaction |
| `tx_norm_17_b3e3e4e0` | **0.1493** | Normal | Standard transaction |
| `tx_norm_1638_ac275679` | **0.1492** | Normal | Standard transaction |
| `tx_norm_843_cf8a4dca` | **0.1491** | Normal | Standard transaction |
| `tx_norm_2557_f5f2da60` | **0.1487** | Normal | Standard transaction |
| `tx_norm_2301_08d74fdc` | **0.1485** | Normal | Standard transaction |
| `tx_norm_2307_76ebb781` | **0.1482** | Normal | Standard transaction |
| `tx_norm_2568_7015e22c` | **0.1482** | Normal | Standard transaction |
| `tx_norm_111_f793e6ec` | **0.1477** | Normal | Standard transaction |
| `tx_norm_2090_021ca305` | **0.1476** | Normal | Standard transaction |
| `tx_norm_2403_80d96e1b` | **0.1476** | Normal | Standard transaction |
| `tx_norm_393_09b6e5ac` | **0.1474** | Normal | Standard transaction |
| `tx_norm_1146_83aeeb2d` | **0.1473** | Normal | Standard transaction |
| `tx_norm_2550_8ffcdaad` | **0.1468** | Normal | Standard transaction |
| `tx_norm_1885_b13aca0b` | **0.1467** | Normal | Standard transaction |
| `tx_norm_2613_a87b6f47` | **0.1466** | Normal | Standard transaction |
| `tx_norm_846_674b6724` | **0.1465** | Normal | Standard transaction |
| `tx_norm_1150_9d15dc51` | **0.1464** | Normal | Standard transaction |
| `tx_norm_1597_de49ebfd` | **0.1464** | Normal | Standard transaction |
| `tx_norm_2102_92f2f165` | **0.1464** | Normal | Standard transaction |
| `tx_norm_399_d07ec8a7` | **0.1463** | Normal | Standard transaction |
| `tx_norm_407_f0e823c8` | **0.1461** | Normal | Standard transaction |
| `tx_norm_326_fb1615fa` | **0.1460** | Normal | Standard transaction |
| `tx_norm_444_7ac96de9` | **0.1460** | Normal | Standard transaction |
| `tx_norm_600_256db5d7` | **0.1460** | Normal | Standard transaction |
| `tx_norm_888_45825e89` | **0.1460** | Normal | Standard transaction |
| `tx_norm_1842_5c8e0ef4` | **0.1460** | Normal | Standard transaction |
| `tx_norm_950_cbf34bb3` | **0.1457** | Normal | Standard transaction |
| `tx_norm_1131_88e04354` | **0.1455** | Normal | Standard transaction |
| `tx_norm_585_8e59a341` | **0.1453** | Normal | Standard transaction |
| `tx_norm_2420_4e08440f` | **0.1450** | Normal | Standard transaction |
| `tx_norm_1257_bc6b21bf` | **0.1448** | Normal | Standard transaction |
| `tx_norm_1490_2552ea30` | **0.1447** | Normal | Standard transaction |
| `tx_norm_1550_61997505` | **0.1447** | Normal | Standard transaction |
| `tx_norm_712_db41df9b` | **0.1445** | Normal | Standard transaction |
| `tx_norm_498_72128441` | **0.1444** | Normal | Standard transaction |
| `tx_norm_289_3535db66` | **0.1443** | Normal | Standard transaction |
| `tx_norm_1692_eea268be` | **0.1442** | Normal | Standard transaction |
| `tx_norm_775_e3e6e05b` | **0.1441** | Normal | Standard transaction |
| `tx_norm_1985_64a4c4c6` | **0.1441** | Normal | Standard transaction |
| `tx_norm_1247_b52eedeb` | **0.1439** | Normal | Standard transaction |
| `tx_norm_1419_debdac1b` | **0.1439** | Normal | Standard transaction |
| `tx_norm_1388_49ed4b44` | **0.1437** | Normal | Standard transaction |
| `tx_norm_999_5630bcb1` | **0.1436** | Normal | Standard transaction |
| `tx_norm_1061_224c6fec` | **0.1436** | Normal | Standard transaction |
| `tx_norm_2501_6af38bdd` | **0.1436** | Normal | Standard transaction |
| `tx_norm_122_d67bfdb9` | **0.1435** | Normal | Standard transaction |
| `tx_norm_187_addee167` | **0.1434** | Normal | Standard transaction |
| `tx_norm_2000_be7d1065` | **0.1434** | Normal | Standard transaction |
| `tx_norm_619_f78b59b3` | **0.1433** | Normal | Standard transaction |
| `tx_norm_976_d5891a4c` | **0.1429** | Normal | Standard transaction |
| `tx_norm_2050_df087208` | **0.1428** | Normal | Standard transaction |
| `tx_norm_642_723b1bac` | **0.1424** | Normal | Standard transaction |
| `tx_norm_1194_17042c7d` | **0.1424** | Normal | Standard transaction |
| `tx_norm_2593_ae6bd216` | **0.1424** | Normal | Standard transaction |
| `tx_norm_1172_31d1f11e` | **0.1423** | Normal | Standard transaction |
| `tx_norm_447_a9304cdd` | **0.1421** | Normal | Standard transaction |
| `tx_norm_1024_db85d8a1` | **0.1421** | Normal | Standard transaction |
| `tx_norm_1478_443e1cc2` | **0.1421** | Normal | Standard transaction |
| `tx_norm_1228_d6bd5223` | **0.1420** | Normal | Standard transaction |
| `tx_norm_624_63447f18` | **0.1419** | Normal | Standard transaction |
| `tx_norm_1393_1759e7d7` | **0.1419** | Normal | Standard transaction |
| `tx_norm_2080_2313405f` | **0.1417** | Normal | Standard transaction |
| `tx_norm_724_8de88242` | **0.1416** | Normal | Standard transaction |
| `tx_norm_2346_a6d69053` | **0.1416** | Normal | Standard transaction |
| `tx_norm_441_eb03f2b2` | **0.1414** | Normal | Standard transaction |
| `tx_norm_1072_4b14bd07` | **0.1414** | Normal | Standard transaction |
| `tx_norm_1223_9e493ca8` | **0.1414** | Normal | Standard transaction |
| `tx_norm_1288_fc556139` | **0.1409** | Normal | Standard transaction |
| `tx_norm_1567_8322b77f` | **0.1409** | Normal | Standard transaction |
| `tx_norm_960_71b38137` | **0.1408** | Normal | Standard transaction |
| `tx_norm_2088_e6641631` | **0.1408** | Normal | Standard transaction |
| `tx_norm_2441_37b43c09` | **0.1408** | Normal | Standard transaction |
| `tx_norm_1001_825d73a2` | **0.1407** | Normal | Standard transaction |
| `tx_norm_797_8555307c` | **0.1406** | Normal | Standard transaction |
| `tx_norm_2184_df369f33` | **0.1405** | Normal | Standard transaction |
| `tx_norm_1543_bf9b6166` | **0.1404** | Normal | Standard transaction |
| `tx_norm_1244_9672cbba` | **0.1402** | Normal | Standard transaction |
| `tx_norm_528_1911a0b7` | **0.1399** | Normal | Standard transaction |
| `tx_norm_69_847facb9` | **0.1398** | Normal | Standard transaction |
| `tx_norm_1699_77398b88` | **0.1397** | Normal | Standard transaction |
| `tx_norm_1242_69c6a255` | **0.1396** | Normal | Standard transaction |
| `tx_norm_2376_b62712cf` | **0.1396** | Normal | Standard transaction |
| `tx_norm_2259_7ce511b5` | **0.1395** | Normal | Standard transaction |
| `tx_norm_1102_f845e4d8` | **0.1393** | Normal | Standard transaction |
| `tx_norm_1186_bc90c010` | **0.1393** | Normal | Standard transaction |
| `tx_norm_171_fdfcb3fc` | **0.1391** | Normal | Standard transaction |
| `tx_norm_1541_cad1bbfd` | **0.1389** | Normal | Standard transaction |
| `tx_norm_1867_fab64b38` | **0.1388** | Normal | Standard transaction |
| `tx_norm_139_eabea273` | **0.1382** | Normal | Standard transaction |
| `tx_norm_2558_631c5f67` | **0.1381** | Normal | Standard transaction |
| `tx_norm_1880_d63a087c` | **0.1378** | Normal | Standard transaction |
| `tx_norm_2399_cc446301` | **0.1377** | Normal | Standard transaction |
| `tx_norm_2140_98600e6d` | **0.1376** | Normal | Standard transaction |
| `tx_norm_2009_26fe9c0d` | **0.1375** | Normal | Standard transaction |
| `tx_norm_1946_07b079d8` | **0.1372** | Normal | Standard transaction |
| `tx_norm_253_1652fe35` | **0.1371** | Normal | Standard transaction |
| `tx_norm_1198_714e97ad` | **0.1371** | Normal | Standard transaction |
| `tx_norm_1840_c31a382b` | **0.1371** | Normal | Standard transaction |
| `tx_norm_1222_6e978352` | **0.1370** | Normal | Standard transaction |
| `tx_norm_1761_11d2f29a` | **0.1366** | Normal | Standard transaction |
| `tx_norm_1978_b7b2933b` | **0.1366** | Normal | Standard transaction |
| `tx_norm_2561_96042b5d` | **0.1366** | Normal | Standard transaction |
| `tx_norm_1018_d8de6b6b` | **0.1364** | Normal | Standard transaction |
| `tx_norm_1377_38726f3f` | **0.1364** | Normal | Standard transaction |
| `tx_norm_309_53c6ddc2` | **0.1360** | Normal | Standard transaction |
| `tx_norm_554_a7c0f1af` | **0.1360** | Normal | Standard transaction |
| `tx_norm_1193_4a9f95d8` | **0.1360** | Normal | Standard transaction |
| `tx_norm_501_777f4516` | **0.1359** | Normal | Standard transaction |
| `tx_norm_2145_36ddc26f` | **0.1358** | Normal | Standard transaction |
| `tx_norm_358_f7d8d95b` | **0.1355** | Normal | Standard transaction |
| `tx_norm_1429_63c34c43` | **0.1354** | Normal | Standard transaction |
| `tx_norm_390_a068d5c4` | **0.1352** | Normal | Standard transaction |
| `tx_norm_710_edf04c96` | **0.1352** | Normal | Standard transaction |
| `tx_norm_580_a78f5a2a` | **0.1351** | Normal | Standard transaction |
| `tx_norm_1560_041b6a34` | **0.1351** | Normal | Standard transaction |
| `tx_norm_1908_bf09cf1b` | **0.1351** | Normal | Standard transaction |
| `tx_norm_1765_1fabd76e` | **0.1349** | Normal | Standard transaction |
| `tx_norm_1858_2295b1a9` | **0.1348** | Normal | Standard transaction |
| `tx_norm_1513_8c46bf5d` | **0.1347** | Normal | Standard transaction |
| `tx_norm_1658_6f58433c` | **0.1347** | Normal | Standard transaction |
| `tx_norm_223_68a7188f` | **0.1346** | Normal | Standard transaction |
| `tx_norm_1218_5a83b78e` | **0.1344** | Normal | Standard transaction |
| `tx_norm_1035_d48f5441` | **0.1343** | Normal | Standard transaction |
| `tx_norm_1933_aad4b664` | **0.1341** | Normal | Standard transaction |
| `tx_norm_577_07e3a215` | **0.1340** | Normal | Standard transaction |
| `tx_norm_1189_f91dd07d` | **0.1340** | Normal | Standard transaction |
| `tx_norm_1650_2e1e26ab` | **0.1340** | Normal | Standard transaction |
| `tx_norm_2162_a09fcbb7` | **0.1340** | Normal | Standard transaction |
| `tx_norm_2249_f4fae73c` | **0.1339** | Normal | Standard transaction |
| `tx_norm_89_e342198b` | **0.1337** | Normal | Standard transaction |
| `tx_norm_875_0ad5c514` | **0.1337** | Normal | Standard transaction |
| `tx_norm_676_fa101f93` | **0.1336** | Normal | Standard transaction |
| `tx_norm_814_4d9a6f39` | **0.1335** | Normal | Standard transaction |
| `tx_norm_482_3103eba2` | **0.1334** | Normal | Standard transaction |
| `tx_norm_1074_bd98e04b` | **0.1333** | Normal | Standard transaction |
| `tx_norm_312_4cc46a19` | **0.1330** | Normal | Standard transaction |
| `tx_norm_2032_e10cdfa5` | **0.1330** | Normal | Standard transaction |
| `tx_norm_1729_a591a2e6` | **0.1328** | Normal | Standard transaction |
| `tx_norm_863_d749497f` | **0.1327** | Normal | Standard transaction |
| `tx_norm_572_cdee245a` | **0.1325** | Normal | Standard transaction |
| `tx_norm_2185_bf737d7c` | **0.1320** | Normal | Standard transaction |
| `tx_norm_303_2ae3802b` | **0.1318** | Normal | Standard transaction |
| `tx_norm_1139_9487de32` | **0.1317** | Normal | Standard transaction |
| `tx_norm_2596_29071406` | **0.1317** | Normal | Standard transaction |
| `tx_norm_228_1093d907` | **0.1316** | Normal | Standard transaction |
| `tx_norm_108_aab7d256` | **0.1315** | Normal | Standard transaction |
| `tx_norm_1255_86c1a5f1` | **0.1315** | Normal | Standard transaction |
| `tx_norm_1358_b570e805` | **0.1315** | Normal | Standard transaction |
| `tx_norm_1328_0c9775f5` | **0.1311** | Normal | Standard transaction |
| `tx_norm_311_c68aa168` | **0.1310** | Normal | Standard transaction |
| `tx_norm_854_7dc6c006` | **0.1305** | Normal | Standard transaction |
| `tx_norm_1125_464a9753` | **0.1305** | Normal | Standard transaction |
| `tx_norm_1963_2194c46b` | **0.1304** | Normal | Standard transaction |
| `tx_norm_977_919bd455` | **0.1303** | Normal | Standard transaction |
| `tx_norm_2273_c5693527` | **0.1303** | Normal | Standard transaction |
| `tx_norm_608_3cad017b` | **0.1302** | Normal | Standard transaction |
| `tx_norm_2154_0050fb0c` | **0.1299** | Normal | Standard transaction |
| `tx_norm_2164_e13f198c` | **0.1297** | Normal | Standard transaction |
| `tx_norm_1159_f7fb1b90` | **0.1296** | Normal | Standard transaction |
| `tx_norm_570_05f8e21d` | **0.1295** | Normal | Standard transaction |
| `tx_norm_1038_0587dd62` | **0.1294** | Normal | Standard transaction |
| `tx_norm_1653_95dd0415` | **0.1294** | Normal | Standard transaction |
| `tx_norm_279_58b0cb24` | **0.1292** | Normal | Standard transaction |
| `tx_norm_931_463b173f` | **0.1290** | Normal | Standard transaction |
| `tx_norm_2333_4d37f6b0` | **0.1288** | Normal | Standard transaction |
| `tx_norm_882_9b725ca9` | **0.1286** | Normal | Standard transaction |
| `tx_norm_1624_dd8e1687` | **0.1286** | Normal | Standard transaction |
| `tx_norm_1318_c674ff53` | **0.1285** | Normal | Standard transaction |
| `tx_norm_2086_f393aa86` | **0.1285** | Normal | Standard transaction |
| `tx_norm_2002_a7ca2b5e` | **0.1284** | Normal | Standard transaction |
| `tx_norm_1261_c9008a92` | **0.1283** | Normal | Standard transaction |
| `tx_norm_1618_74f71d4d` | **0.1282** | Normal | Standard transaction |
| `tx_norm_1634_4a21e7ce` | **0.1282** | Normal | Standard transaction |
| `tx_norm_2564_f3b039fb` | **0.1281** | Normal | Standard transaction |
| `tx_norm_830_abdefe81` | **0.1280** | Normal | Standard transaction |
| `tx_norm_2039_2c0885c7` | **0.1280** | Normal | Standard transaction |
| `tx_norm_2392_901a1b38` | **0.1280** | Normal | Standard transaction |
| `tx_norm_592_7787c7f6` | **0.1277** | Normal | Standard transaction |
| `tx_norm_2360_3a986128` | **0.1277** | Normal | Standard transaction |
| `tx_norm_1945_962a7f14` | **0.1275** | Normal | Standard transaction |
| `tx_norm_2205_f7b39123` | **0.1271** | Normal | Standard transaction |
| `tx_norm_1119_e7618aa4` | **0.1270** | Normal | Standard transaction |
| `tx_norm_2592_dbf0be00` | **0.1270** | Normal | Standard transaction |
| `tx_norm_2503_70d21b0b` | **0.1269** | Normal | Standard transaction |
| `tx_norm_1748_7e9b75a5` | **0.1268** | Normal | Standard transaction |
| `tx_norm_510_703a4416` | **0.1267** | Normal | Standard transaction |
| `tx_norm_639_a8666b7b` | **0.1267** | Normal | Standard transaction |
| `tx_norm_1738_db296d2e` | **0.1267** | Normal | Standard transaction |
| `tx_norm_927_7fabbfcd` | **0.1266** | Normal | Standard transaction |
| `tx_norm_2581_3c6ce124` | **0.1266** | Normal | Standard transaction |
| `tx_norm_1164_bc5c2962` | **0.1263** | Normal | Standard transaction |
| `tx_norm_1724_cbf4d121` | **0.1263** | Normal | Standard transaction |
| `tx_norm_2554_c3f973f2` | **0.1263** | Normal | Standard transaction |
| `tx_norm_1233_de804042` | **0.1262** | Normal | Standard transaction |
| `tx_norm_2383_e511ee36` | **0.1262** | Normal | Standard transaction |
| `tx_norm_166_07deecb1` | **0.1261** | Normal | Standard transaction |
| `tx_norm_483_ee41940f` | **0.1261** | Normal | Standard transaction |
| `tx_norm_677_1d6538f1` | **0.1259** | Normal | Standard transaction |
| `tx_norm_957_f4494b82` | **0.1258** | Normal | Standard transaction |
| `tx_norm_227_47c17e12` | **0.1253** | Normal | Standard transaction |
| `tx_norm_659_933eeb3a` | **0.1252** | Normal | Standard transaction |
| `tx_norm_1305_8b9e236c` | **0.1252** | Normal | Standard transaction |
| `tx_norm_82_3a53c2eb` | **0.1250** | Normal | Standard transaction |
| `tx_norm_1021_21d6d734` | **0.1249** | Normal | Standard transaction |
| `tx_norm_813_d4527a56` | **0.1246** | Normal | Standard transaction |
| `tx_norm_1120_29b1ad47` | **0.1246** | Normal | Standard transaction |
| `tx_norm_12_66c18ec5` | **0.1243** | Normal | Standard transaction |
| `tx_norm_222_23d238f5` | **0.1241** | Normal | Standard transaction |
| `tx_norm_369_e89a6d72` | **0.1240** | Normal | Standard transaction |
| `tx_norm_2398_c83c7e17` | **0.1238** | Normal | Standard transaction |
| `tx_norm_1484_ad920f54` | **0.1236** | Normal | Standard transaction |
| `tx_norm_628_c83c61b7` | **0.1234** | Normal | Standard transaction |
| `tx_norm_1178_c2397021` | **0.1234** | Normal | Standard transaction |
| `tx_norm_606_4b24048e` | **0.1233** | Normal | Standard transaction |
| `tx_norm_1214_a9f8898b` | **0.1232** | Normal | Standard transaction |
| `tx_norm_1281_f9a3b2cb` | **0.1232** | Normal | Standard transaction |
| `tx_norm_1815_e524f789` | **0.1229** | Normal | Standard transaction |
| `tx_norm_2291_39a9d331` | **0.1229** | Normal | Standard transaction |
| `tx_norm_2602_d72341a2` | **0.1228** | Normal | Standard transaction |
| `tx_norm_824_2b120eb8` | **0.1227** | Normal | Standard transaction |
| `tx_norm_351_10190b9a` | **0.1225** | Normal | Standard transaction |
| `tx_norm_1227_c3c6b264` | **0.1225** | Normal | Standard transaction |
| `tx_norm_167_6fabbb2f` | **0.1224** | Normal | Standard transaction |
| `tx_norm_799_027e34d4` | **0.1224** | Normal | Standard transaction |
| `tx_norm_361_28a54369` | **0.1223** | Normal | Standard transaction |
| `tx_norm_610_72a016bf` | **0.1223** | Normal | Standard transaction |
| `tx_norm_968_18e8cf61` | **0.1222** | Normal | Standard transaction |
| `tx_norm_522_1913a874` | **0.1219** | Normal | Standard transaction |
| `tx_norm_1709_944ab6b9` | **0.1219** | Normal | Standard transaction |
| `tx_norm_2308_4e8b5aa3` | **0.1217** | Normal | Standard transaction |
| `tx_norm_2507_b69d5a8a` | **0.1209** | Normal | Standard transaction |
| `tx_norm_768_0107a455` | **0.1206** | Normal | Standard transaction |
| `tx_norm_13_a01b8193` | **0.1205** | Normal | Standard transaction |
| `tx_norm_1015_c1017e29` | **0.1204** | Normal | Standard transaction |
| `tx_norm_1807_838d6cbb` | **0.1204** | Normal | Standard transaction |
| `tx_norm_1907_539caa23` | **0.1204** | Normal | Standard transaction |
| `tx_norm_2128_596e6e38` | **0.1204** | Normal | Standard transaction |
| `tx_norm_2361_acc8b965` | **0.1203** | Normal | Standard transaction |
| `tx_norm_2549_0652379f` | **0.1202** | Normal | Standard transaction |
| `tx_norm_1044_1bd5839f` | **0.1201** | Normal | Standard transaction |
| `tx_norm_29_d6534887` | **0.1197** | Normal | Standard transaction |
| `tx_norm_2358_fe5db97c` | **0.1197** | Normal | Standard transaction |
| `tx_norm_817_9b5a5a3f` | **0.1196** | Normal | Standard transaction |
| `tx_norm_2280_46a2277f` | **0.1195** | Normal | Standard transaction |
| `tx_norm_2467_9a10b18f` | **0.1192** | Normal | Standard transaction |
| `tx_norm_1481_2e9697ca` | **0.1190** | Normal | Standard transaction |
| `tx_norm_1750_5f8a70b2` | **0.1189** | Normal | Standard transaction |
| `tx_norm_295_7c326412` | **0.1187** | Normal | Standard transaction |
| `tx_norm_110_0796665c` | **0.1186** | Normal | Standard transaction |
| `tx_norm_353_6e1004f5` | **0.1186** | Normal | Standard transaction |
| `tx_norm_2402_003b6ff8` | **0.1185** | Normal | Standard transaction |
| `tx_norm_1654_562abce5` | **0.1183** | Normal | Standard transaction |
| `tx_norm_2134_c9de1f62` | **0.1183** | Normal | Standard transaction |
| `tx_norm_2461_019af8fd` | **0.1183** | Normal | Standard transaction |
| `tx_norm_732_28ebe613` | **0.1182** | Normal | Standard transaction |
| `tx_norm_1389_39d72556` | **0.1182** | Normal | Standard transaction |
| `tx_norm_2062_6ff690b0` | **0.1182** | Normal | Standard transaction |
| `tx_norm_1293_1c1ebc02` | **0.1180** | Normal | Standard transaction |
| `tx_norm_820_871e73c8` | **0.1179** | Normal | Standard transaction |
| `tx_norm_1918_ccbd835f` | **0.1179** | Normal | Standard transaction |
| `tx_norm_63_ae6287eb` | **0.1177** | Normal | Standard transaction |
| `tx_norm_1871_dd91d0fa` | **0.1177** | Normal | Standard transaction |
| `tx_norm_2331_165f8e6a` | **0.1177** | Normal | Standard transaction |
| `tx_norm_924_6e1e5f6c` | **0.1175** | Normal | Standard transaction |
| `tx_norm_2523_d254eee0` | **0.1172** | Normal | Standard transaction |
| `tx_norm_821_ffbab6c3` | **0.1171** | Normal | Standard transaction |
| `tx_norm_2236_506ef8e5` | **0.1170** | Normal | Standard transaction |
| `tx_norm_1778_2e6eafa4` | **0.1165** | Normal | Standard transaction |
| `tx_norm_352_895e7e1f` | **0.1163** | Normal | Standard transaction |
| `tx_norm_587_5ce3c121` | **0.1162** | Normal | Standard transaction |
| `tx_norm_1790_8b8db5e2` | **0.1162** | Normal | Standard transaction |
| `tx_norm_1979_703c6688` | **0.1161** | Normal | Standard transaction |
| `tx_norm_1735_7f7f7b07` | **0.1160** | Normal | Standard transaction |
| `tx_norm_1040_19dc80bc` | **0.1153** | Normal | Standard transaction |
| `tx_norm_178_b4acf8f9` | **0.1152** | Normal | Standard transaction |
| `tx_norm_647_92e5df81` | **0.1152** | Normal | Standard transaction |
| `tx_norm_1848_02c921fa` | **0.1152** | Normal | Standard transaction |
| `tx_norm_1482_5a8e8c22` | **0.1151** | Normal | Standard transaction |
| `tx_norm_873_406739f6` | **0.1150** | Normal | Standard transaction |
| `tx_norm_1861_dedc3c93` | **0.1149** | Normal | Standard transaction |
| `tx_norm_559_88af9041` | **0.1148** | Normal | Standard transaction |
| `tx_norm_2531_2c847c2b` | **0.1145** | Normal | Standard transaction |
| `tx_norm_907_2deb3b76` | **0.1144** | Normal | Standard transaction |
| `tx_norm_1088_a2b4f6eb` | **0.1143** | Normal | Standard transaction |
| `tx_norm_1064_7a8e9ccc` | **0.1142** | Normal | Standard transaction |
| `tx_norm_1774_ead43820` | **0.1141** | Normal | Standard transaction |
| `tx_norm_112_7d0960bf` | **0.1138** | Normal | Standard transaction |
| `tx_norm_2046_3d48108f` | **0.1135** | Normal | Standard transaction |
| `tx_norm_2573_8c64a370` | **0.1135** | Normal | Standard transaction |
| `tx_norm_2067_ff2e5adf` | **0.1134** | Normal | Standard transaction |
| `tx_norm_1384_ff26faa9` | **0.1132** | Normal | Standard transaction |
| `tx_norm_746_fbc3e9fa` | **0.1130** | Normal | Standard transaction |
| `tx_norm_1197_8651eb4e` | **0.1130** | Normal | Standard transaction |
| `tx_norm_1919_4f94fc65` | **0.1130** | Normal | Standard transaction |
| `tx_norm_2620_57362398` | **0.1130** | Normal | Standard transaction |
| `tx_norm_1117_9b5d374c` | **0.1127** | Normal | Standard transaction |
| `tx_norm_1031_bc0418ff` | **0.1123** | Normal | Standard transaction |
| `tx_norm_1275_7a759bc8` | **0.1123** | Normal | Standard transaction |
| `tx_norm_1568_cbbf1656` | **0.1122** | Normal | Standard transaction |
| `tx_norm_539_cfe3c145` | **0.1121** | Normal | Standard transaction |
| `tx_norm_2226_7d394be5` | **0.1121** | Normal | Standard transaction |
| `tx_norm_1739_c7201256` | **0.1118** | Normal | Standard transaction |
| `tx_norm_561_49665cbe` | **0.1117** | Normal | Standard transaction |
| `tx_norm_2576_17286f41` | **0.1115** | Normal | Standard transaction |
| `tx_norm_1606_5a7c4ab7` | **0.1112** | Normal | Standard transaction |
| `tx_norm_1667_d712d555` | **0.1112** | Normal | Standard transaction |
| `tx_norm_495_ea3e1013` | **0.1111** | Normal | Standard transaction |
| `tx_norm_448_d47ce932` | **0.1109** | Normal | Standard transaction |
| `tx_norm_527_9e09e6ff` | **0.1109** | Normal | Standard transaction |
| `tx_norm_1183_108248b4` | **0.1108** | Normal | Standard transaction |
| `tx_norm_1282_47b9f132` | **0.1107** | Normal | Standard transaction |
| `tx_norm_1045_87e8977c` | **0.1106** | Normal | Standard transaction |
| `tx_norm_1506_89abe231` | **0.1105** | Normal | Standard transaction |
| `tx_norm_1932_9a6dc4f8` | **0.1105** | Normal | Standard transaction |
| `tx_norm_355_121c231e` | **0.1104** | Normal | Standard transaction |
| `tx_norm_1992_9f9f66ce` | **0.1104** | Normal | Standard transaction |
| `tx_norm_470_d32d9ebb` | **0.1103** | Normal | Standard transaction |
| `tx_norm_1581_29e5a3f1` | **0.1103** | Normal | Standard transaction |
| `tx_norm_47_283f4e4c` | **0.1102** | Normal | Standard transaction |
| `tx_norm_164_25bc4cd7` | **0.1102** | Normal | Standard transaction |
| `tx_norm_2326_f724800c` | **0.1102** | Normal | Standard transaction |
| `tx_norm_981_11911e5f` | **0.1100** | Normal | Standard transaction |
| `tx_norm_382_6f1c8879` | **0.1097** | Normal | Standard transaction |
| `tx_norm_2546_992f14c1` | **0.1097** | Normal | Standard transaction |
| `tx_norm_909_8ab5b52c` | **0.1095** | Normal | Standard transaction |
| `tx_norm_1780_04051680` | **0.1094** | Normal | Standard transaction |
| `tx_norm_663_231ff5cb` | **0.1093** | Normal | Standard transaction |
| `tx_norm_1576_f4d9cb62` | **0.1093** | Normal | Standard transaction |
| `tx_norm_506_484ce92d` | **0.1092** | Normal | Standard transaction |
| `tx_norm_176_5408a480` | **0.1090** | Normal | Standard transaction |
| `tx_norm_533_f0ea6691` | **0.1089** | Normal | Standard transaction |
| `tx_norm_1367_56e04a0a` | **0.1089** | Normal | Standard transaction |
| `tx_norm_951_eb296b31` | **0.1088** | Normal | Standard transaction |
| `tx_norm_1476_4dfbf31b` | **0.1084** | Normal | Standard transaction |
| `tx_norm_2364_645db58b` | **0.1084** | Normal | Standard transaction |
| `tx_norm_2637_f9fe6edd` | **0.1084** | Normal | Standard transaction |
| `tx_norm_2161_2ff1ac3b` | **0.1080** | Normal | Standard transaction |
| `tx_norm_1489_b83e72e9` | **0.1079** | Normal | Standard transaction |
| `tx_norm_217_13a9371a` | **0.1078** | Normal | Standard transaction |
| `tx_norm_2396_f6897e37` | **0.1078** | Normal | Standard transaction |
| `tx_norm_686_52304a14` | **0.1077** | Normal | Standard transaction |
| `tx_norm_1925_cd9a14f7` | **0.1077** | Normal | Standard transaction |
| `tx_norm_2006_644d2e1d` | **0.1076** | Normal | Standard transaction |
| `tx_norm_2497_e5666b63` | **0.1072** | Normal | Standard transaction |
| `tx_norm_552_f95cbfd8` | **0.1071** | Normal | Standard transaction |
| `tx_norm_1326_e0d11057` | **0.1067** | Normal | Standard transaction |
| `tx_norm_343_3dcdb20f` | **0.1066** | Normal | Standard transaction |
| `tx_norm_564_0740a86d` | **0.1065** | Normal | Standard transaction |
| `tx_norm_2319_93e3039c` | **0.1064** | Normal | Standard transaction |
| `tx_norm_186_63cc1f8c` | **0.1062** | Normal | Standard transaction |
| `tx_norm_429_f17d44e9` | **0.1062** | Normal | Standard transaction |
| `tx_norm_2085_3270da96` | **0.1062** | Normal | Standard transaction |
| `tx_norm_2429_a1231942` | **0.1061** | Normal | Standard transaction |
| `tx_norm_154_ed156bfb` | **0.1059** | Normal | Standard transaction |
| `tx_norm_2458_7071ad8a` | **0.1059** | Normal | Standard transaction |
| `tx_norm_1536_3fe2470c` | **0.1057** | Normal | Standard transaction |
| `tx_norm_1154_80abf3bf` | **0.1056** | Normal | Standard transaction |
| `tx_norm_2017_5969a151` | **0.1056** | Normal | Standard transaction |
| `tx_norm_2146_04e5d81a` | **0.1055** | Normal | Standard transaction |
| `tx_norm_1697_4232c490` | **0.1050** | Normal | Standard transaction |
| `tx_norm_301_ed49e36b` | **0.1049** | Normal | Standard transaction |
| `tx_norm_825_f4082c0c` | **0.1048** | Normal | Standard transaction |
| `tx_norm_2349_ad1c9c30` | **0.1047** | Normal | Standard transaction |
| `tx_norm_2569_839d072f` | **0.1047** | Normal | Standard transaction |
| `tx_norm_1239_b1dbc1d3` | **0.1044** | Normal | Standard transaction |
| `tx_norm_582_a88a1700` | **0.1042** | Normal | Standard transaction |
| `tx_norm_2371_9d2c25fc` | **0.1042** | Normal | Standard transaction |
| `tx_norm_2545_14a5efef` | **0.1041** | Normal | Standard transaction |
| `tx_norm_804_c279ce93` | **0.1039** | Normal | Standard transaction |
| `tx_norm_459_7f9bd725` | **0.1038** | Normal | Standard transaction |
| `tx_norm_918_16a06ee7` | **0.1037** | Normal | Standard transaction |
| `tx_norm_1642_57e28dfb` | **0.1037** | Normal | Standard transaction |
| `tx_norm_2615_7844b318` | **0.1037** | Normal | Standard transaction |
| `tx_norm_531_1f4b4ef6` | **0.1035** | Normal | Standard transaction |
| `tx_norm_2452_3ef96365` | **0.1035** | Normal | Standard transaction |
| `tx_norm_665_62419616` | **0.1034** | Normal | Standard transaction |
| `tx_norm_1348_a1142efc` | **0.1034** | Normal | Standard transaction |
| `tx_norm_1823_a614fd3e` | **0.1034** | Normal | Standard transaction |
| `tx_norm_2532_0630db65` | **0.1034** | Normal | Standard transaction |
| `tx_norm_1958_d8fc61a6` | **0.1033** | Normal | Standard transaction |
| `tx_norm_419_bc22baff` | **0.1032** | Normal | Standard transaction |
| `tx_norm_668_9dd0653c` | **0.1029** | Normal | Standard transaction |
| `tx_norm_2553_319e7918` | **0.1028** | Normal | Standard transaction |
| `tx_norm_116_ee39bc5e` | **0.1024** | Normal | Standard transaction |
| `tx_norm_478_39cce028` | **0.1023** | Normal | Standard transaction |
| `tx_norm_1256_4eae0bdf` | **0.1023** | Normal | Standard transaction |
| `tx_norm_2560_b09aaf7c` | **0.1023** | Normal | Standard transaction |
| `tx_norm_440_fd26f331` | **0.1022** | Normal | Standard transaction |
| `tx_norm_1284_f0ea6c96` | **0.1022** | Normal | Standard transaction |
| `tx_norm_239_b45f9605` | **0.1021** | Normal | Standard transaction |
| `tx_norm_1199_fa3e3a8a` | **0.1021** | Normal | Standard transaction |
| `tx_norm_767_6c37c06f` | **0.1019** | Normal | Standard transaction |
| `tx_norm_2368_4c445673` | **0.1019** | Normal | Standard transaction |
| `tx_norm_1505_5370eb1c` | **0.1012** | Normal | Standard transaction |
| `tx_norm_579_99283dab` | **0.1010** | Normal | Standard transaction |
| `tx_norm_1375_e1adc22d` | **0.1005** | Normal | Standard transaction |
| `tx_norm_803_c35f8a8c` | **0.1004** | Normal | Standard transaction |
| `tx_norm_126_e3c8c9ca` | **0.1003** | Normal | Standard transaction |
| `tx_norm_1768_425b9386` | **0.1002** | Normal | Standard transaction |
| `tx_norm_673_32523a4a` | **0.1001** | Normal | Standard transaction |
| `tx_norm_868_e19eb9e0` | **0.1001** | Normal | Standard transaction |
| `tx_norm_2393_2a886082` | **0.0997** | Normal | Standard transaction |
| `tx_norm_2290_abae319c` | **0.0994** | Normal | Standard transaction |
| `tx_norm_1838_ce023944` | **0.0993** | Normal | Standard transaction |
| `tx_norm_2129_274075a3` | **0.0993** | Normal | Standard transaction |
| `tx_norm_1866_502773ee` | **0.0992** | Normal | Standard transaction |
| `tx_norm_1356_85033a1d` | **0.0991** | Normal | Standard transaction |
| `tx_norm_1975_7ba13217` | **0.0991** | Normal | Standard transaction |
| `tx_norm_2143_adfa1794` | **0.0985** | Normal | Standard transaction |
| `tx_norm_2342_dbb2151a` | **0.0983** | Normal | Standard transaction |
| `tx_norm_477_f74e9046` | **0.0982** | Normal | Standard transaction |
| `tx_norm_1605_084847b4` | **0.0981** | Normal | Standard transaction |
| `tx_norm_153_0c183f2a` | **0.0980** | Normal | Standard transaction |
| `tx_norm_2585_a5a4f214` | **0.0977** | Normal | Standard transaction |
| `tx_norm_553_167838d2` | **0.0975** | Normal | Standard transaction |
| `tx_norm_988_92e5b885` | **0.0974** | Normal | Standard transaction |
| `tx_norm_1101_28c19795` | **0.0974** | Normal | Standard transaction |
| `tx_norm_1860_1af3ac25` | **0.0973** | Normal | Standard transaction |
| `tx_norm_1873_c292498a` | **0.0971** | Normal | Standard transaction |
| `tx_norm_2588_7a80d796` | **0.0971** | Normal | Standard transaction |
| `tx_norm_1494_29070dc6` | **0.0967** | Normal | Standard transaction |
| `tx_norm_2567_d9c1e54f` | **0.0965** | Normal | Standard transaction |
| `tx_norm_1107_02f9621c` | **0.0964** | Normal | Standard transaction |
| `tx_norm_1132_b339e64a` | **0.0963** | Normal | Standard transaction |
| `tx_norm_2132_169b8e53` | **0.0963** | Normal | Standard transaction |
| `tx_norm_2040_b7ad48b4` | **0.0962** | Normal | Standard transaction |
| `tx_norm_1843_8c8e4d37` | **0.0961** | Normal | Standard transaction |
| `tx_norm_427_8df8cb7c` | **0.0958** | Normal | Standard transaction |
| `tx_norm_2173_2a7e4c07` | **0.0953** | Normal | Standard transaction |
| `tx_norm_348_dc215df5` | **0.0951** | Normal | Standard transaction |
| `tx_norm_2397_7925fad2` | **0.0951** | Normal | Standard transaction |
| `tx_norm_2595_2f2663d5` | **0.0950** | Normal | Standard transaction |
| `tx_norm_414_1d88eb11` | **0.0948** | Normal | Standard transaction |
| `tx_norm_2234_36922fb6` | **0.0948** | Normal | Standard transaction |
| `tx_norm_135_7bdb6210` | **0.0947** | Normal | Standard transaction |
| `tx_norm_1806_98e87dad` | **0.0947** | Normal | Standard transaction |
| `tx_norm_1446_23061e25` | **0.0946** | Normal | Standard transaction |
| `tx_norm_1889_53904dc5` | **0.0939** | Normal | Standard transaction |
| `tx_norm_920_fbcae4ac` | **0.0938** | Normal | Standard transaction |
| `tx_norm_598_3097cda6` | **0.0937** | Normal | Standard transaction |
| `tx_norm_596_e8e17a93` | **0.0936** | Normal | Standard transaction |
| `tx_norm_885_a0a92b1a` | **0.0935** | Normal | Standard transaction |
| `tx_norm_837_4795d4e6` | **0.0934** | Normal | Standard transaction |
| `tx_norm_1715_799494db` | **0.0932** | Normal | Standard transaction |
| `tx_norm_114_d000d08c` | **0.0929** | Normal | Standard transaction |
| `tx_norm_762_3457c604` | **0.0929** | Normal | Standard transaction |
| `tx_norm_1165_d01d3758` | **0.0929** | Normal | Standard transaction |
| `tx_norm_1180_3c831aa2` | **0.0926** | Normal | Standard transaction |
| `tx_norm_1934_effc5baf` | **0.0923** | Normal | Standard transaction |
| `tx_norm_1535_c3f2efc2` | **0.0920** | Normal | Standard transaction |
| `tx_norm_737_28b95d13` | **0.0917** | Normal | Standard transaction |
| `tx_norm_683_e68df761` | **0.0916** | Normal | Standard transaction |
| `tx_norm_2539_17a20a05` | **0.0915** | Normal | Standard transaction |
| `tx_norm_921_2d772822` | **0.0914** | Normal | Standard transaction |
| `tx_norm_258_ebafa1c9` | **0.0911** | Normal | Standard transaction |
| `tx_norm_2195_625ac27c` | **0.0911** | Normal | Standard transaction |
| `tx_norm_1213_7e12a29d` | **0.0909** | Normal | Standard transaction |
| `tx_norm_1012_cc061cdc` | **0.0905** | Normal | Standard transaction |
| `tx_norm_1631_d4ce0bb6` | **0.0905** | Normal | Standard transaction |
| `tx_norm_1962_8dab68f5` | **0.0905** | Normal | Standard transaction |
| `tx_norm_1996_3439b7e1` | **0.0905** | Normal | Standard transaction |
| `tx_norm_105_21e8d7b5` | **0.0904** | Normal | Standard transaction |
| `tx_norm_181_a4413b9d` | **0.0904** | Normal | Standard transaction |
| `tx_norm_786_2b048e07` | **0.0902** | Normal | Standard transaction |
| `tx_norm_1466_4cf770cf` | **0.0902** | Normal | Standard transaction |
| `tx_norm_2113_0ceac6e6` | **0.0902** | Normal | Standard transaction |
| `tx_norm_604_1bdb3852` | **0.0901** | Normal | Standard transaction |
| `tx_norm_785_cf64e0e9` | **0.0900** | Normal | Standard transaction |
| `tx_norm_98_68b45b10` | **0.0899** | Normal | Standard transaction |
| `tx_norm_1087_8a477056` | **0.0899** | Normal | Standard transaction |
| `tx_norm_1702_9b815d32` | **0.0899** | Normal | Standard transaction |
| `tx_norm_714_dd42e082` | **0.0897** | Normal | Standard transaction |
| `tx_norm_645_b36e70a2` | **0.0892** | Normal | Standard transaction |
| `tx_norm_2312_a7081182` | **0.0891** | Normal | Standard transaction |
| `tx_norm_1590_8e547b19` | **0.0888** | Normal | Standard transaction |
| `tx_norm_2417_e35ed2f2` | **0.0888** | Normal | Standard transaction |
| `tx_norm_955_d698cd7d` | **0.0887** | Normal | Standard transaction |
| `tx_norm_155_a03ee294` | **0.0886** | Normal | Standard transaction |
| `tx_norm_1453_ba0fdf22` | **0.0886** | Normal | Standard transaction |
| `tx_norm_391_abf00812` | **0.0883** | Normal | Standard transaction |
| `tx_norm_425_2d7436e1` | **0.0880** | Normal | Standard transaction |
| `tx_norm_590_5521f675` | **0.0877** | Normal | Standard transaction |
| `tx_norm_1294_fae248eb` | **0.0874** | Normal | Standard transaction |
| `tx_norm_715_23ee80a4` | **0.0872** | Normal | Standard transaction |
| `tx_norm_2336_44bc301c` | **0.0872** | Normal | Standard transaction |
| `tx_norm_1111_2b47f636` | **0.0866** | Normal | Standard transaction |
| `tx_norm_1327_0ecc3dcf` | **0.0866** | Normal | Standard transaction |
| `tx_norm_403_670ba85d` | **0.0864** | Normal | Standard transaction |
| `tx_norm_1939_0b6cc8c6` | **0.0861** | Normal | Standard transaction |
| `tx_norm_2571_ae62fa72` | **0.0861** | Normal | Standard transaction |
| `tx_norm_411_fc8a3519` | **0.0860** | Normal | Standard transaction |
| `tx_norm_633_bbca4289` | **0.0859** | Normal | Standard transaction |
| `tx_norm_1725_e0991b44` | **0.0858** | Normal | Standard transaction |
| `tx_norm_50_2e19e1a4` | **0.0857** | Normal | Standard transaction |
| `tx_norm_458_03a3af95` | **0.0857** | Normal | Standard transaction |
| `tx_norm_1779_367a36f0` | **0.0856** | Normal | Standard transaction |
| `tx_norm_282_df93365c` | **0.0855** | Normal | Standard transaction |
| `tx_norm_2229_2d64475e` | **0.0854** | Normal | Standard transaction |
| `tx_norm_1104_2367e1db` | **0.0852** | Normal | Standard transaction |
| `tx_norm_1376_cbcc068b` | **0.0852** | Normal | Standard transaction |
| `tx_norm_1706_1cd4767f` | **0.0850** | Normal | Standard transaction |
| `tx_norm_125_868976cc` | **0.0843** | Normal | Standard transaction |
| `tx_norm_684_bf40b9b3` | **0.0842** | Normal | Standard transaction |
| `tx_norm_268_2485484f` | **0.0841** | Normal | Standard transaction |
| `tx_norm_133_5c7e677e` | **0.0840** | Normal | Standard transaction |
| `tx_norm_1528_82dc93be` | **0.0838** | Normal | Standard transaction |
| `tx_norm_1406_62417b78` | **0.0835** | Normal | Standard transaction |
| `tx_norm_670_1ac2d02c` | **0.0833** | Normal | Standard transaction |
| `tx_norm_1204_a2fbd9a2` | **0.0831** | Normal | Standard transaction |
| `tx_norm_2287_42ff9b5e` | **0.0831** | Normal | Standard transaction |
| `tx_norm_347_cf81c626` | **0.0825** | Normal | Standard transaction |
| `tx_norm_445_c9e4de52` | **0.0825** | Normal | Standard transaction |
| `tx_norm_20_c0a05cfd` | **0.0824** | Normal | Standard transaction |
| `tx_norm_1439_cbaa5b51` | **0.0824** | Normal | Standard transaction |
| `tx_norm_1646_2bca2b8b` | **0.0822** | Normal | Standard transaction |
| `tx_norm_334_9d557601` | **0.0816** | Normal | Standard transaction |
| `tx_norm_490_5870ee52` | **0.0815** | Normal | Standard transaction |
| `tx_norm_845_4d951e2b` | **0.0815** | Normal | Standard transaction |
| `tx_norm_716_229ff090` | **0.0814** | Normal | Standard transaction |
| `tx_norm_395_aa5126bf` | **0.0810** | Normal | Standard transaction |
| `tx_norm_129_a666e822` | **0.0807** | Normal | Standard transaction |
| `tx_norm_1097_c7ec4c5c` | **0.0807** | Normal | Standard transaction |
| `tx_norm_2193_052b500f` | **0.0806** | Normal | Standard transaction |
| `tx_norm_1850_9b7fd83d` | **0.0803** | Normal | Standard transaction |
| `tx_norm_2377_d754fd1a` | **0.0803** | Normal | Standard transaction |
| `tx_norm_2475_576d770e` | **0.0802** | Normal | Standard transaction |
| `tx_norm_1647_11e70001` | **0.0800** | Normal | Standard transaction |
| `tx_norm_594_5720d708` | **0.0798** | Normal | Standard transaction |
| `tx_norm_1956_20d059c2` | **0.0797** | Normal | Standard transaction |
| `tx_norm_2374_ac4dfd94` | **0.0796** | Normal | Standard transaction |
| `tx_norm_1208_9df0b9d4` | **0.0794** | Normal | Standard transaction |
| `tx_norm_1196_43215908` | **0.0792** | Normal | Standard transaction |
| `tx_norm_1957_743ea827` | **0.0791** | Normal | Standard transaction |
| `tx_norm_1636_ad63d66b` | **0.0790** | Normal | Standard transaction |
| `tx_norm_2064_e687677a` | **0.0789** | Normal | Standard transaction |
| `tx_norm_36_d4325950` | **0.0788** | Normal | Standard transaction |
| `tx_norm_2521_1f9b56e0` | **0.0787** | Normal | Standard transaction |
| `tx_norm_2468_a62c0655` | **0.0782** | Normal | Standard transaction |
| `tx_norm_1564_7a22ca93` | **0.0780** | Normal | Standard transaction |
| `tx_norm_2242_b47f6ab7` | **0.0780** | Normal | Standard transaction |
| `tx_norm_700_3ea1b4ad` | **0.0779** | Normal | Standard transaction |
| `tx_norm_1570_e50f02d5` | **0.0779** | Normal | Standard transaction |
| `tx_norm_40_0124b8a6` | **0.0777** | Normal | Standard transaction |
| `tx_norm_290_c6e91301` | **0.0776** | Normal | Standard transaction |
| `tx_norm_926_08be770c` | **0.0775** | Normal | Standard transaction |
| `tx_norm_1426_7f771309` | **0.0773** | Normal | Standard transaction |
| `tx_norm_948_fb2ba0cf` | **0.0771** | Normal | Standard transaction |
| `tx_norm_1995_d57e6b5b` | **0.0771** | Normal | Standard transaction |
| `tx_norm_1361_a6c3ed3e` | **0.0769** | Normal | Standard transaction |
| `tx_norm_1856_b06c3e0b` | **0.0769** | Normal | Standard transaction |
| `tx_norm_2224_a57055b4` | **0.0767** | Normal | Standard transaction |
| `tx_norm_832_e7d30ed5` | **0.0764** | Normal | Standard transaction |
| `tx_norm_2506_e56ae6de` | **0.0762** | Normal | Standard transaction |
| `tx_norm_1066_ee17fd22` | **0.0761** | Normal | Standard transaction |
| `tx_norm_749_de1f9e6c` | **0.0760** | Normal | Standard transaction |
| `tx_norm_1520_0705daa6` | **0.0760** | Normal | Standard transaction |
| `tx_norm_928_327e210b` | **0.0756** | Normal | Standard transaction |
| `tx_norm_224_52edcb1e` | **0.0755** | Normal | Standard transaction |
| `tx_norm_2028_4eb26aa4` | **0.0751** | Normal | Standard transaction |
| `tx_norm_474_60c6b62e` | **0.0750** | Normal | Standard transaction |
| `tx_norm_365_9429808f` | **0.0748** | Normal | Standard transaction |
| `tx_norm_59_1427e8f3` | **0.0747** | Normal | Standard transaction |
| `tx_norm_1422_80e15d49` | **0.0747** | Normal | Standard transaction |
| `tx_norm_946_2e70cc7a` | **0.0744** | Normal | Standard transaction |
| `tx_norm_1006_04a89a9d` | **0.0744** | Normal | Standard transaction |
| `tx_norm_1157_20c69227` | **0.0744** | Normal | Standard transaction |
| `tx_norm_625_b4ba69da` | **0.0743** | Normal | Standard transaction |
| `tx_norm_1532_95ef5ae1` | **0.0743** | Normal | Standard transaction |
| `tx_norm_2256_81d757b9` | **0.0743** | Normal | Standard transaction |
| `tx_norm_2544_d05393df` | **0.0742** | Normal | Standard transaction |
| `tx_norm_1423_e2e16e15` | **0.0739** | Normal | Standard transaction |
| `tx_norm_829_ce498968` | **0.0738** | Normal | Standard transaction |
| `tx_norm_1826_8a81b5e6` | **0.0737** | Normal | Standard transaction |
| `tx_norm_640_a601114e` | **0.0735** | Normal | Standard transaction |
| `tx_norm_1225_51ebee24` | **0.0733** | Normal | Standard transaction |
| `tx_norm_1836_a7f8d406` | **0.0732** | Normal | Standard transaction |
| `tx_norm_354_a3b3d1ac` | **0.0731** | Normal | Standard transaction |
| `tx_norm_2051_834375b2` | **0.0731** | Normal | Standard transaction |
| `tx_norm_146_6ab1fa0b` | **0.0729** | Normal | Standard transaction |
| `tx_norm_1083_b1091d4d` | **0.0729** | Normal | Standard transaction |
| `tx_norm_2167_e511b450` | **0.0724** | Normal | Standard transaction |
| `tx_norm_1862_2b706cce` | **0.0720** | Normal | Standard transaction |
| `tx_norm_2439_fdce0639` | **0.0717** | Normal | Standard transaction |
| `tx_norm_2608_39363916` | **0.0717** | Normal | Standard transaction |
| `tx_norm_1428_fb1fa142` | **0.0705** | Normal | Standard transaction |
| `tx_norm_2217_a6e7d6cc` | **0.0704** | Normal | Standard transaction |
| `tx_norm_24_64dad3de` | **0.0699** | Normal | Standard transaction |
| `tx_norm_1289_e54d73b1` | **0.0699** | Normal | Standard transaction |
| `tx_norm_2390_50ea1167` | **0.0699** | Normal | Standard transaction |
| `tx_norm_1270_d5481094` | **0.0698** | Normal | Standard transaction |
| `tx_norm_428_b834a2a5` | **0.0697** | Normal | Standard transaction |
| `tx_norm_2519_a1985fc3` | **0.0693** | Normal | Standard transaction |
| `tx_norm_1518_bb64b562` | **0.0692** | Normal | Standard transaction |
| `tx_norm_2339_0a513173` | **0.0692** | Normal | Standard transaction |
| `tx_norm_857_cb0789fb` | **0.0691** | Normal | Standard transaction |
| `tx_norm_286_ffc1d19c` | **0.0688** | Normal | Standard transaction |
| `tx_norm_46_f292085f` | **0.0686** | Normal | Standard transaction |
| `tx_norm_2382_35239f4d` | **0.0684** | Normal | Standard transaction |
| `tx_norm_1511_dd5155cb` | **0.0679** | Normal | Standard transaction |
| `tx_norm_1555_889889be` | **0.0676** | Normal | Standard transaction |
| `tx_norm_544_e498c891` | **0.0674** | Normal | Standard transaction |
| `tx_norm_518_7575b9fe` | **0.0672** | Normal | Standard transaction |
| `tx_norm_2213_d3075b41` | **0.0672** | Normal | Standard transaction |
| `tx_norm_1433_8944b497` | **0.0669** | Normal | Standard transaction |
| `tx_norm_1964_c8038686` | **0.0669** | Normal | Standard transaction |
| `tx_norm_1000_17c73d4f` | **0.0667** | Normal | Standard transaction |
| `tx_norm_2450_aa857d49` | **0.0666** | Normal | Standard transaction |
| `tx_norm_2513_6a9e195c` | **0.0666** | Normal | Standard transaction |
| `tx_norm_623_70f8910d` | **0.0665** | Normal | Standard transaction |
| `tx_norm_233_2f56a344` | **0.0663** | Normal | Standard transaction |
| `tx_norm_1700_50d2e8d9` | **0.0663** | Normal | Standard transaction |
| `tx_norm_2601_27105014` | **0.0661** | Normal | Standard transaction |
| `tx_norm_1721_27e3bbd3` | **0.0659** | Normal | Standard transaction |
| `tx_norm_1184_a70b49aa` | **0.0658** | Normal | Standard transaction |
| `tx_norm_1628_c8278af4` | **0.0658** | Normal | Standard transaction |
| `tx_norm_2474_15ad8d0f` | **0.0656** | Normal | Standard transaction |
| `tx_norm_697_51bcfbeb` | **0.0645** | Normal | Standard transaction |
| `tx_norm_1137_93028af1` | **0.0645** | Normal | Standard transaction |
| `tx_norm_1497_eccac0d8` | **0.0644** | Normal | Standard transaction |
| `tx_norm_1999_60d98759` | **0.0643** | Normal | Standard transaction |
| `tx_norm_669_2dd5df4c` | **0.0639** | Normal | Standard transaction |
| `tx_norm_607_66ffa786` | **0.0634** | Normal | Standard transaction |
| `tx_norm_709_1ef8c02e` | **0.0628** | Normal | Standard transaction |
| `tx_norm_1047_4257ef37` | **0.0628** | Normal | Standard transaction |
| `tx_norm_1714_f12c3a26` | **0.0624** | Normal | Standard transaction |
| `tx_norm_688_e6077986` | **0.0622** | Normal | Standard transaction |
| `tx_norm_1002_a7fed34c` | **0.0620** | Normal | Standard transaction |
| `tx_norm_1043_540fe2c0` | **0.0618** | Normal | Standard transaction |
| `tx_norm_2241_4f49b6b8` | **0.0618** | Normal | Standard transaction |
| `tx_norm_859_b591f99c` | **0.0616** | Normal | Standard transaction |
| `tx_norm_1250_9ded0631` | **0.0614** | Normal | Standard transaction |
| `tx_norm_215_f8a97ed2` | **0.0613** | Normal | Standard transaction |
| `tx_norm_2225_a7f79119` | **0.0613** | Normal | Standard transaction |
| `tx_norm_1179_4e05f63f` | **0.0612** | Normal | Standard transaction |
| `tx_norm_1580_172d2a6d` | **0.0610** | Normal | Standard transaction |
| `tx_norm_1776_e94a561a` | **0.0609** | Normal | Standard transaction |
| `tx_norm_55_3d69c383` | **0.0608** | Normal | Standard transaction |
| `tx_norm_1177_9f390761` | **0.0608** | Normal | Standard transaction |
| `tx_norm_78_6c7ffa65` | **0.0606** | Normal | Standard transaction |
| `tx_norm_497_b87c64b2` | **0.0606** | Normal | Standard transaction |
| `tx_norm_1912_12c72f48` | **0.0605** | Normal | Standard transaction |
| `tx_norm_1231_d5d8b478` | **0.0604** | Normal | Standard transaction |
| `tx_norm_1069_f0c08ba5` | **0.0603** | Normal | Standard transaction |
| `tx_norm_86_063ac1f8` | **0.0600** | Normal | Standard transaction |
| `tx_norm_1922_08014ffd` | **0.0599** | Normal | Standard transaction |
| `tx_norm_2635_9db83404` | **0.0598** | Normal | Standard transaction |
| `tx_norm_2258_6085e9a4` | **0.0596** | Normal | Standard transaction |
| `tx_norm_183_8230b27d` | **0.0593** | Normal | Standard transaction |
| `tx_norm_499_761fb6b0` | **0.0590** | Normal | Standard transaction |
| `tx_norm_706_93bc92bf` | **0.0587** | Normal | Standard transaction |
| `tx_norm_2575_54428521` | **0.0586** | Normal | Standard transaction |
| `tx_norm_1094_ed57f0c9` | **0.0585** | Normal | Standard transaction |
| `tx_norm_2350_4da4d0e0` | **0.0582** | Normal | Standard transaction |
| `tx_norm_345_df09821e` | **0.0578** | Normal | Standard transaction |
| `tx_norm_370_39bb166b` | **0.0577** | Normal | Standard transaction |
| `tx_norm_2424_3b4c2e8c` | **0.0577** | Normal | Standard transaction |
| `tx_norm_1387_5b832b24` | **0.0576** | Normal | Standard transaction |
| `tx_norm_1793_610028f4` | **0.0572** | Normal | Standard transaction |
| `tx_norm_2034_bbe5aa40` | **0.0567** | Normal | Standard transaction |
| `tx_norm_363_2ce6428b` | **0.0565** | Normal | Standard transaction |
| `tx_norm_1229_67f91196` | **0.0565** | Normal | Standard transaction |
| `tx_norm_945_a8b8a2c4` | **0.0563** | Normal | Standard transaction |
| `tx_norm_322_75c8ad63` | **0.0562** | Normal | Standard transaction |
| `tx_norm_2076_4179ee7b` | **0.0560** | Normal | Standard transaction |
| `tx_norm_1662_d98e4141` | **0.0552** | Normal | Standard transaction |
| `tx_norm_593_c7cd1259` | **0.0551** | Normal | Standard transaction |
| `tx_norm_412_c75de62a` | **0.0550** | Normal | Standard transaction |
| `tx_norm_2174_86bc4365` | **0.0550** | Normal | Standard transaction |
| `tx_norm_2563_bd429b77` | **0.0545** | Normal | Standard transaction |
| `tx_norm_2356_32f4c372` | **0.0542** | Normal | Standard transaction |
| `tx_norm_138_c12bf2cb` | **0.0541** | Normal | Standard transaction |
| `tx_norm_1451_949cb81e` | **0.0541** | Normal | Standard transaction |
| `tx_norm_2237_8c71f282` | **0.0540** | Normal | Standard transaction |
| `tx_norm_475_8093c516` | **0.0534** | Normal | Standard transaction |
| `tx_norm_801_5ab914bb` | **0.0534** | Normal | Standard transaction |
| `tx_norm_380_fbd7822c` | **0.0530** | Normal | Standard transaction |
| `tx_norm_1295_a1f458b9` | **0.0530** | Normal | Standard transaction |
| `tx_norm_739_4d5d5cb2` | **0.0529** | Normal | Standard transaction |
| `tx_norm_58_2afcc9a5` | **0.0528** | Normal | Standard transaction |
| `tx_norm_1007_cd29d122` | **0.0528** | Normal | Standard transaction |
| `tx_norm_93_796dd8c5` | **0.0527** | Normal | Standard transaction |
| `tx_norm_339_d1d7862a` | **0.0527** | Normal | Standard transaction |
| `tx_norm_2623_16e81b0e` | **0.0525** | Normal | Standard transaction |
| `tx_norm_787_d3dbdc28` | **0.0523** | Normal | Standard transaction |
| `tx_norm_2372_7beb71d6` | **0.0519** | Normal | Standard transaction |
| `tx_norm_2408_c1adb71a` | **0.0517** | Normal | Standard transaction |
| `tx_norm_1427_b2c4780d` | **0.0513** | Normal | Standard transaction |
| `tx_norm_2477_3c705e43` | **0.0506** | Normal | Standard transaction |
| `tx_norm_996_91e6491b` | **0.0505** | Normal | Standard transaction |
| `tx_norm_2347_314443bf` | **0.0504** | Normal | Standard transaction |
| `tx_norm_468_1001867b` | **0.0502** | Normal | Standard transaction |
| `tx_norm_2182_38dbdcdb` | **0.0499** | Normal | Standard transaction |
| `tx_norm_793_e7716814` | **0.0498** | Normal | Standard transaction |
| `tx_norm_591_d49ae7b3` | **0.0490** | Normal | Standard transaction |
| `tx_norm_693_7fec2add` | **0.0486** | Normal | Standard transaction |
| `tx_norm_1583_37994c3c` | **0.0486** | Normal | Standard transaction |
| `tx_norm_2484_ddb1a86e` | **0.0486** | Normal | Standard transaction |
| `tx_norm_1311_3cda3cae` | **0.0485** | Normal | Standard transaction |
| `tx_norm_362_278536d5` | **0.0473** | Normal | Standard transaction |
| `tx_norm_1148_4811311c` | **0.0473** | Normal | Standard transaction |
| `tx_norm_1603_8e41057d` | **0.0471** | Normal | Standard transaction |
| `tx_norm_802_2e93b3db` | **0.0467** | Normal | Standard transaction |
| `tx_norm_2636_a58a235d` | **0.0467** | Normal | Standard transaction |
| `tx_norm_313_6767c100` | **0.0463** | Normal | Standard transaction |
| `tx_norm_1758_17cb578d` | **0.0458** | Normal | Standard transaction |
| `tx_norm_2303_639b3d08` | **0.0456** | Normal | Standard transaction |
| `tx_norm_1226_d89f5acd` | **0.0454** | Normal | Standard transaction |
| `tx_norm_961_02838771` | **0.0451** | Normal | Standard transaction |
| `tx_norm_636_521d4f3b` | **0.0450** | Normal | Standard transaction |
| `tx_norm_2054_a8e6687f` | **0.0450** | Normal | Standard transaction |
| `tx_norm_1418_dc1436d9` | **0.0447** | Normal | Standard transaction |
| `tx_norm_1942_733eb959` | **0.0446** | Normal | Standard transaction |
| `tx_norm_207_c88bc49d` | **0.0442** | Normal | Standard transaction |
| `tx_norm_1296_8bc6779a` | **0.0442** | Normal | Standard transaction |
| `tx_norm_2210_68ee556f` | **0.0442** | Normal | Standard transaction |
| `tx_norm_150_7b97973c` | **0.0440** | Normal | Standard transaction |
| `tx_norm_889_6e95889a` | **0.0439** | Normal | Standard transaction |
| `tx_norm_245_cc581bb1` | **0.0438** | Normal | Standard transaction |
| `tx_norm_1566_84ea3cf9` | **0.0438** | Normal | Standard transaction |
| `tx_norm_2082_c98a7add` | **0.0437** | Normal | Standard transaction |
| `tx_norm_1507_c52c4b05` | **0.0435** | Normal | Standard transaction |
| `tx_norm_1331_ea8ad2e2` | **0.0433** | Normal | Standard transaction |
| `tx_norm_2355_f7dd98fe` | **0.0432** | Normal | Standard transaction |
| `tx_norm_449_5cb725dc` | **0.0425** | Normal | Standard transaction |
| `tx_norm_2170_59c39327` | **0.0420** | Normal | Standard transaction |
| `tx_norm_1161_a9d53829` | **0.0415** | Normal | Standard transaction |
| `tx_norm_1463_ee928b73` | **0.0413** | Normal | Standard transaction |
| `tx_norm_1741_dfff4cea` | **0.0408** | Normal | Standard transaction |
| `tx_norm_674_e5c31d09` | **0.0406** | Normal | Standard transaction |
| `tx_norm_1984_025e7a87` | **0.0405** | Normal | Standard transaction |
| `tx_norm_1719_cf3081a1` | **0.0403** | Normal | Standard transaction |
| `tx_norm_545_65487c97` | **0.0402** | Normal | Standard transaction |
| `tx_norm_588_a9fac1cd` | **0.0402** | Normal | Standard transaction |
| `tx_norm_202_1243cde7` | **0.0401** | Normal | Standard transaction |
| `tx_norm_1846_c6b155c5` | **0.0399** | Normal | Standard transaction |
| `tx_norm_260_4ce5a64a` | **0.0396** | Normal | Standard transaction |
| `tx_norm_2483_08607726` | **0.0396** | Normal | Standard transaction |
| `tx_norm_182_2d2f63be` | **0.0395** | Normal | Standard transaction |
| `tx_norm_2075_d079ba1d` | **0.0392** | Normal | Standard transaction |
| `tx_norm_335_e693b3c4` | **0.0391** | Normal | Standard transaction |
| `tx_norm_2105_616461c4` | **0.0385** | Normal | Standard transaction |
| `tx_norm_73_f1a150ce` | **0.0379** | Normal | Standard transaction |
| `tx_norm_1444_24f8028c` | **0.0378** | Normal | Standard transaction |
| `tx_norm_2578_c706c667` | **0.0378** | Normal | Standard transaction |
| `tx_norm_1655_4a6d3581` | **0.0375** | Normal | Standard transaction |
| `tx_norm_2095_68c98b61` | **0.0361** | Normal | Standard transaction |
| `tx_norm_1491_d11cf4d3` | **0.0351** | Normal | Standard transaction |
| `tx_norm_2181_efadd6be` | **0.0350** | Normal | Standard transaction |
| `tx_norm_1770_ad41b413` | **0.0341** | Normal | Standard transaction |
| `tx_norm_990_881dfad5` | **0.0339** | Normal | Standard transaction |
| `tx_norm_60_edb7204e` | **0.0337** | Normal | Standard transaction |
| `tx_norm_937_eb38f78b` | **0.0335** | Normal | Standard transaction |
| `tx_norm_615_c2fda8d0` | **0.0332** | Normal | Standard transaction |
| `tx_norm_1020_9dcff890` | **0.0323** | Normal | Standard transaction |
| `tx_norm_168_dcfd6fd5` | **0.0314** | Normal | Standard transaction |
| `tx_norm_1114_d8418684` | **0.0304** | Normal | Standard transaction |
| `tx_norm_2455_6958bf6b` | **0.0297** | Normal | Standard transaction |
| `tx_norm_2073_19ac3ed6` | **0.0296** | Normal | Standard transaction |
| `tx_norm_455_7685ebce` | **0.0294** | Normal | Standard transaction |
| `tx_norm_1162_763d6867` | **0.0294** | Normal | Standard transaction |
| `tx_norm_327_78b449fc` | **0.0290** | Normal | Standard transaction |
| `tx_norm_1096_aa7923c9` | **0.0289** | Normal | Standard transaction |
| `tx_norm_505_0ef329cf` | **0.0288** | Normal | Standard transaction |
| `tx_norm_1696_6d022bb1` | **0.0287** | Normal | Standard transaction |
| `tx_norm_2555_e4710c82` | **0.0285** | Normal | Standard transaction |
| `tx_norm_484_295926b2` | **0.0280** | Normal | Standard transaction |
| `tx_norm_1754_71c270a8` | **0.0279** | Normal | Standard transaction |
| `tx_norm_2472_d1b181f3` | **0.0273** | Normal | Standard transaction |
| `tx_norm_77_1c7e9ae1` | **0.0272** | Normal | Standard transaction |
| `tx_norm_1598_5da9c770` | **0.0270** | Normal | Standard transaction |
| `tx_norm_422_62e15f71` | **0.0268** | Normal | Standard transaction |
| `tx_norm_641_4d645fc0` | **0.0268** | Normal | Standard transaction |
| `tx_norm_1928_cd20df78` | **0.0266** | Normal | Standard transaction |
| `tx_norm_2343_b61fe194` | **0.0266** | Normal | Standard transaction |
| `tx_norm_1071_46d5ffcd` | **0.0260** | Normal | Standard transaction |
| `tx_norm_2365_f99d6935` | **0.0259** | Normal | Standard transaction |
| `tx_norm_1893_3e4cf856` | **0.0258** | Normal | Standard transaction |
| `tx_norm_1135_4dd7814d` | **0.0238** | Normal | Standard transaction |
| `tx_norm_517_48e0507b` | **0.0210** | Normal | Standard transaction |
| `tx_norm_2176_da8ee8e1` | **0.0202** | Normal | Standard transaction |
| `tx_norm_2605_3305646b` | **0.0202** | Normal | Standard transaction |
| `tx_norm_2306_f42e8b83` | **0.0201** | Normal | Standard transaction |
| `tx_norm_0_ddd9a366` | **0.0196** | Normal | Standard transaction |
| `tx_norm_2081_39b3bae7` | **0.0193** | Normal | Standard transaction |
| `tx_norm_136_55259ed7` | **0.0186** | Normal | Standard transaction |
| `tx_norm_2057_dc30d10e` | **0.0184** | Normal | Standard transaction |
| `tx_norm_1191_acf70957` | **0.0181** | Normal | Standard transaction |
| `tx_norm_1410_20192712` | **0.0181** | Normal | Standard transaction |
| `tx_norm_508_f8800539` | **0.0179** | Normal | Standard transaction |
| `tx_norm_694_3dfc34fa` | **0.0179** | Normal | Standard transaction |
| `tx_norm_916_8cc80ee9` | **0.0177** | Normal | Standard transaction |
| `tx_norm_1022_45d9c46f` | **0.0174** | Normal | Standard transaction |
| `tx_norm_1797_dcc2f3cd` | **0.0168** | Normal | Standard transaction |
| `tx_norm_1372_e068f5bf` | **0.0164** | Normal | Standard transaction |
| `tx_norm_1037_8a1e7c46` | **0.0157** | Normal | Standard transaction |
| `tx_norm_2201_bab87775` | **0.0155** | Normal | Standard transaction |
| `tx_norm_765_c90dbf27` | **0.0150** | Normal | Standard transaction |
| `tx_norm_2430_038a0aba` | **0.0142** | Normal | Standard transaction |
| `tx_norm_144_28ece203` | **0.0139** | Normal | Standard transaction |
| `tx_norm_95_d2a84ee9` | **0.0126** | Normal | Standard transaction |
| `tx_norm_1212_a75a6c28` | **0.0113** | Normal | Standard transaction |
| `tx_norm_174_ce96f8ad` | **0.0104** | Normal | Standard transaction |
| `tx_norm_878_85bb3588` | **0.0102** | Normal | Standard transaction |
| `tx_norm_294_9e0e8cd3` | **0.0096** | Normal | Standard transaction |
| `tx_norm_1431_ec93cb3d` | **0.0092** | Normal | Standard transaction |
| `tx_norm_2169_3d38ae17` | **0.0090** | Normal | Standard transaction |
| `tx_norm_1592_cdf8f84d` | **0.0085** | Normal | Standard transaction |
| `tx_norm_2344_7644e2e2` | **0.0077** | Normal | Standard transaction |
| `tx_norm_2582_78a02b78` | **0.0077** | Normal | Standard transaction |
| `tx_norm_453_3c525808` | **0.0073** | Normal | Standard transaction |
| `tx_norm_1055_8767a9bd` | **0.0057** | Normal | Standard transaction |
| `tx_norm_152_b7bdd67a` | **0.0048** | Normal | Standard transaction |
| `tx_norm_838_3bf76936` | **0.0048** | Normal | Standard transaction |
| `tx_norm_1019_fa231553` | **0.0046** | Normal | Standard transaction |
| `tx_norm_2191_f8ab35f9` | **0.0041** | Normal | Standard transaction |
| `tx_norm_2177_9b97639b` | **0.0039** | Normal | Standard transaction |
| `tx_norm_213_44bc346c` | **0.0036** | Normal | Standard transaction |
| `tx_norm_85_3bfd73c9` | **0.0035** | Normal | Standard transaction |
| `tx_norm_1764_e59539c0` | **0.0027** | Normal | Standard transaction |
| `tx_norm_896_1ff1c1df` | **0.0026** | Normal | Standard transaction |
| `tx_norm_2460_1ff30885` | **0.0018** | Normal | Standard transaction |
| `tx_norm_1448_d06cfc21` | **0.0006** | Normal | Standard transaction |
| `tx_norm_1523_0e641446` | **0.0003** | Normal | Standard transaction |
| `tx_norm_1086_9ade7df8` | **0.0000** | Normal | Standard transaction |
| `tx_norm_1315_b84d8cae` | **0.0000** | Normal | Standard transaction |
| `tx_norm_1380_e2990347` | **0.0000** | Normal | Standard transaction |
| `tx_norm_1413_994b93d6` | **0.0000** | Normal | Standard transaction |
| `tx_norm_1682_371a2fd0` | **0.0000** | Normal | Standard transaction |
| `tx_norm_1722_907f36e4` | **0.0000** | Normal | Standard transaction |
| `tx_norm_1785_e4e7e716` | **0.0000** | Normal | Standard transaction |
| `tx_norm_2149_15785048` | **0.0000** | Normal | Standard transaction |
| `tx_norm_2389_dcc52f29` | **0.0000** | Normal | Standard transaction |
| `tx_norm_2476_c8122f33` | **0.0000** | Normal | Standard transaction |

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

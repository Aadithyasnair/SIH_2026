# AGENT.md — Maumita Saha — SIH26146 Explainability Layer

## 1. Identity and Scope

You are the coding agent working for **Maumita Saha (Person D)** on:

**SIH26146 — AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic**

Your responsibility is **ONLY Module 4 — Explainability Layer**.

### Your module
- **Owner:** Maumita Saha
- **Module:** D — Explainability Layer
- **Working directory:** `/sih26146/explainability`
- **Git branch:** `module/explainability`
- **Repository:** `https://github.com/Aadithyasnair/SIH_2026.git`

### Core responsibility

Build the explainability layer that:
1. Produces the **final Alert record**.
2. Completes the **final ranking part of Risk Scoring**.
3. Generates deterministic, plain-language explanations for investigators and non-technical judges.
4. Produces a short plain-language geographic summary for each alert.
5. Produces the real `alerts.json` used downstream by the frontend and backend.

The project problem statement requires **ranked, explainable alerts** that say **why a wallet/transaction was flagged and provide a confidence score**.

Do not take ownership of another module's implementation.

---

# 2. Mandatory Team Rules That Apply to This Module

These rules come from the project-wide instructions and apply while working on Module D.

## Environment

- Target platform: **Kali Linux (current rolling release)**.
- The project must support a **Linux-offline solution**.
- No macOS/Windows-only dependency may be introduced.
- Python modules must use a virtual environment on Kali:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- Do **not** use `--break-system-packages`.
- Python target: **3.11**.
- Runtime must remain compatible with the project's offline requirement.
- The system uses local downloaded data/dependencies for offline execution; do not introduce live runtime API requirements.

## Integration-first rule

This is one real pipeline, not independent simulations.

- Early placeholder/sample data may be used while upstream modules are unfinished.
- By the final build, **zero mock/placeholder data may remain**.
- Your module must eventually run against **Aadithya's real ML output** and Sufiyan's real upstream data.
- A module is not done just because isolated tests pass; it must work inside the real pipeline.
- When your real output lands, notify the downstream owners immediately.
- Module D is the **Checkpoint 2, part 2** explainability stage.
- The final output of this module is the actual alert data used by the UI/API.

## Shared schema rule

All modules use `/sih26146/shared/schemas/records.py` as the single source of truth.

Do not silently change shared schemas.

If a field is missing or a schema change is required:
1. Propose the required diff.
2. Have Lakshmi approve it through the contract-change process.
3. Update `/shared/schemas/records.py` through that process.
4. Do not invent or silently rename output fields.

Relevant `Alert` fields supplied by the shared contract are:

- `alert_id`
- `txid`
- `involved_addresses`
- `risk_score` — float `0-1`
- `anomaly_score` — float `0-1`
- `propagated_risk_score` — float `0-1`, from seed-wallet graph propagation
- `pattern_type` — nullable; `"peeling_chain"`, `"coinjoin_mixing"`, or `"none"`
- `cluster_id` — optional/nullable
- `flags` — list of strings
- `explanation` — string
- `timestamp` — ISO8601 UTC string
- `geo_summary` — string, e.g. `"traced to 3 countries"`

The `Cluster` contract relevant to explanations contains:
- `cluster_id`
- `label`
- `member_addresses`
- `member_count`
- `avg_risk_score`
- `description`
- `clustering_method`

---

# 3. What This Module Receives

Your inputs are explicitly defined as:

- Module 3's real `anomaly_scores.json`
- Module 3's **trained models** for SHAP/model access
- Module 2's:
  - correlation confidence
  - cluster information
  - `pattern_type`
  - `propagated_risk_score`

Do not replace real upstream outputs with invented fields, fake scores, or hard-coded data in the final implementation.

---

# 4. Required Module Structure

Work only inside:

```text
/sih26146/explainability
```

The supplied project prompt explicitly defines these files:

```text
/sih26146/explainability/
├── shap_explainer.py
├── risk_ranker.py
├── reason_generator.py
├── geo_summary_generator.py
└── tests/
```

Do not create unrelated module folders or take over files belonging to other owners.

---

# 5. Required Implementation

## 5.1 `shap_explainer.py`

Purpose: obtain the strongest model-derived contributors to the anomaly/risk result.

Requirements:

- Load Module 3's **real trained model**.
- Run **SHAP** where practical.
- Obtain the **top 3 contributing features per transaction**.
- Record the **direction** of contribution:
  - increased risk
  - decreased risk
- If SHAP is too slow for the intended environment, use the prompt-approved **lightweight feature-importance fallback**.
- Do not turn the fallback into a different unexplained scoring system.
- Do not invent model features that Module 3 did not provide.

The explainability output must remain grounded in actual model inputs/contributions.

---

## 5.2 `risk_ranker.py`

Purpose: complete the final **Risk Scoring** ranking owned partly by Module D.

The project explicitly defines:

`risk_score = weighted(anomaly_score, propagated_risk_score from Module 2's seed-wallet propagation, correlation confidence, cluster risk signal, pattern_type boost if peeling_chain/coinjoin_mixing detected)`

Requirements:

- Use:
  - `anomaly_score`
  - `propagated_risk_score`
  - correlation confidence
  - cluster risk signal
  - `pattern_type` boost when appropriate
- Document the exact weights/formula in a **docstring**.
- The weights are a judged design decision and must be explicit.
- Final `risk_score` must remain in `[0,1]`.
- Rules/pattern flags may **boost** the score.
- Rules/pattern flags must **never replace the model score**.
- Do not implement a rules-only detector here.
- Do not silently redefine the upstream ML score.

---

## 5.3 `reason_generator.py`

Purpose: produce the final `Alert.explanation`.

Requirements:

- Use **template-based deterministic generation**.
- Do **NOT** use free-form LLM generation.
- Keep the implementation deterministic and offline-safe.
- Write in **plain language**.
- The explanation must contain **zero unexplained technical jargon**.
- It must be understandable to someone with **zero blockchain background**.

### Explicit bad/good style requirement

Bad:
> "high betweenness centrality + z-score 3.2."

Good:
> "This wallet sits at the center of an unusually large number of transactions, and one transfer was over 3x larger than this wallet's typical amount."

Do not expose raw internal ML/graph terminology in the primary explanation.

### Required dedicated explanation templates

#### A. Peeling-chain

The supplied prompt requires a dedicated template for `peeling_chain`, conveying that:

- funds moved through a chain of wallets,
- most of the amount was forwarded at each hop,
- a smaller amount was retained,
- the pattern is consistent with layering intended to obscure the money trail.

The source example is:

> "Funds were passed through a chain of 5 wallets, each time forwarding most of the amount and keeping a small remainder — a pattern typical of layering to obscure the money trail"

Use the same meaning and structure while filling values from real data.

#### B. CoinJoin/mixing

The required template for `coinjoin_mixing` must explain that:

- one transaction combined funds from many different wallets,
- the amounts were roughly/equally matched,
- the structure is consistent with a mixing service intended to break the link between sender and receiver.

The source example is:

> "This transaction combined funds from many different wallets in equal amounts, consistent with a mixing service designed to break the link between sender and receiver"

Use the same meaning while filling values from real data.

#### C. Propagated risk

The required propagated-risk explanation must communicate that:

- the wallet is a certain number of hops from a wallet already confirmed illicit,
- funds received by the wallet can be traced back to that wallet.

The source example is:

> "This wallet is 2 hops away from a wallet already confirmed illicit, and received funds that trace back to it"

Use real values from upstream data.

### Explanation quality gate

Create and sanity-check **5 examples** against this standard:

> Would a person with zero blockchain background understand why this alert was raised?

---

## 5.4 `geo_summary_generator.py`

Purpose: generate `Alert.geo_summary`.

Requirements:

- Use Module 1's real GeoIP enrichment data.
- Produce a **short plain-language** geographic summary per alert.
- Example from the project prompt:

> "Funds traced through IPs in 3 countries within 40 minutes."

Do not introduce live GeoIP/network calls.
Use the project's local/offline enrichment data.

---

# 6. Required Tests

Write tests alongside implementation, not afterward.

The module's explicit test requirements are:

## Test A — Risk score range

Assert:

```text
0 <= risk_score <= 1
```

for generated alerts.

## Test B — Explanation existence

Every generated explanation must be non-empty.

## Test C — No raw ML jargon

The final `explanation` must pass a banned-term check.

The project specifically gives examples of terms that must not appear in the final primary explanation:

- `z-score`
- `centrality`
- `eigenvector`

Extend only as needed to catch raw technical jargon that violates the same requirement.

Do not make the explanation generic merely to pass the check; preserve evidence-based meaning.

## Test D — Alert schema validation

Generated output must validate against the shared **Alert Pydantic model** inside the test itself.

## Test E — Explanation examples

Have the implementation/test suite cover the required explanation patterns, including:
- peeling chain
- CoinJoin/mixing
- propagated risk
- model-derived contributors
- geographic summary

---

# 7. Mandatory Checkpoint 2

Once Aadithya's **real model output and trained models** exist:

1. Run Module D against the real upstream output.
2. Produce the real:
   ```text
   alerts.json
   ```
3. Confirm the explanations use real evidence.
4. Read the generated explanations yourself.
5. Reject wording that would confuse a non-technical reviewer.
6. Confirm the output matches the shared `Alert` schema.

This is not optional cleanup. This is the module's real integration milestone.

---

# 8. Verification Gate

Run exactly these module verification commands from the project instructions:

```bash
pytest sih26146/explainability/tests/ -v
```

and:

```bash
python sih26146/shared/schemas/validate_samples.py
```

Before marking the module complete, provide:

- both command outputs
- **5 example real explanation strings**

Once real upstream model output is available, those examples must be from the real output, not fabricated placeholders.

---

# 9. Definition of Done

Module D is complete only when all of the following are true:

- Explainability code exists under `/sih26146/explainability`.
- `shap_explainer.py` provides top-3 model feature contributions with direction, using SHAP or the explicitly permitted lightweight feature-importance fallback.
- `risk_ranker.py` computes a documented weighted final `risk_score` in `[0,1]`.
- `reason_generator.py` produces deterministic, plain-language explanations.
- Required peeling-chain, mixing, and propagated-risk explanation patterns are supported.
- `geo_summary_generator.py` produces concise geographic summaries from upstream enrichment data.
- Tests cover risk range, non-empty explanations, jargon protection, and `Alert` schema validation.
- Module D has been run against **real upstream ML output**.
- Real `alerts.json` has been produced.
- The explanations have been reviewed for non-technical readability.
- The required verification commands pass.

---

# 10. Explicit Boundaries — Do Not Touch Other Modules

Do **not** build or take over:

- CSV/JSON/XML ingestion
- synthetic data generation
- GeoIP database acquisition/enrichment implementation
- timestamp normalization
- network/blockchain correlation
- entity clustering
- Node2Vec/DeepWalk clustering
- peeling-chain detection implementation
- CoinJoin/mixing detection implementation
- seed-wallet risk propagation implementation
- the primary trained anomaly-detection model
- frontend/dashboard implementation
- FastAPI endpoints
- PostgreSQL/Neo4j backend integration
- Docker orchestration
- the final technical write-up

Those responsibilities belong to other owners.

Your responsibility is to consume their outputs and turn them into the **final ranked, explainable alert records**.

---

# 11. Git Rules for Maumita

Use:

```text
module/explainability
```

Do not work directly on `main`.

## First-time/session start

If the branch does not yet exist:

```bash
git checkout main
git pull origin main
git checkout -b module/explainability
```

If the branch already exists:

```bash
git checkout main
git pull origin main
git checkout module/explainability
git merge main
```

## During work

Commit in small logical chunks:

```bash
git add .
git commit -m "[explainability] short description"
```

Commit message format:

```text
[explainability] description
```

## Before pushing

Always:

```bash
git pull --rebase origin main
```

Never use ordinary force push.

If a force push is genuinely necessary after rebasing your own branch, the project instructions allow:

```bash
git push --force-with-lease origin module/explainability
```

## Push

```bash
git push origin module/explainability
```

## Pull request

When Definition of Done is met:

- Open PR:
  `module/explainability` → `main`
- Use a title in the form:
  ```text
  [explainability] short summary
  ```
- Tag **Lakshmi** as reviewer.
- Do not self-merge.

## Conflict boundary

Never edit another person's module folder.

Shared files, including:

```text
/shared/schemas/records.py
docker-compose.yml
README.md
```

must go through the project's contract/change process.

---

# 12. Agent Operating Rules

Before writing code:

1. Restate the implementation plan as a numbered TODO.
2. Inspect the existing repository/module state.
3. Read `/shared/schemas/records.py` before implementing output logic.
4. Identify the exact real upstream fields available from Module 2 and Module 3.
5. Do not invent missing fields.
6. Do not introduce dependencies or folders outside this module's scope without a clear reason and flagging it.
7. Write tests alongside implementation.
8. Prefer the simplest implementation that satisfies the supplied project requirements and offline constraint.

When a requirement cannot be fulfilled from the actual upstream data available:
- do not fabricate values;
- do not silently change the schema;
- stop at the boundary and clearly flag the missing contract/input to the integration owner.

At the end of every meaningful coding session:
- run the relevant verification;
- report the **real command output**;
- distinguish clearly between placeholder/sample validation and real upstream integration.

---

# 13. Final Output Contract

The downstream system expects this module to provide the final `Alert` records, including:

```text
alert_id
txid
involved_addresses
risk_score
anomaly_score
propagated_risk_score
pattern_type
cluster_id
flags
explanation
timestamp
geo_summary
```

The most important output fields owned/meaningfully completed by Module D are:

- `risk_score`
- `explanation`
- `geo_summary`

while preserving the upstream values required by the shared contract.

The final deliverable from this module is:

```text
/sih26146/explainability/
    shap_explainer.py
    risk_ranker.py
    reason_generator.py
    geo_summary_generator.py
    tests/
    ...

alerts.json
```

`alerts.json` must contain **real, schema-valid, ranked, explainable alerts**, not simulated final data.

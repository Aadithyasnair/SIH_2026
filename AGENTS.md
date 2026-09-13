# SIH26146 — Project Context

## Project

**SIH26146 — AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic**

Repository:

`https://github.com/Aadithyasnair/SIH_2026.git`

This repository contains a multi-module system for monitoring, correlating, analyzing, and detecting anomalous Bitcoin transaction traffic.

---

# Project Architecture

The system is divided into modules:

```text
A — Data Ingestion
B — Correlation / Clustering / Pattern / Risk
C — AI/ML Detection
D — Explainability
E — Frontend
F — Backend / Integration
```

Aadithya owns:

```text
/ml_detection
```

Do not modify another person's module unless explicitly required for an integration or shared-contract change.

---

# Target Environment

Primary target:

* Kali Linux
* Python 3.11
* Node.js 20 where applicable
* Docker for infrastructure services

Do not introduce dependencies that work only on Windows or macOS.

---

# Python Environment

Use a Python virtual environment.

Do NOT use:

```bash
pip install --break-system-packages
```

Prefer:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Use the existing project's environment/dependency configuration when available.

Do not unnecessarily introduce new dependencies.

---

# Infrastructure

Infrastructure services such as PostgreSQL and Neo4j are expected to run through Docker.

Do not assume Neo4j is installed directly on the host.

GeoIP data should use the project's local GeoIP resources rather than requiring an external runtime service.

---

# Shared Contracts

Before implementing any module, inspect:

```text
/shared/schemas/
```

The shared data contracts are authoritative.

Important shared entities include:

```text
NetworkEvent
BlockchainTxn
CorrelationEdge
Alert
Cluster
```

Do not silently modify shared schemas.

If a module requires a field that does not exist, identify the schema gap and report it before independently changing the contract.

Shared-contract changes must be coordinated with the team.

---

# Shared Data

Sample and evaluation data are located under:

```text
/shared/sample_data/
```

Sample data may be used during initial development.

However, placeholder/sample data must not become a permanent substitute for real module-to-module integration.

When upstream modules become available, downstream modules must be tested and retrained/re-evaluated against real outputs where applicable.

---

# Integration-First Development

Modules are independent during development but must respect the shared contracts.

Do not create isolated implementations that cannot consume the outputs of other modules.

When an upstream module becomes available:

1. Inspect its actual output.
2. Validate it against the shared schema.
3. Adapt only where necessary.
4. Test the integration.
5. Replace temporary sample assumptions with real pipeline data.

---

# Agent Development Rules

Before writing code:

1. Inspect the repository.
2. Inspect the relevant module.
3. Inspect shared schemas.
4. Inspect existing utilities and dependencies.
5. Inspect available sample data.
6. Produce a numbered TODO plan.
7. Implement incrementally.

Do not assume files exist.

Do not invent project infrastructure that has not been inspected.

Do not rewrite working code unnecessarily.

---

# Testing

Tests should be written alongside implementation.

Before declaring work complete:

* Run the relevant tests.
* Validate the shared schemas.
* Verify imports.
* Verify saved artifacts where applicable.
* Verify integration with real data where applicable.

Never claim a test passed unless it was actually executed.

Include the actual verification result when reporting completion.

---

# Git Rules

Use a dedicated branch for each module.

Aadithya's branch:

```text
module/ml_detection
```

Never push directly to:

```text
main
```

Before pushing:

```bash
git pull --rebase origin main
```

Commit format:

```text
[ml_detection] description
```

Do not force-push shared branches.

Do not modify another contributor's module without coordination.

---

# Change Management

If implementation requires changing a shared schema or cross-module contract:

1. Identify the required change.
2. Explain why it is required.
3. Coordinate the change.
4. Update affected modules.
5. Run relevant validation.

Do not silently change a shared contract to make local code work.

---

# Module Ownership

| Module                                        | Owner              | Directory         |
| --------------------------------------------- | ------------------ | ----------------- |
| A — Ingestion                                 | A Madhumitha A Rao | `/ingestion`      |
| B — Correlation / Clustering / Pattern / Risk | Sufiyan Khan       | `/correlation`    |
| C — AI/ML Detection                           | Aadithya S Nair    | `/ml_detection`   |
| D — Explainability                            | Maumita Saha       | `/explainability` |
| E — Frontend                                  | Mohammed Saleem    | `/frontend`       |
| F — Backend / Integration                     | Lakshmi A          | `/backend`        |

Aadithya's implementation instructions are defined in:

```text
/ml_detection/AGENTS.md
```

When working inside `/ml_detection`, follow that file as the module-specific authority.

---

# General Principle

Build the real system, not a demonstration-only mock.

Prefer:

* Real data
* Real models
* Real validation
* Real module integration
* Reproducible pipelines
* Tested interfaces
* Explicit failures

Avoid:

* Hardcoded results
* Fake model outputs
* Placeholder implementations presented as complete
* Silent schema changes
* Unverified claims
* Unnecessary rewrites

When a requirement cannot be satisfied honestly with the available data or infrastructure, report the limitation instead of fabricating a result.

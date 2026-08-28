# Manager — Ecosystem Manager (Skill / Agent / Environment Lifecycle & Configuration)

> Unified configuration, schema, sanitizer and deployment management center for the Airymax platform.
> A leaf repository under the [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem).

**Language:** English | [简体中文](README_zh.md)

[![Version](https://img.shields.io/badge/version-0.1.1-5a6b7e)](https://atomgit.com/openairymax/manager)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-feature%2Fofficial--hubs--01-6f7b8e)](https://atomgit.com/openairymax/manager)

**Repository:** `git@atomgit.com:openairymax/manager.git` · **Branch:** `feature/official-hubs-01`

---

## Overview

`ecosystem/manager/` is the **unified configuration and lifecycle management center** of the Airymax AI Agent Runtime Platform. It is the single source of truth for every configuration consumed by the AgentRT runtime, the build toolchain, the observability stack and the surrounding daemons. The repository owns three core management responsibilities — **skill management**, **agent management** and **environment management** — alongside schema validation, sanitizer suppressions, security policy and deployment templates.

The repository is **schema-driven**: every YAML / JSON file is validated against a JSON Schema before it is allowed to take effect, and every change is captured in an auditable audit log. It maintains `skill/registry.yaml` (10 registered skills), `agent/registry.yaml` (12 registered agents with capabilities, dual-system models, RBAC permissions, cost profiles and trust metrics) and `environment/{development,staging,production}.yaml` overlays that are merged on top of the base `configs/agentrt.yaml` (v0.1.1).

Within the ecosystem layer, `manager/` sits at the foundation: it has **no upstream Airymax repository dependency** (it is the configuration root), and is consumed downstream by the AgentRT runtime, the build toolchain, the Cupolas security module, the `tool_d` daemon, CI/CD pipelines and operators. It is what makes every other ecosystem component reproducible, validated and auditable.

## Directory Structure

```
manager/
├── schema/                            # JSON Schema definitions (11 files, ~272 rules)
│   ├── _metadata.schema.json          # Schema metadata & versioning
│   ├── agent-registry.schema.json     # Agent registry
│   ├── config-audit-log.schema.json   # Configuration audit log
│   ├── config-management.schema.json  # Manager self-management
│   ├── kernel-settings.schema.json    # Kernel settings
│   ├── logging.schema.json            # Logging configuration
│   ├── model.schema.json              # Model configuration
│   ├── sanitizer-rules.schema.json    # Sanitizer rules
│   ├── security-policy.schema.json    # Security policy
│   ├── skill-registry.schema.json     # Skill registry
│   └── tool-service.schema.json       # tool_d service
├── sanitizer/                         # Sanitizer suppressions + input rules
│   ├── sanitizer_rules.json           # 25 input rules across 7 attack categories
│   ├── lsan-suppressions              # LeakSanitizer suppression file
│   └── valgrind-suppressions          # Valgrind suppression file
├── security/                          # Security policy & RBAC
│   └── policy.yaml                    # Default policy, sandbox, audit, intrusion detection
│                                      # (tool ACL runtime template: tools/scripts/ops/templates)
├── kernel/                            # Kernel configuration (kernel.yaml, settings.yaml)
├── model/                             # LLM model configuration (model.yaml, model.json)
├── logging/                           # Logging configuration (manager.yaml)
├── agent/                             # Agent registry (registry.yaml — 12 agents)
├── skill/                             # Skill registry (registry.yaml — 10 skills)
├── service/                           # Daemon configuration (tool_d/tool.yaml)
├── configs/                           # Deployment configuration templates
│   ├── agentrt.yaml                   # Unified AgentRT runtime configuration (v0.1.1)
│   └── env.example                    # Environment variable template
├── environment/                       # Environment overlays (development / staging / production)
├── deployment/                        # Deployment configuration (cupolas, manager_management, example)
├── monitoring/                        # Observability (alerts, dashboards, otel-collector)
├── audit/                             # Audit log samples (sample_audit_log.json)
├── tools/                             # Operations toolset (drift_detector, config_diff, ...)
├── benchmark/                         # Performance benchmarks (benchmark_manager.py)
├── tests/                             # Test suite
├── .github/workflows/ci.yml           # CI pipeline
├── .gitignore
└── README.md                          # This file
```

## Core Components

### 1. Skill Management (`skill/`)

`skill/registry.yaml` is the authoritative registry of every skill available to the runtime. Each entry declares `skill_id`, version, `unit_type` (`file` / `shell` / `api` / `code` / `db` / `browser` / `tool`), required permissions, dependencies, compatibility (min/max AgentRT version, platforms), resource limits and rate limits. 10 builtin skills are registered: `filesystem_skill`, `shell_skill`, `http_skill`, `python_skill`, `javascript_skill`, `database_skill`, `browser_skill`, `git_skill`, `vector_search_skill`, `log_analysis_skill`. Validated against `schema/skill-registry.schema.json`.

### 2. Agent Management (`agent/`)

`agent/registry.yaml` registers 12 agents across roles (product_manager, architect, frontend, backend, tester, devops, security, data_engineer, coordinator, reviewer, analyst, plus a custom template). Each agent entry is a full contract: capabilities (with input/output JSON Schema, token estimates, success rate), a dual-system model configuration (System 1 for fast response, System 2 for deep reasoning), `required_permissions`, `cost_profile`, `trust_metrics` and `resource_limits`. Validated against `schema/agent-registry.schema.json`; contract paths point at `ecosystem/agents/airymax_agents/*/contract.json`.

### 3. Environment Management (`environment/`)

Three overlay files — `development.yaml`, `staging.yaml`, `production.yaml` — provide per-environment overrides (log level, Redis address, session timeout, etc.) merged on top of the base configuration. A higher-priority layer overrides keys of the same name in lower-priority layers:

| Layer | Priority | Description | Example |
|-------|----------|-------------|---------|
| **Base** | Low | Infrastructure config shared by all environments | Log paths, data dirs, default ports |
| **Environment** | Medium | Per-environment overrides (`development` / `staging` / `production`) | Log level, Redis address, session timeout |
| **Runtime** | High | Runtime dynamic config, supports hot reload | Rate limit, feature flags, model parameters |

### 4. Schema Validation (`schema/`)

11 JSON Schema files (~272 validation rules) covering every configuration domain — kernel, model, security, sanitizer, logging, agent/skill registries, tool service, audit log and manager self-management. Every config file references its schema via the `_schema` key and is rejected unless it validates.

### 5. Sanitizer (`sanitizer/`)

Two responsibilities: (a) build-time suppression files (`lsan-suppressions`, `valgrind-suppressions`) that silence known third-party false positives during AddressSanitizer / LeakSanitizer / Valgrind runs; (b) runtime input-sanitization rules (`sanitizer_rules.json`) covering 7 attack categories (XSS, SQL injection, prompt injection, PII, path traversal, command injection, SSRF). Co-owned with the Cupolas security module under a dual-responsibility model.

### 6. Unified Runtime Config (`configs/agentrt.yaml`)

The v0.1.1 unified AgentRT runtime configuration covering: `kernel` (IPC, scheduler, memory, timer, error), `llm` (runtime policy: cost-aware routing fallback chain, daily budget, cache; provider/model definitions consolidated to `model/model.yaml` as the single source), `memory` (L1–L4 layered memory), `security` (Cupolas, sandbox, RBAC, audit), `multi_agent` (A2A, collaboration patterns, lanes), `gateway` (HTTP, WebSocket, MCP, A2A, OpenAI-compat), `hooks`, `plugins` and `observability` (metrics, tracing, logging, health).

> **LLM config SSoT (0.1.1 consolidation)**: the `llm` section in `agentrt.yaml` keeps only **runtime policy** (routing fallback_chain / cost_budget / cache); `providers` and `models` definitions live in [`model/model.yaml`](model/README.md) (kept in sync with `model.json`) as the **single source of truth**, loaded by `llm_d` via `-c <config>`. Model and policy are separated to avoid dual-source drift.

### 7. Operations Toolset (`tools/`)

`drift_detector.py` (baseline + drift detection with `--fail-on-drift` CI mode), `config_diff.py` (snapshot diffing), `config_version_cleanup.py` (version history pruning), `audit_log_generator.py` (sample audit entries) and `schema_diff.py` (schema evolution diffing).

## Upstream Dependencies

**None — `manager/` is the configuration root.** It does not depend on any other Airymax repository at runtime; it is the layer every other component reads from. It only consumes standard tooling:

| Dependency | Purpose |
|------------|---------|
| Python ≥ 3.10 | Scripting runtime for tools, benchmark and tests |
| `jsonschema` | JSON Schema validation engine |
| `PyYAML` | YAML configuration parsing |
| `pytest` | Test framework |
| Valgrind / LeakSanitizer / AddressSanitizer | Memory tooling driven by the suppression files |

## Downstream Consumers

| Consumer | How it uses `manager/` |
|----------|------------------------|
| **AgentRT runtime** | Reads `configs/agentrt.yaml` and environment overlays at startup; loads `security/`, `kernel/`, `model/`, `logging/` settings at runtime |
| **AgentRT build toolchain** | Uses `sanitizer/lsan-suppressions` and `sanitizer/valgrind-suppressions` at **build / test time** to silence known third-party false positives |
| **Cupolas security module** | Co-owns `sanitizer/` and `security/` content under the dual-responsibility model; consumes `security/policy.yaml` (runtime tool ACL template is in tools/scripts/ops/templates, SSoT) |
| **tool_d daemon** | Reads `service/tool_d/tool.yaml` (validated by `tool-service.schema.json`) |
| **Agent & skill registries** | Runtime resolves agents/skills from `agent/registry.yaml` and `skill/registry.yaml`; agent contract paths point into `ecosystem/agents/airymax_agents/` |
| **CI / CD pipelines** | Run `tools/drift_detector.py` and `tools/config_diff.py` as configuration validation gates |
| **Operators** | Use `deployment/` and `monitoring/` templates for production rollouts |

## Usage / Quick Start

### Configuration validation

```bash
# Validate a configuration file against its schema
python -c "
import json, yaml
from jsonschema import validate
schema = json.load(open('schema/kernel-settings.schema.json'))
config = yaml.safe_load(open('kernel/settings.yaml'))
validate(instance=config, schema=schema)
"
```

### Operations toolset

```bash
# Configuration drift detection (create baseline + detect in one pass)
python tools/src/drift_detector.py --action both --output drift_report.json

# CI/CD mode — returns non-zero exit code when drift is detected
python tools/src/drift_detector.py --action detect --fail-on-drift

# Diff two configuration snapshots
python tools/src/config_diff.py config_v1.json config_v2.json

# Clean up version history (keep the 10 most recent)
python tools/src/config_version_cleanup.py --max-versions 10

# Generate sample audit log entries
python tools/src/audit_log_generator.py --count 10 --output audit.json

# Run performance benchmarks
python benchmark/benchmark_manager.py --iterations 1000
```

### Sanitizer suppressions (build time)

```bash
# LeakSanitizer with suppressions
LSAN_OPTIONS=suppressions=sanitizer/lsan-suppressions ./build/agentrt

# Valgrind with suppressions
valgrind --suppressions=sanitizer/valgrind-suppressions ./build/agentrt
```

### Environment overlays

```bash
# Pick an environment overlay (development / staging / production)
# then merge it on top of the base configuration before starting the runtime.
cp configs/env.example .env
# edit .env, set AGENTOS_ENV=production
```

## Build

`manager/` ships Python tooling and tests rather than a compiled artifact. Install the runtime dependencies and run the test suite:

```bash
# Runtime dependencies for tooling / validation
pip install jsonschema pyyaml pytest

# Run the operations toolset test suite
python -m pytest tests/ -v

# Run the schema coverage / diff tools
python tools/src/schema_diff.py --help
```

CI is defined in `.github/workflows/ci.yml` and runs schema validation, drift detection and the test suite on every push.

## Branch Strategy

This leaf repository is on the **`feature/official-hubs-01`** branch (active development). The management repository that aggregates it stays on `main`.

## License

Dual-licensed under **AGPL v3 + Apache 2.0** (SPDX: `AGPL-3.0-or-later OR Apache-2.0`). See [LICENSE](LICENSE) for the full text.

Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved.

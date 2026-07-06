# Manager — Ecosystem Manager (Config / Deployment / Schema / Sanitizer)

> Unified configuration, schema, sanitizer and deployment management center for the Airymax platform.
> A leaf repository under the [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem).

**Language:** English | [简体中文](README_zh.md)

[![Version](https://img.shields.io/badge/version-0.1.1-5a6b7e)](https://atomgit.com/openairymax/manager)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-feature%2Fofficial--hubs--01-6f7b8e)](https://atomgit.com/openairymax/manager)

---

## Module Positioning

`ecosystem/manager/` is the **unified configuration and lifecycle management center** of the Airymax AI Agent Runtime Platform. It owns the single source of truth for every configuration consumed by the AgentRT runtime, the build toolchain, and the surrounding observability stack.

The repository is organized around four responsibilities:

| Responsibility | Directory | Purpose |
|----------------|-----------|---------|
| **Sanitizer** | `sanitizer/` | ASan / LSan / Valgrind suppression files + input sanitization rules (XSS, SQLi, prompt injection, PII, …) |
| **Schema** | `schema/` | 11 JSON Schema files (~272 validation rules) covering every configuration domain |
| **Security** | `security/` | Security policies, RBAC permission rules, sandbox and audit configuration |
| **Configs** | `configs/`, `kernel/`, `model/`, `environment/`, `deployment/`, `monitoring/`, … | Deployment configuration templates, environment overlays and runtime settings |

It is **schema-driven**: every YAML / JSON file is validated against a JSON Schema before it is allowed to take effect, and every change is captured in an auditable audit log.

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
│   ├── policy.yaml                    # Default policy, sandbox, audit, intrusion detection
│   └── permission_rules.yaml          # Fine-grained RBAC rules
├── kernel/                            # Kernel configuration
│   ├── kernel.yaml
│   └── settings.yaml
├── model/                             # LLM model configuration
│   ├── model.yaml
│   └── model.json
├── logging/                           # Logging configuration
│   └── manager.yaml
├── agent/                             # Agent registry
│   └── registry.yaml
├── skill/                             # Skill registry
│   └── registry.yaml
├── service/                           # Daemon configuration
│   └── tool_d/tool.yaml               # tool_d configuration
├── configs/                           # Deployment configuration templates
│   ├── agentrt.yaml                   # Unified AgentRT runtime configuration (v0.1.1)
│   └── env.example                    # Environment variable template
├── environment/                       # Environment overlays
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
├── deployment/                        # Deployment configuration
│   ├── cupolas/environments.yaml      # Cupolas environment configuration
│   ├── manager_management.yaml        # Manager self-management configuration
│   └── example.yaml
├── monitoring/                        # Observability configuration
│   ├── alerts/cupolas-alerts.yml      # Cupolas alerting rules
│   ├── dashboards/cupolas-dashboard.json
│   └── otel-collector-manager.yaml    # OpenTelemetry Collector pipeline
├── audit/                             # Audit log samples
│   └── sample_audit_log.json
├── tools/                             # Operations toolset
│   ├── src/
│   │   ├── config_diff.py             # Configuration diff
│   │   ├── config_version_cleanup.py  # Version history cleanup
│   │   ├── drift_detector.py          # Configuration drift detection
│   │   ├── audit_log_generator.py     # Audit log generator
│   │   └── schema_diff.py             # Schema diff
│   └── base/                          # Shared utilities
├── benchmark/                         # Performance benchmarks
│   └── benchmark_manager.py
├── tests/                             # Test suite
├── .github/workflows/ci.yml           # CI pipeline
├── .gitignore
└── README.md                          # This file
```

## Configuration Architecture

```
+-------------------------------------------------------------------+
|        Configuration sources (files / env vars / API)             |
+-------------------------------------------------------------------+
|                      Manager configuration engine                  |
|  +-------------+   +-------------+   +-------------+              |
|  | Base config |   | Environment |   |  Runtime    |              |
|  | (infra)     |   | (env diff)  |   | (dynamic)   |              |
|  +------+------|   +------+------+   +------+------+              |
|         \____________|________|____________/                      |
|                      v                                            |
|  +-----------------------------------------------------------+    |
|  |             Merged configuration (runtime effective)      |    |
|  +-----------------------------------------------------------+    |
|                      |                                            |
|  +-----------------------------------------------------------+    |
|  |       JSON Schema validation engine                       |    |
|  |       11 schemas · ~272 validation rules                  |    |
|  +-----------------------------------------------------------+    |
+-------------------------------------------------------------------+
|        Semantic validation  →  Audit log  →  Distribution         |
+-------------------------------------------------------------------+
```

### Configuration Layers

| Layer | Priority | Description | Example |
|-------|----------|-------------|---------|
| **Base** | Low | Infrastructure configuration shared by all environments | Log paths, data dirs, default ports |
| **Environment** | Medium | Per-environment overrides (`development` / `staging` / `production`) | Log level, Redis address, session timeout |
| **Runtime** | High | Runtime dynamic configuration, supports hot reload | Rate limit, feature flags, model parameters |

A higher-priority layer overrides keys of the same name in lower-priority layers.

## Upstream / Downstream Dependencies

### Upstream

**None.** `manager/` is an independent configuration layer that does not depend on any other Airymax repository at runtime. It only consumes standard tooling:

| Dependency | Purpose |
|------------|---------|
| Python ≥ 3.10 | Scripting runtime for tools and tests |
| `jsonschema` | JSON Schema validation |
| `PyYAML` | YAML configuration parsing |
| `pytest` | Test framework |
| Valgrind / LeakSanitizer / AddressSanitizer | Memory tooling driven by the suppression files |

### Downstream

| Consumer | How it uses `manager/` |
|----------|------------------------|
| **AgentRT runtime** | Reads `configs/agentrt.yaml` and environment overlays at startup; loads `security/`, `kernel/`, `model/`, `logging/` settings at runtime |
| **AgentRT build toolchain** | Uses `sanitizer/lsan-suppressions` and `sanitizer/valgrind-suppressions` at **build / test time** to silence known third-party false positives |
| **Cupolas security module** | Owns the content responsibility for `sanitizer/` and `security/` (dual-responsibility model); consumes `security/policy.yaml` |
| **tool_d daemon** | Reads `service/tool_d/tool.yaml` |
| **CI / CD pipelines** | Runs `tools/drift_detector.py` and `tools/config_diff.py` for configuration validation gates |
| **Operators** | Use `deployment/` and `monitoring/` templates for production rollouts |

## Usage

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
python tools/src/config_version_cleanup.py --keep 10

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

## Schema Coverage

| Domain | Schema file | Config file |
|--------|-------------|-------------|
| Schema metadata | `_metadata.schema.json` | — |
| Audit log | `config-audit-log.schema.json` | `audit/sample_audit_log.json` |
| Kernel | `kernel-settings.schema.json` | `kernel/settings.yaml` |
| Model | `model.schema.json` | `model/model.yaml` |
| Security | `security-policy.schema.json` | `security/policy.yaml` |
| Sanitizer | `sanitizer-rules.schema.json` | `sanitizer/sanitizer_rules.json` |
| Logging | `logging.schema.json` | `logging/manager.yaml` |
| Agent registry | `agent-registry.schema.json` | `agent/registry.yaml` |
| Skill registry | `skill-registry.schema.json` | `skill/registry.yaml` |
| Tool service | `tool-service.schema.json` | `service/tool_d/tool.yaml` |
| Manager self-management | `config-management.schema.json` | `deployment/manager_management.yaml` |

## Branch Strategy

This leaf repository is on the **`feature/official-hubs-01`** branch (active development). The management repository that aggregates it stays on `main`.

## License

Dual-licensed under **AGPL v3 + Apache 2.0** (SPDX: `AGPL-3.0-or-later OR Apache-2.0`). See [LICENSE](LICENSE) for the full text.

Copyright (c) 2025-2026 **SPHARX Ltd.** All Rights Reserved.

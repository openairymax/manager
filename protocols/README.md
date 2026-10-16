# Protocol Vendor Manifests — L3 Policy Injection Surface

> Vendor / framework policy data for the AgentRT protocol layer. Mechanism
> lives in `agentrt/protocols/core`; this directory only describes policy.
> Data surface of the [manager](../) ecosystem repository.

**Language:** English | [简体中文](README_zh.md)

---

## Overview

This directory is the **L3 policy injection surface** of the AgentRT protocol
layer: JSON manifests that describe external protocol vendors and agent
frameworks. The **mechanism** — transport implementations, the JSON-RPC
codec skeleton, retry / backoff / heartbeat / reconnect state machines, and
the protocol registry — is uniquely implemented in
`agentrt/protocols/core`. The manifests here carry **policy only**; they are
loaded at startup and feed the registry as self-registration data sources.

**Inclusion criterion** (enforced during review): a field enters a manifest
only if changing it changes product behavior semantics. Pure implementation
constants — log tags, error-code bases, hash constants, buffer / chunk
sizes, socket-semantic macros — stay in the mechanism, never here.

## Files

```
protocols/
├── README.md               # This file (English)
├── README_zh.md            # Chinese version
└── vendors/
    ├── _schema.json        # JSON Schema (draft 2020-12) — manifest contract
    ├── jsonrpc.json        # JSON-RPC 2.0        (core)
    ├── mcp.json            # MCP v1.0.0          (standard)
    ├── a2a.json            # A2A v0.3.0          (standard)
    ├── agntcy.json         # AGNTCY v0.1.0       (standard)
    ├── openai.json         # OpenAI v1.0         (integration)
    ├── claude.json         # Claude v1.0.0       (integration)
    ├── china_eco.json      # China ecosystem v0.1.0 (integration)
    ├── openclaw.json       # OpenClaw v1.0.0     (integration)
    ├── openjiuwen.json     # OpenJiuwen v0.1.0   (integration)
    ├── autogen.json        # AutoGen v1.0.0      (framework)
    └── langchain.json      # LangChain v1.0.0    (framework)
```

`kind` maps 1:1 to `proto_category_t` in the mechanism core:
`core` → built-in wire contract; `standard` → open industry protocols
(MCP / A2A / AGNTCY); `integration` → vendor HTTP APIs; `framework` →
agent frameworks.

## Manifest Anatomy

Every manifest validates against `vendors/_schema.json`
(`manifest_version` is currently `1`):

| Block | Required | Purpose |
|-------|----------|---------|
| `manifest_version` | yes | Schema contract version (const `1`) |
| `id` | yes | Unique identifier (`^[a-z][a-z0-9_]*$`) |
| `kind` | yes | `core` \| `standard` \| `integration` \| `framework` |
| `protocol` | yes | Wire identity: `name`, `version`, optional `aliases` |
| `registry` | no | Built-in registry metadata (name, description, category, type, `capabilities[]`) — present only for vendors pre-registered by agentrt |
| `interface` | no | RPC surface: `methods[]`, `invoke` (`style`, `path`, `version`) |
| `transport` | no | Transport policy: `kind` (`stdio` \| …), endpoint and connection parameters |

## Governance

- **Adding a vendor**: add one manifest under `vendors/`; it must pass
  `_schema.json` validation. No mechanism code changes are required unless
  a new transport `kind` is introduced.
- **Changing a field**: if the change alters behavior semantics, bump
  `manifest_version` only when the schema contract itself changes — vendor
  data changes do not bump it.
- **Validation**: manifests are schema-validated before being loaded by
  the agentrt registry; invalid manifests are rejected fail-closed.

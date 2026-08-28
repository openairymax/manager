# Manager — 生态管理器（技能 / Agent / 环境生命周期与配置）

> Airymax 平台的统一配置、Schema、Sanitizer 与部署管理中心。
> 隶属于 [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem) 的叶子仓。

**语言:** [English](README.md) | 简体中文

[![Version](https://img.shields.io/badge/version-0.1.1-5a6b7e)](https://atomgit.com/openairymax/manager)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-feature%2Fofficial--hubs--01-6f7b8e)](https://atomgit.com/openairymax/manager)

**仓库:** `git@atomgit.com:openairymax/manager.git` · **分支:** `feature/official-hubs-01`

---

## 概述

`ecosystem/manager/` 是 Airymax AI Agent 运行时平台的**统一配置与生命周期管理中心**，是 AgentRT 运行时、构建工具链、可观测性体系以及各守护进程所消费的全部配置的唯一真相源（Single Source of Truth）。本仓承担三项核心管理职责——**技能管理**、**Agent 管理**与**环境管理**——同时负责 Schema 校验、Sanitizer 抑制、安全策略与部署模板。

整个模块采用 **Schema 驱动**：任何 YAML / JSON 配置生效前必须通过 JSON Schema 校验，所有变更均记录在审计日志中。本仓维护 `skill/registry.yaml`（10 个注册技能）、`agent/registry.yaml`（12 个注册 Agent，含能力定义、双系统模型、RBAC 权限、成本画像与信任指标）以及 `environment/{development,staging,production}.yaml` 覆盖层，这些覆盖层合并到基础配置 `configs/agentrt.yaml`（v0.1.1）之上。

在生态层中，`manager/` 处于基础位置：**不依赖任何上游 Airymax 仓**（它是配置根），下游被 AgentRT 运行时、构建工具链、Cupolas 安全模块、`tool_d` 守护进程、CI/CD 流水线与运维人员消费。正是它让生态中的其他组件可复现、可校验、可审计。

## 目录结构

```
manager/
├── schema/                            # JSON Schema 定义（11 个文件，约 272 条规则）
│   ├── _metadata.schema.json          # Schema 元数据与版本
│   ├── agent-registry.schema.json     # Agent 注册表
│   ├── config-audit-log.schema.json   # 配置审计日志
│   ├── config-management.schema.json  # Manager 自身管理
│   ├── kernel-settings.schema.json    # 内核设置
│   ├── logging.schema.json            # 日志配置
│   ├── model.schema.json              # 模型配置
│   ├── sanitizer-rules.schema.json    # Sanitizer 规则
│   ├── security-policy.schema.json    # 安全策略
│   ├── skill-registry.schema.json     # 技能注册表
│   └── tool-service.schema.json       # tool_d 服务
├── sanitizer/                         # Sanitizer 抑制 + 输入规则
│   ├── sanitizer_rules.json           # 8 大攻击类别的 26 条输入规则（默认启用 25 条）
│   ├── lsan-suppressions              # LeakSanitizer 抑制文件
│   └── valgrind-suppressions          # Valgrind 抑制文件
├── security/                          # 安全策略与 RBAC
│   └── policy.yaml                    # 默认策略、沙箱、审计、入侵检测
│                                      # （工具 ACL 运行时模板：tools/scripts/ops/templates）
├── kernel/                            # 内核配置（kernel.yaml、settings.yaml）
├── model/                             # LLM 模型配置（model.yaml、model.json）
├── logging/                           # 日志配置（manager.yaml）
├── agent/                             # Agent 注册表（registry.yaml — 12 个 Agent）
├── skill/                             # 技能注册表（registry.yaml — 10 个技能）
├── service/                           # 守护进程配置（tool_d/tool.yaml）
├── configs/                           # 部署配置模板
│   ├── agentrt.yaml                   # AgentRT 运行时统一配置（v0.1.1）
│   └── env.example                    # 环境变量模板
├── environment/                       # 环境覆盖层（development / staging / production）
├── deployment/                        # 部署配置（cupolas、manager_management、example）
├── monitoring/                        # 可观测性（alerts、dashboards、otel-collector）
├── audit/                             # 审计日志样例（sample_audit_log.json）
├── tools/                             # 运维工具集（drift_detector、config_diff 等）
├── benchmark/                         # 性能基准测试（benchmark_manager.py）
├── tests/                             # 测试套件
├── .github/workflows/ci.yml           # CI 流水线
├── .gitignore
└── README.md                          # 本文件
```

## 核心组件

### 1. 技能管理（`skill/`）

`skill/registry.yaml` 是运行时可用的全部技能的权威注册表。每个条目声明 `skill_id`、版本、`unit_type`（`file` / `shell` / `api` / `code` / `db` / `browser` / `tool`）、所需权限、依赖、兼容性（AgentRT 最低/最高版本、平台）、资源限制与速率限制。共注册 10 个内置技能：`filesystem_skill`、`shell_skill`、`http_skill`、`python_skill`、`javascript_skill`、`database_skill`、`browser_skill`、`git_skill`、`vector_search_skill`、`log_analysis_skill`。由 `schema/skill-registry.schema.json` 校验。

### 2. Agent 管理（`agent/`）

`agent/registry.yaml` 注册了 12 个 Agent，覆盖多种角色（product_manager、architect、frontend、backend、tester、devops、security、data_engineer、coordinator、reviewer、analyst，以及自定义模板）。每个 Agent 条目是一份完整契约：能力（含输入/输出 JSON Schema、Token 估算、成功率）、双系统模型配置（System 1 快速响应、System 2 深度推理）、`required_permissions`、`cost_profile`、`trust_metrics` 与 `resource_limits`。由 `schema/agent-registry.schema.json` 校验，契约路径指向 `ecosystem/agents/airymax_agents/*/contract.json`。

### 3. 环境管理（`environment/`）

三套覆盖文件——`development.yaml`、`staging.yaml`、`production.yaml`——提供按环境的覆盖（日志级别、Redis 地址、会话超时等），合并到基础配置之上。高优先级层覆盖低优先级层中的同名键：

| 层 | 优先级 | 说明 | 示例 |
|----|--------|------|------|
| **Base** | 低 | 基础设施配置，所有环境共享 | 日志路径、数据目录、默认端口 |
| **Environment** | 中 | 按环境覆盖（`development` / `staging` / `production`） | 日志级别、Redis 地址、会话超时 |
| **Runtime** | 高 | 运行时动态配置，支持热重载 | 速率限制、功能开关、模型参数 |

### 4. Schema 校验（`schema/`）

11 个 JSON Schema 文件（约 272 项校验规则），覆盖所有配置领域——内核、模型、安全、Sanitizer、日志、Agent/技能注册表、工具服务、审计日志与 Manager 自身管理。每个配置文件通过 `_schema` 键引用其 Schema，未通过校验即被拒绝。

### 5. Sanitizer（`sanitizer/`）

两项职责：(a) 构建期抑制文件（`lsan-suppressions`、`valgrind-suppressions`），在 AddressSanitizer / LeakSanitizer / Valgrind 运行期间静默第三方已知误报；(b) 运行时输入安全检测规则（`sanitizer_rules.json`），覆盖 7 大攻击类别（XSS、SQL 注入、提示注入、PII、路径穿越、命令注入、SSRF）。按双重责任模型与 Cupolas 安全模块共同拥有。

### 6. 统一运行时配置（`configs/agentrt.yaml`）

v0.1.1 的 AgentRT 统一运行时配置，覆盖：`kernel`（IPC、调度器、内存、定时器、错误）、`llm`（运行时策略：成本感知路由 fallback 链、日预算、缓存；提供商与模型定义收敛至 `model/model.yaml` 单一来源）、`memory`（L1–L4 分层记忆）、`security`（Cupolas、沙箱、RBAC、审计）、`multi_agent`（A2A、协作模式、lanes）、`gateway`（HTTP、WebSocket、MCP、A2A、OpenAI 兼容）、`hooks`、`plugins` 与 `observability`（指标、链路追踪、日志、健康检查）。

> **LLM 配置 SSoT（0.1.1 收敛）**：`agentrt.yaml` 的 `llm` 段仅保留**运行时策略**（routing fallback_chain / cost_budget / cache）；`providers` 与 `models` 定义以 [`model/model.yaml`](model/README.md)（同源 `model.json`）为**唯一真相源**，由 `llm_d` 经 `-c <config>` 加载。模型与策略分离，避免双源漂移。

### 7. 运维工具集（`tools/`）

`drift_detector.py`（基线 + 漂移检测，含 `--fail-on-drift` CI 模式）、`config_diff.py`（快照差异对比）、`config_version_cleanup.py`（版本历史清理）、`audit_log_generator.py`（审计样例生成）与 `schema_diff.py`（Schema 演进对比）。

## 上游依赖

**无——`manager/` 是配置根。** 运行时不依赖任何其他 Airymax 仓，它是其他组件读取的层。仅消费标准工具链：

| 依赖 | 用途 |
|------|------|
| Python ≥ 3.10 | 工具、基准与测试的脚本运行环境 |
| `jsonschema` | JSON Schema 校验引擎 |
| `PyYAML` | YAML 配置解析 |
| `pytest` | 测试框架 |
| Valgrind / LeakSanitizer / AddressSanitizer | 由抑制文件驱动的内存检测工具 |

## 下游消费方

| 消费方 | 使用方式 |
|--------|----------|
| **AgentRT 运行时** | 启动时读取 `configs/agentrt.yaml` 及环境覆盖层；运行时加载 `security/`、`kernel/`、`model/`、`logging/` 配置 |
| **AgentRT 构建工具链** | **构建 / 测试期**使用 `sanitizer/lsan-suppressions` 与 `sanitizer/valgrind-suppressions` 抑制第三方库已知误报 |
| **Cupolas 安全模块** | 按双重责任模型共有 `sanitizer/` 与 `security/` 内容；消费 `security/policy.yaml`（运行时工具 ACL 模板在 tools/scripts/ops/templates，SSoT） |
| **tool_d 守护进程** | 读取 `service/tool_d/tool.yaml`（由 `tool-service.schema.json` 校验） |
| **Agent 与技能注册表** | 运行时从 `agent/registry.yaml` 与 `skill/registry.yaml` 解析；Agent 契约路径指向 `ecosystem/agents/airymax_agents/` |
| **CI / CD 流水线** | 运行 `tools/drift_detector.py` 与 `tools/config_diff.py` 作为配置校验门禁 |
| **运维人员** | 使用 `deployment/` 与 `monitoring/` 模板进行生产部署 |

## 使用说明 / 快速开始

### 配置校验

```bash
# 用 Schema 校验配置文件
python -c "
import json, yaml
from jsonschema import validate
schema = json.load(open('schema/kernel-settings.schema.json'))
config = yaml.safe_load(open('kernel/settings.yaml'))
validate(instance=config, schema=schema)
"
```

### 运维工具集

```bash
# 配置漂移检测（一键执行：建基线 + 检测）
python tools/src/drift_detector.py --action both --output drift_report.json

# CI/CD 模式 — 检测到漂移时返回非零退出码
python tools/src/drift_detector.py --action detect --fail-on-drift

# 对比两份配置快照
python tools/src/config_diff.py config_v1.json config_v2.json

# 清理版本历史（保留最近 10 个版本）
python tools/src/config_version_cleanup.py --max-versions 10

# 生成审计日志样例
python tools/src/audit_log_generator.py --count 10 --output audit.json

# 运行性能基准测试
python benchmark/benchmark_manager.py --iterations 1000
```

### Sanitizer 抑制（构建期）

```bash
# 使用抑制文件运行 LeakSanitizer
LSAN_OPTIONS=suppressions=sanitizer/lsan-suppressions ./build/agentrt

# 使用抑制文件运行 Valgrind
valgrind --suppressions=sanitizer/valgrind-suppressions ./build/agentrt
```

### 环境覆盖

```bash
# 选择一个环境覆盖层（development / staging / production）
# 启动运行时前将其合并到基础配置之上
cp configs/env.example .env
# 编辑 .env，设置 AGENTOS_ENV=production
```

## 构建

`manager/` 提供的是 Python 工具与测试，而非编译产物。安装运行时依赖并运行测试套件：

```bash
# 工具 / 校验的运行时依赖
pip install jsonschema pyyaml pytest

# 运维工具集测试套件
python -m pytest tests/ -v

# 运行 Schema 覆盖 / 差异工具
python tools/src/schema_diff.py --help
```

CI 定义在 `.github/workflows/ci.yml`，每次推送时运行 Schema 校验、漂移检测与测试套件。

## 分支策略

本叶子仓位于 **`feature/official-hubs-01`** 分支（活跃开发）。聚合它的管理仓保持在 `main`。

## 许可证

采用 **AGPL v3 + Apache 2.0** 双许可证（SPDX: `AGPL-3.0-or-later OR Apache-2.0`）。详见 [LICENSE](LICENSE)。

Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved.

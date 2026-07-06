# Manager — 生态管理器（配置 / 部署 / Schema / Sanitizer）

> Airymax 平台的统一配置、Schema、Sanitizer 与部署管理中心。
> 隶属于 [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem) 的叶子仓。

**语言:** [English](README.md) | 简体中文

[![Version](https://img.shields.io/badge/version-0.1.1-5a6b7e)](https://atomgit.com/openairymax/manager)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-feature%2Fofficial--hubs--01-6f7b8e)](https://atomgit.com/openairymax/manager)

---

## 模块定位

`ecosystem/manager/` 是 Airymax AI Agent 运行时平台的**统一配置与生命周期管理中心**，是 AgentRT 运行时、构建工具链以及可观测性体系所消费的全部配置的唯一真相源（Single Source of Truth）。

本仓围绕四项职责组织：

| 职责 | 目录 | 用途 |
|------|------|------|
| **Sanitizer** | `sanitizer/` | ASan / LSan / Valgrind 抑制文件 + 输入安全检测规则（XSS、SQL 注入、提示注入、PII 等） |
| **Schema** | `schema/` | 11 个 JSON Schema 文件（约 272 项校验规则），覆盖所有配置领域 |
| **Security** | `security/` | 安全策略、RBAC 权限规则、沙箱与审计配置 |
| **Configs** | `configs/`、`kernel/`、`model/`、`environment/`、`deployment/`、`monitoring/` 等 | 部署配置模板、环境覆盖与运行时设置 |

整个模块采用 **Schema 驱动**：任何 YAML / JSON 配置生效前必须通过 JSON Schema 校验，所有变更均记录在审计日志中。

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
│   ├── sanitizer_rules.json           # 7 大攻击类别的 25 条输入规则
│   ├── lsan-suppressions              # LeakSanitizer 抑制文件
│   └── valgrind-suppressions          # Valgrind 抑制文件
├── security/                          # 安全策略与 RBAC
│   ├── policy.yaml                    # 默认策略、沙箱、审计、入侵检测
│   └── permission_rules.yaml          # 细粒度 RBAC 规则
├── kernel/                            # 内核配置
│   ├── kernel.yaml
│   └── settings.yaml
├── model/                             # LLM 模型配置
│   ├── model.yaml
│   └── model.json
├── logging/                           # 日志配置
│   └── manager.yaml
├── agent/                             # Agent 注册表
│   └── registry.yaml
├── skill/                             # 技能注册表
│   └── registry.yaml
├── service/                           # 守护进程配置
│   └── tool_d/tool.yaml               # tool_d 配置
├── configs/                           # 部署配置模板
│   ├── agentrt.yaml                   # AgentRT 运行时统一配置（v0.1.1）
│   └── env.example                    # 环境变量模板
├── environment/                       # 环境覆盖层
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
├── deployment/                        # 部署配置
│   ├── cupolas/environments.yaml      # Cupolas 环境配置
│   ├── manager_management.yaml        # Manager 自身管理配置
│   └── example.yaml
├── monitoring/                        # 可观测性配置
│   ├── alerts/cupolas-alerts.yml      # Cupolas 告警规则
│   ├── dashboards/cupolas-dashboard.json
│   └── otel-collector-manager.yaml    # OpenTelemetry Collector 流水线
├── audit/                             # 审计日志样例
│   └── sample_audit_log.json
├── tools/                             # 运维工具集
│   ├── src/
│   │   ├── config_diff.py             # 配置差异对比
│   │   ├── config_version_cleanup.py  # 版本历史清理
│   │   ├── drift_detector.py          # 配置漂移检测
│   │   ├── audit_log_generator.py     # 审计日志生成器
│   │   └── schema_diff.py             # Schema 差异对比
│   └── base/                          # 公共工具库
├── benchmark/                         # 性能基准测试
│   └── benchmark_manager.py
├── tests/                             # 测试套件
├── .github/workflows/ci.yml           # CI 流水线
├── .gitignore
└── README.md                          # 本文件
```

## 配置架构

```
+-------------------------------------------------------------------+
|              配置来源（文件 / 环境变量 / API）                       |
+-------------------------------------------------------------------+
|                       Manager 配置引擎                              |
|  +-------------+   +-------------+   +-------------+              |
|  | Base 配置   |   | 环境配置    |   | 运行时配置  |              |
|  | (基础设施)  |   | (环境差异)  |   | (动态调整)  |              |
|  +------+------+   +------+------+   +------+------+              |
|         \____________|________|____________/                      |
|                      v                                            |
|  +-----------------------------------------------------------+    |
|  |             合并配置（运行时生效）                          |    |
|  +-----------------------------------------------------------+    |
|                      |                                            |
|  +-----------------------------------------------------------+    |
|  |       JSON Schema 校验引擎                                 |    |
|  |       11 个 Schema · 约 272 项校验规则                     |    |
|  +-----------------------------------------------------------+    |
+-------------------------------------------------------------------+
|              语义校验  →  审计日志  →  配置分发                    |
+-------------------------------------------------------------------+
```

### 配置分层

| 层 | 优先级 | 说明 | 示例 |
|----|--------|------|------|
| **Base** | 低 | 基础设施配置，所有环境共享 | 日志路径、数据目录、默认端口 |
| **Environment** | 中 | 按环境覆盖（`development` / `staging` / `production`） | 日志级别、Redis 地址、会话超时 |
| **Runtime** | 高 | 运行时动态配置，支持热重载 | 速率限制、功能开关、模型参数 |

高优先级层覆盖低优先级层中的同名键。

## 上游 / 下游依赖关系

### 上游

**无。** `manager/` 是独立的配置层，运行时不依赖任何其他 Airymax 仓。仅消费标准工具链：

| 依赖 | 用途 |
|------|------|
| Python ≥ 3.10 | 工具与测试的脚本运行环境 |
| `jsonschema` | JSON Schema 校验 |
| `PyYAML` | YAML 配置解析 |
| `pytest` | 测试框架 |
| Valgrind / LeakSanitizer / AddressSanitizer | 由抑制文件驱动的内存检测工具 |

### 下游

| 消费方 | 使用方式 |
|--------|----------|
| **AgentRT 运行时** | 启动时读取 `configs/agentrt.yaml` 及环境覆盖层；运行时加载 `security/`、`kernel/`、`model/`、`logging/` 配置 |
| **AgentRT 构建工具链** | **构建 / 测试期**使用 `sanitizer/lsan-suppressions` 和 `sanitizer/valgrind-suppressions` 抑制第三方库已知误报 |
| **Cupolas 安全模块** | 按双重责任模型拥有 `sanitizer/` 与 `security/` 的内容责任；消费 `security/policy.yaml` |
| **tool_d 守护进程** | 读取 `service/tool_d/tool.yaml` |
| **CI / CD 流水线** | 运行 `tools/drift_detector.py` 与 `tools/config_diff.py` 作为配置校验门禁 |
| **运维人员** | 使用 `deployment/` 与 `monitoring/` 模板进行生产部署 |

## 使用说明

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
python tools/src/config_version_cleanup.py --keep 10

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

## Schema 覆盖范围

| 领域 | Schema 文件 | 配置文件 |
|------|-------------|---------|
| Schema 元数据 | `_metadata.schema.json` | — |
| 审计日志 | `config-audit-log.schema.json` | `audit/sample_audit_log.json` |
| 内核 | `kernel-settings.schema.json` | `kernel/settings.yaml` |
| 模型 | `model.schema.json` | `model/model.yaml` |
| 安全 | `security-policy.schema.json` | `security/policy.yaml` |
| Sanitizer | `sanitizer-rules.schema.json` | `sanitizer/sanitizer_rules.json` |
| 日志 | `logging.schema.json` | `logging/manager.yaml` |
| Agent 注册表 | `agent-registry.schema.json` | `agent/registry.yaml` |
| 技能注册表 | `skill-registry.schema.json` | `skill/registry.yaml` |
| 工具服务 | `tool-service.schema.json` | `service/tool_d/tool.yaml` |
| Manager 自身管理 | `config-management.schema.json` | `deployment/manager_management.yaml` |

## 分支策略

本叶子仓位于 **`feature/official-hubs-01`** 分支（活跃开发）。聚合它的管理仓保持在 `main`。

## 许可证

采用 **AGPL v3 + Apache 2.0** 双许可证（SPDX: `AGPL-3.0-or-later OR Apache-2.0`）。详见 [LICENSE](LICENSE)。

Copyright (c) 2025-2026 **SPHARX Ltd.** All Rights Reserved.

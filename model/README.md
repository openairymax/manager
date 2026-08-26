# Manager Model — LLM 模型配置

**模块路径**: `ecosystem/manager/model/`
**版本**: v0.1.1

## 概述

`manager/model/` 包含 AgentRT 的 LLM 模型配置（v3.0.0 表格形式），以「模型连接表」统一抽象各提供商，不区分厂商。提供 YAML 和 JSON 两种格式，分别服务于人类可读编辑和守护进程程序化加载。配置遵循 `schema/model.schema.json` 规范。

> **SSoT（0.1.1）**：`model.yaml`（同源 `model.json`）是 AgentRT 的 **LLM 提供商与模型唯一真相源**。`configs/agentrt.yaml` 的 `llm` 段仅保留运行时策略（路由/成本/缓存），模型连接定义全部由此文件提供，由 `llm_d` / `think_d` 经 `-c <config>` 加载。

## 目录结构

```
model/
├── model.yaml       # 模型配置（YAML 格式，人类可读，含详细注释）
├── model.json       # 模型配置（JSON 格式，供 llm_d / think_d 程序化加载）
└── model.schema.json# （位于 ../schema/，配置格式校验）
```

## 核心组件

### model.yaml

YAML 格式的模型配置，包含详细注释，适合人工编辑。定义以下内容：

| 配置域 | 说明 |
|--------|------|
| **`models`** | 模型连接表（最多 3 个）：`name` / `mode`（api\|local）/ `api_format`（openai\|anthropic）/ `base_url` / `model_id` / `api_key_env` / `context_window` / `max_output` / `tool_rounds` / `vision` / `thinking` / `input_cost_per_1k` / `output_cost_per_1k` |
| **`default_model`** | 默认模型（须为 `models` 表中某一行的 `model_id`） |
| **`think`** | 双思考系统（Thinkdual / GRAD 批判循环）：`enabled`、三个思考角色的模型分配（`think2_slow_model` / `think1_fast_model` / `think1_prof_model`）、`timeout_ms` |

> v3 起移除旧的 `providers` / `global` / 超时重试 / 熔断器长清单，字段统一抽象：用户只需填写格式、地址、模型名与 key，即可接入任意厂商 API 或本地模型。

### model.json

JSON 格式的模型配置，与 `model.yaml` 包含相同数据（`models` / `default_model` / `think`），供守护进程 `llm_d` / `think_d` 程序化加载使用。

> 两个文件包含相同数据，服务于不同消费者：
> - `model.yaml` — 人类可读，含注释
> - `model.json` — 程序化加载，供守护进程使用

## 依赖关系

| 组件 | 用途 |
|------|------|
| `schema/model.schema.json` | 配置格式校验 |
| llm_d / think_d 守护进程 | JSON 格式配置消费者 |
| PyYAML | YAML 配置解析 |

---

© 2025-2026 SPHARX Ltd. All Rights Reserved.

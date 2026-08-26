# Manager Skill — 技能注册表配置

**模块路径**: `ecosystem/manager/skill/`
**版本**: v0.1.1

## 概述

`manager/skill/` 包含 AgentRT 的技能注册表配置，定义系统可用的技能列表及其参数。技能是 Agent 可调用的原子能力单元，注册表描述了每个技能的输入/输出规范、权限要求和资源消耗。配置遵循 `schema/skill-registry.schema.json` 规范。

## 目录结构

```
skill/
└── registry.yaml      # 技能注册表定义
```

## 核心组件

### registry.yaml

技能注册表，每个技能包含以下字段：

| 字段 | 说明 |
|------|------|
| `skill_id` | 技能唯一标识符 |
| `name` / `description` | 技能名称与描述 |
| `version` / `source` | 版本号与来源（builtin/custom） |
| `enabled` | 是否启用 |
| `unit_type` | 单元类型（file/shell/api/code/db/browser/tool） |
| `contract_path` | 技能契约 JSON 路径 |
| `permissions` | 执行所需权限 |
| `dependencies` | 依赖的其他技能（skill_id/version/optional） |
| `compatibility` | 兼容性（min/max AgentRT 版本、平台） |
| `resource_limits` | 资源限制（max_memory_mb/timeout_sec/max_file_size_mb） |
| `rate_limit` | 速率限制（max_calls_per_minute） |
| `tags` / `author` / `license` | 标签、作者与许可 |

### 内置技能列表

注册表共登记 10 个内置技能（`_metadata.total_skills: 10`）：

| skill_id | unit_type | 说明 |
|----------|-----------|------|
| `filesystem_skill` | file | 文件和目录的读写、创建、删除 |
| `shell_skill` | shell | 安全的 Shell 命令执行（沙箱隔离） |
| `http_skill` | api | HTTP/HTTPS 请求，REST API 调用 |
| `python_skill` | code | Python 代码安全执行 |
| `javascript_skill` | code | JavaScript/Node.js 代码安全执行 |
| `database_skill` | db | 数据库连接与 SQL 操作 |
| `browser_skill` | browser | 浏览器自动化与网页抓取 |
| `git_skill` | tool | Git 版本控制操作 |
| `vector_search_skill` | api | 向量相似度搜索与嵌入生成 |
| `log_analysis_skill` | tool | 日志解析、分析与异常检测 |

## 依赖关系

| 组件 | 用途 |
|------|------|
| `schema/skill-registry.schema.json` | 注册表格式校验 |
| PyYAML | YAML 配置解析 |

---

© 2025-2026 SPHARX Ltd. All Rights Reserved.

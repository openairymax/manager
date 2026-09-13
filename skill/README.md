# Manager Skill — 技能注册表配置

**模块路径**: `ecosystem/manager/skill/`
**版本**: v1.0.0（registry.yaml 配置版本）

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
| `version` / `source` | 版本号与来源（builtin/community/skills） |
| `enabled` | 是否启用 |
| `unit_type` | 单元类型（file/shell/api/code/db/browser/tool） |
| `contract_path` | 技能契约 JSON 路径 |
| `permissions` | 执行所需权限 |
| `dependencies` | 依赖的其他技能（skill_id/version/optional） |
| `compatibility` | 兼容性（min/max AgentRT 版本、平台） |
| `resource_limits` | 资源限制（max_memory_mb/timeout_sec/max_file_size_mb） |
| `rate_limit` | 速率限制（max_calls_per_minute） |
| `tags` / `author` / `license` | 标签、作者与许可 |

### 注册技能列表

注册表共登记 15 个技能（`_metadata.total_skills: 15`），按来源分为三类：
8 个内置技能（builtin）、2 个社区技能（community，默认禁用）、5 个源自
skills 叶子仓的官方技能（skills）。

| skill_id | unit_type | source | 说明 |
|----------|-----------|--------|------|
| `filesystem_skill` | file | builtin | 文件和目录的读写、创建、删除 |
| `shell_skill` | shell | builtin | 安全的 Shell 命令执行（沙箱隔离） |
| `http_skill` | api | builtin | HTTP/HTTPS 请求，REST API 调用 |
| `python_skill` | code | builtin | Python 代码安全执行 |
| `javascript_skill` | code | builtin | JavaScript/Node.js 代码安全执行 |
| `git_skill` | tool | builtin | Git 版本控制操作 |
| `vector_search_skill` | api | builtin | 向量相似度搜索与嵌入生成 |
| `log_analysis_skill` | tool | builtin | 日志解析、分析与异常检测 |
| `database_skill` | db | community | 数据库连接与 SQL 操作（默认禁用） |
| `browser_skill` | browser | community | 浏览器自动化与网页抓取（默认禁用） |
| `code_review` | skill | skills | 代码审查技能（skills 叶子仓） |
| `data_analysis` | skill | skills | 数据分析技能（skills 叶子仓） |
| `security_audit` | skill | skills | 安全审计技能（skills 叶子仓） |
| `text_summarization` | skill | skills | 文本摘要技能（skills 叶子仓） |
| `web_search` | skill | skills | 网页搜索技能（skills 叶子仓） |

## 依赖关系

| 组件 | 用途 |
|------|------|
| `schema/skill-registry.schema.json` | 注册表格式校验 |
| PyYAML | YAML 配置解析 |

---

© 2025-2026 SPHARX Ltd. All Rights Reserved.

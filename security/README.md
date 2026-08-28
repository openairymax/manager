# Manager Security — 安全策略与权限配置

**模块路径**: `ecosystem/manager/security/`
**版本**: v0.1.1

## 概述

`manager/security/` 包含 AgentRT 的安全策略和权限规则配置，定义系统的默认访问策略、细粒度权限规则、审计配置、沙箱隔离、入侵检测、密钥管理和会话安全。配置遵循 `schema/security-policy.schema.json` 规范，按双重责任模型归属 cupolas 模块。

## 目录结构

```
security/
├── policy.yaml              # 安全策略定义（默认策略 + 权限规则 + 沙箱 + 入侵检测）
└── README.md                # 模块说明（SSoT 边界见下）
```

## 核心组件

### policy.yaml

安全策略主配置文件，覆盖以下安全域：

| 安全域 | 关键配置 |
|--------|---------|
| **默认策略** | deny-by-default（默认拒绝所有访问） |
| **权限规则** | 文件系统/网络/代码执行/环境变量四类权限控制 |
| **审计规则** | 敏感操作审计、日志加密（AES-256-GCM）、告警 Webhook |
| **沙箱配置** | 隔离类型（docker/wasm/process/container/none）、资源限制、Seccomp/AppArmor |
| **入侵检测** | 异常检测阈值、阻止模式（提示注入/越狱）、行为分析 |
| **密钥管理** | 提供者选择（env/file/vault/aws_kms/azure_keyvault/gcp_kms）、静态加密、轮换周期 |
| **会话安全** | 超时控制、并发限制、JWT 令牌配置 |
| **热更新** | 安全策略支持热重载 |

#### 权限规则分类

| 类别 | 规则数 | 说明 |
|------|--------|------|
| 文件系统 | 6 | 临时目录读写、数据目录读写、/etc 写入拒绝、文件删除拒绝 |
| 网络 | 5 | OpenAI/Anthropic/DeepSeek API 允许、localhost 允许、其他出站拒绝 |
| 代码执行 | 3 | Python/JavaScript/Shell 沙箱执行 |
| 环境变量 | 5 | API Key 读取允许、AGENTRT_* 允许、其他拒绝 |

### 工具权限规则（SSoT 边界）

运行时工具级 ACL（tool_d/agent_d 加载的 `rules: [{agent, tool, effect}]`
格式）**不在此目录维护**——权威模板为 tools 仓
`scripts/ops/templates/permission_rules.yaml`（v1.1.0），经 install.sh 部署到
`$AIRY_HOME/config/cupolas/permission_rules.yaml`。本目录历史上的
`permission_rules.yaml`（v1.0.0，action/resource 旧格式）与运行时 schema
不兼容，已于 2026-08-28 删除，避免同名异格式误导。安全策略的治理入口为
本目录 `policy.yaml`。

## 依赖关系

| 组件 | 用途 |
|------|------|
| `schema/security-policy.schema.json` | 配置格式校验 |
| cupolas 模块 | 内容定义责任方 |
| `environment/` | 环境配置覆盖 |
| PyYAML | YAML 配置解析 |

---

© 2025-2026 SPHARX Ltd. All Rights Reserved.

# Manager Deployment — 部署环境配置

**模块路径**: `ecosystem/manager/deployment/`
**版本**: v0.1.1

## 概述

`manager/deployment/` 包含 AgentRT Manager 模块的部署环境配置，定义 Cupolas 子系统的多环境部署参数，包括各环境的资源限制、服务端点和监控配置。

## 目录结构

```
deployment/
├── cupolas/
│   └── environments.yaml   # Cupolas 多环境部署配置
├── example.yaml            # AgentRT 完整配置示例（快速启动/测试用）
└── manager_management.yaml # Manager 自管理配置（schema/config-management.schema.json）
```

## 核心组件

### cupolas/environments.yaml

Cupolas 子系统的多环境部署配置，定义不同部署环境下的参数差异：

- 各环境的资源分配与限制
- 服务端点与连接配置
- 监控与告警阈值
- 环境特定的安全策略

### example.yaml

AgentRT 完整配置示例文件，覆盖 kernel / model / security 等配置域，供快速启动与测试使用。

### manager_management.yaml

Manager 模块自身的管理配置（自管理），定义配置热更新（`hot_reload`：监听文件、支持热更新的配置项白名单、更新前后回调）、版本控制（git 后端）、回滚、启动/重载时校验、配置变更审计（加密存储）与导入导出等设置，遵循 `schema/config-management.schema.json` 规范。

## 依赖关系

| 组件 | 用途 |
|------|------|
| Cupolas 子系统 | 安全沙箱运行时 |
| `environment/` | 环境配置覆盖 |

---

© 2025-2026 SPHARX Ltd. All Rights Reserved.

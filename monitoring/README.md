# Manager Monitoring — 监控配置

**模块路径**: `ecosystem/manager/monitoring/`
**版本**: v0.1.1

## 概述

`manager/monitoring/` 包含 AgentRT Manager 模块的监控配置，提供 Cupolas 子系统的 CI/CD 质量门禁告警规则、Grafana 可视化仪表盘以及 OpenTelemetry Collector 采集配置，用于在构建 / 测试 / 发布流水线中实时监控质量与安全状态。

## 目录结构

```
monitoring/
├── alerts/                            # 告警规则
│   └── cupolas-alerts.yml             # Cupolas 子系统告警规则
├── dashboards/                        # 仪表盘
│   └── cupolas-dashboard.json         # Cupolas CI/CD 监控仪表盘
└── otel-collector-manager.yaml        # OpenTelemetry Collector 配置（OTLP gRPC/HTTP → logging）
```

## 核心组件

### alerts/cupolas-alerts.yml

Cupolas 子系统的 Prometheus 告警规则，共 15 条，覆盖：

- 构建 / 测试流水线质量门禁（构建失败、构建超时、构建成功率下降、测试失败、测试覆盖率下降）
- 安全事件（高危 / 严重漏洞、密钥泄露）
- 代码质量（质量评分下降、警告数）
- 部署与发布（部署失败、自动回滚触发）
- 运行健康（健康检查失败）
- 性能退化（构建性能退化、基准回归）

### dashboards/cupolas-dashboard.json

Cupolas 子系统的 Grafana CI/CD 仪表盘，提供：

- 构建状态概览与构建成功率
- 构建时长趋势与分阶段时长
- 测试覆盖率与测试结果
- 静态分析问题
- 安全漏洞（按严重程度）与开源安全问题
- 部署状态与近期部署
- Fuzzing 结果与基准对比

## 依赖关系

| 组件 | 用途 |
|------|------|
| Prometheus | 告警规则引擎 |
| Grafana | 仪表盘可视化 |
| Cupolas 子系统 | 被监控目标 |

---

© 2025-2026 SPHARX Ltd. All Rights Reserved.

<!-- SPDX-License-Identifier: AGPL-3.0-or-later OR Apache-2.0 -->
<!-- Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved. -->

# `.github/` — Ecosystem Manager 仓库自动化

> GitHub Actions 工作流与 CI 模板，服务于
> [Manager](https://atomgit.com/openairymax/manager) 叶子仓库。

---

## 定位

Manager 是 Airymax AI Agent 运行时平台的**统一配置与生命周期管理中心**——
AgentRT 运行时、构建工具链、可观测性栈及周边守护进程消费的所有配置的唯一真源。
本目录承载该仓库的 GitHub 级自动化配置。

## 目录内容

```
.github/
├── README.md              # 本文件
└── workflows/
    └── ci.yml             # CI 流水线（Schema 校验 + 漂移检测 + 测试套件）
```

## CI 流水线

| 工作流 | 触发条件 | 职责 |
|--------|----------|------|
| `ci.yml` | PR / push | JSON Schema 校验、配置漂移检测、Python 测试套件 |

## 相关链接

| 资源 | 链接 |
|------|------|
| **主 README** | [manager/README.md](../README.md) |
| **伞仓** | [airymaxhub](https://atomgit.com/openairymax/airymaxhub) |
| **Ecosystem 管理仓** | [ecosystem/](../../) |

## 许可证

双许可证：**AGPL v3 + Apache 2.0**（SPDX: `AGPL-3.0-or-later OR Apache-2.0`）。
详见仓库根目录 [LICENSE](../LICENSE) 与 [NOTICE](../NOTICE)。

Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved.

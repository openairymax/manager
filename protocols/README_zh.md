# 协议厂商清单 — L3 策略注入面

> AgentRT 协议层的厂商/框架策略数据。机制唯一实现在 `agentrt/protocols/core`，
> 本目录只承载策略。[manager](../) 生态仓的数据面。

**语言：** [English](README.md) | 简体中文

---

## 概述

本目录是 AgentRT 协议层的 **L3 策略注入面**：以 JSON 清单描述外部协议厂商
与 agent 框架。**机制**——传输实现、JSON-RPC 编解码骨架、重试/退避/心跳/
重连状态机、协议注册表——唯一实现在 `agentrt/protocols/core`；本目录的
清单**只承载策略**，启动期加载，作为注册表的自注册数据源。

**入清单判据**（评审强制）：某字段入清单，当且仅当改动它会改变产品行为
语义。纯实现常量——日志标签、错误码基址、哈希常量、缓冲区/分块尺寸、
socket 语义宏——留在机制内，不入清单。

## 文件

```
protocols/
├── README.md               # 英文版
├── README_zh.md            # 本文件（中文版）
└── vendors/
    ├── _schema.json        # JSON Schema（draft 2020-12）——清单契约
    ├── jsonrpc.json        # JSON-RPC 2.0        （core）
    ├── mcp.json            # MCP v1.0.0          （standard）
    ├── a2a.json            # A2A v0.3.0          （standard）
    ├── agntcy.json         # AGNTCY v0.1.0       （standard）
    ├── openai.json         # OpenAI v1.0         （integration）
    ├── claude.json         # Claude v1.0.0       （integration）
    ├── china_eco.json      # 中国生态 v0.1.0     （integration）
    ├── openclaw.json       # OpenClaw v1.0.0     （integration）
    ├── openjiuwen.json     # OpenJiuwen v0.1.0   （integration）
    ├── autogen.json        # AutoGen v1.0.0      （framework）
    └── langchain.json      # LangChain v1.0.0    （framework）
```

`kind` 与机制核 `proto_category_t` 一一对应：`core` → 内置线上契约；
`standard` → 开放行业标准（MCP / A2A / AGNTCY）；`integration` → 厂商
HTTP API；`framework` → agent 框架。

## 清单结构

每份清单须通过 `vendors/_schema.json` 校验（`manifest_version` 当前为 `1`）：

| 块 | 必填 | 用途 |
|----|------|------|
| `manifest_version` | 是 | 清单结构版本（常量 `1`） |
| `id` | 是 | 唯一标识（`^[a-z][a-z0-9_]*$`） |
| `kind` | 是 | `core` \| `standard` \| `integration` \| `framework` |
| `protocol` | 是 | 线上身份：`name`、`version`、可选 `aliases` |
| `registry` | 否 | 内置注册表元数据（name、description、category、type、`capabilities[]`）——仅被 agentrt 预置注册的厂商具备 |
| `interface` | 否 | RPC 面：`methods[]`、`invoke`（`style`、`path`、`version`） |
| `transport` | 否 | 传输策略：`kind`（`stdio` \| …）、端点与连接参数 |

## 治理

- **新增厂商**：在 `vendors/` 下追加一份清单，必须通过 `_schema.json`
  校验；除非引入新的传输 `kind`，机制代码零改动。
- **改动字段**：若改动改变行为语义，仅当 schema 契约本身变化时才提升
  `manifest_version`——厂商数据变化不提升。
- **校验**：清单在被 agentrt 注册表加载前先做 schema 校验；非法清单
  fail-closed 拒绝。

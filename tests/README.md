# Manager 测试套件

**模块路径**: `ecosystem/manager/tests/`
**版本**: v0.1.9（随 Manager 仓库）

## 概述

`manager/tests/` 包含 Manager 模块的测试套件，覆盖配置一致性（配置漂移检测铁律）、注册表一致性、`tools/` 工具集的单元测试与集成测试。测试套件通过 pytest 运行。

## 目录结构

```
tests/
├── test_base_utils.py         # tools/base/utils.py 单元测试（ConfigLoader / ReportExporter / FileHelper）
├── test_config_consistency.py # 配置一致性测试（遗留路径禁令、SSoT 同源校验）
├── test_config_diff.py        # tools/src/config_diff.py 单元测试
├── test_schema_diff.py        # tools/src/schema_diff.py 单元测试
├── test_tools.py              # tools/ 工具集成测试（audit_log_generator / drift_detector / config_version_cleanup）
├── test_agent_registry_consistency.py # Agent 注册表一致性测试（registry.yaml ↔ agents.yaml）
├── test_skill_registry_consistency.py # 技能注册表一致性测试（registry.yaml ↔ skills/definitions/）
└── README.md                  # 本文件
```

## 测试类型

### 1. 基础工具测试 (`test_base_utils.py`)

`tools/base/utils.py` 的单元测试：

- `ConfigLoader`：YAML / JSON / BOM 加载、文件不存在等错误处理
- `ReportExporter` / `FileHelper`：报告导出与文件操作

### 2. 配置一致性测试 (`test_config_consistency.py`)

守护 AIRY_HOME 路径体系与密钥变量名 SSoT，防止声明与实现漂移：

- T1：`configs/agentrt.yaml` 无遗留硬编码路径（`/var/lib`、`/var/log`、`~/.agentrt` 等），本地路径值以 `${AIRY_HOME}` 开头
- T2：`agentrt.yaml` 审计日志路径与 C 侧 `daemon_security.c` 默认一致
- T3：`model/model.yaml` 的 `api_key_env` 变量 ⊆ `secrets.env.example`（密钥变量名 SSoT），模板禁止写入真实密钥
- T4：`model.yaml` 与 `model.json` 同源（默认模型一致）
- T5：orchestration key fallback 链覆盖 `model.yaml` 的 OpenAI 兼容 provider

### 3. 配置差异对比测试 (`test_config_diff.py`)

`tools/src/config_diff.py` 的单元测试：

- `ValueType` 值类型检测、`normalize_value` 归一化
- `deep_diff` 递归对比、`DiffEntry` / `DiffResult` 结构
- `compare_configs` 配置对比、`load_config_file` 加载、`format_diff_entry` 输出

### 4. Schema 差异测试 (`test_schema_diff.py`)

`tools/src/schema_diff.py` 的单元测试：

- `DiffSeverity` / `DiffEntry` / `DiffReport` 数据结构
- `SchemaDiffer`：各 Schema 文件与 `agentrt.yaml` 的双向一致性检查

### 5. 工具集成测试 (`test_tools.py`)

`tools/` 工具集的集成测试：

- **审计日志生成器**：`ActionType`（LOAD/RELOAD/CHANGE/ROLLBACK/VALIDATE/EXPORT/IMPORT）、`OperatorType`（user/system/ci_cd）、`AuditLogEntry` / `AuditLogGenerator` 生成与导出
- **配置漂移检测器**：`DriftSeverity` / `DriftType` / `DriftReport`、`ConfigDriftDetector` 的基线创建、漂移检测、严重程度分级与报告导出
- **版本历史清理**：`VersionInfo` / `CleanupResult` / `ConfigVersionCleanup` 清理逻辑与 `format_bytes`

### 6. Agent 注册表一致性测试 (`test_agent_registry_consistency.py`)

守护 `agent/registry.yaml` 与权威 Agent 清单 `ecosystem/agents/registry/agents.yaml` 的一致性：

- A1：两侧 `agent_id` 集合一致，且注册 Agent 总数为 14
- A2：基础字段（role / source / version / enabled）逐项一致
- A3：`contract_path` 指向的契约文件真实存在
- A4：计数元数据（total / implemented / planned agents）一致

### 7. 技能注册表一致性测试 (`test_skill_registry_consistency.py`)

守护 `skill/registry.yaml` 与 skills 叶子仓 `skills/definitions/` 目录的一致性：

- S1：`source: skills` 的注册条目与 `skills/definitions/` 下的技能定义一一对应
- S2：`contract_path` 指向的契约文件真实存在
- S3：`source` 取值合法（builtin / community / skills），社区技能默认禁用

## 使用方式

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行指定测试
python -m pytest tests/test_config_diff.py
python -m pytest tests/test_schema_diff.py
python -m pytest tests/test_tools.py
python -m pytest tests/test_config_consistency.py
python -m pytest tests/test_agent_registry_consistency.py
python -m pytest tests/test_skill_registry_consistency.py

# 生成 HTML 测试报告
python -m pytest --html=report.html tests/
```

## 测试示例

### 配置一致性测试

```python
def test_no_legacy_paths():
    """agentrt.yaml 实际配置值（非注释）禁止遗留路径。"""
    text = AGENTRT_YAML.read_text(encoding="utf-8")
    code_lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    body = "\n".join(code_lines)
    for legacy in LEGACY_PATH_PATTERNS:
        assert legacy not in body
```

### 漂移检测测试

```python
def test_detect_modified_file():
    """测试检测文件修改。"""
    detector = ConfigDriftDetector(config_dir)
    detector.create_baseline()

    # 修改文件
    modify_config("kernel/settings.yaml")

    report = detector.detect_drift()
    assert report.has_drift
    assert report.drifted_files == 1
```

## 依赖关系

| 组件 | 用途 |
|------|------|
| Python ≥ 3.10 | 运行环境 |
| pytest | 测试框架 |
| PyYAML | YAML 解析 |

---

© 2025-2026 SPHARX Ltd. All Rights Reserved.

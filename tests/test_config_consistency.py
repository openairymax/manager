# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""配置一致性测试（配置漂移检测铁律）。

守护 AIRY_HOME 路径体系与密钥变量名 SSoT，防止声明与实现漂移：

  - T1: agentrt.yaml 无遗留硬编码路径（/var/lib、/var/log、~/.agentrt 等）
  - T2: agentrt.yaml 审计日志路径与 C 侧 daemon_security.c 默认一致
  - T3: model.yaml providers[].api_key_env ⊆ secrets.env.example 变量（SSoT）
  - T4: model.yaml 与 model.json 同源（default_provider / default_model）
  - T5: orchestration key fallback 链覆盖 model.yaml 的 OpenAI 兼容 provider

文件定位均基于测试文件相对路径推导，不依赖本地绝对路径。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# 仓库内文件定位（相对测试文件推导，不硬编码本地路径）
_HUB_ROOT = Path(__file__).resolve().parents[3]
_MANAGER_DIR = Path(__file__).resolve().parent.parent

MODEL_YAML = _MANAGER_DIR / "model" / "model.yaml"
MODEL_JSON = _MANAGER_DIR / "model" / "model.json"
AGENTRT_YAML = _MANAGER_DIR / "configs" / "agentrt.yaml"
SECRETS_TEMPLATE = _HUB_ROOT.parent / "tools" / "scripts" / "ops" / "templates" / "secrets.env.example"
ORCHESTRATION_LLM = _HUB_ROOT / "ecosystem" / "agents" / "orchestration" / "core" / "llm.py"

# 遗留硬编码路径黑名单（配置漂移检测）
LEGACY_PATH_PATTERNS = [
    "/var/lib/agentrt",
    "/var/log/agentrt",
    "/etc/agentrt",
    "/usr/lib/agentrt",
    "~/.agentrt",
    "~/.agentrt/",
]


class TestAgentRTYamlNoLegacyPaths:
    """T1: agentrt.yaml 禁止遗留硬编码绝对路径。"""

    def test_config_exists(self):
        assert AGENTRT_YAML.exists(), f"missing {AGENTRT_YAML.relative_to(_HUB_ROOT)}"

    def test_no_legacy_paths(self):
        """实际配置值（非注释）禁止遗留路径。"""
        text = AGENTRT_YAML.read_text(encoding="utf-8")
        # 仅检查非注释行：头注释中的禁令举例（如 ~/.agentrt）不是配置值
        code_lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
        body = "\n".join(code_lines)
        for legacy in LEGACY_PATH_PATTERNS:
            assert legacy not in body, f"agentrt.yaml 残留遗留路径: {legacy}"

    def test_all_local_paths_use_airy_home(self):
        """yaml 中的文件系统路径值必须以 ${AIRY_HOME} 开头。

        文件系统路径特征：含 ≥2 个 '/'（如 ${AIRY_HOME}/data/memory）。
        HTTP 端点（/healthz、/readyz）与 http url 排除。
        """
        text = AGENTRT_YAML.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            m = re.match(r'^[-\w]+:\s*"([^"]*)"', stripped)
            if not m:
                continue
            value = m.group(1)
            if value.startswith("http") or value.count("/") < 2:
                continue
            assert value.startswith("${AIRY_HOME}"), \
                f"agentrt.yaml 路径值未使用 ${{AIRY_HOME}}: {value}"


class TestAuditLogPathConsistency:
    """T2: agentrt.yaml 审计日志路径与 daemon_security.c 默认一致。"""

    DAEMON_SECURITY_PATH = (
        _HUB_ROOT / "agentrt" / "daemons" / "common" / "src" / "security" / "daemon_security.c"
    )
    EXPECTED_PATH = "${AIRY_HOME}/data/agentrt/logs/daemon_audit.log"

    def test_config_matches_c_default(self):
        text = AGENTRT_YAML.read_text(encoding="utf-8")
        assert f"log_path: \"{self.EXPECTED_PATH}\"" in text

    def test_c_side_default_unchanged(self):
        """daemon_security.c 默认审计路径与配置声明一致（双向守护）。"""
        assert self.DAEMON_SECURITY_PATH.exists()
        c_text = self.DAEMON_SECURITY_PATH.read_text(encoding="utf-8")
        assert "airy_log_dir()" in c_text
        assert "daemon_audit.log" in c_text


class TestSecretsSSoT:
    """T3: model.yaml 的 api_key_env 变量 ⊆ secrets.env.example（密钥变量名 SSoT）。"""

    def test_template_exists(self):
        assert SECRETS_TEMPLATE.exists(), "secrets.env.example 缺失"

    def test_provider_key_env_covered_by_template(self):
        model_text = MODEL_YAML.read_text(encoding="utf-8")
        secrets_text = SECRETS_TEMPLATE.read_text(encoding="utf-8")

        env_vars = set(re.findall(r'^(\w+)=', secrets_text, re.M))
        used_keys = set(re.findall(r'api_key_env:\s*"([^"]+)"', model_text))
        used_keys.discard("")  # local provider 无 key

        missing = used_keys - env_vars
        assert not missing, \
            f"model.yaml 引用了 secrets.env.example 未声明的变量: {missing}"

    def test_template_has_no_placeholder_secrets(self):
        """模板中的 key 必须留空，禁止提交真实密钥。"""
        secrets_text = SECRETS_TEMPLATE.read_text(encoding="utf-8")
        for line in secrets_text.splitlines():
            m = re.match(r'^(\w+)=\S+$', line.strip())
            if m:
                assert False, f"secrets.env.example 禁止写入真实密钥: {m.group(1)}"


class TestModelYamlJsonSameSource:
    """T4: model.yaml 与 model.json 同源（v3 表格：models / default_model 一致）。"""

    def test_default_model_consistent(self):
        yaml_text = MODEL_YAML.read_text(encoding="utf-8")
        json_data = json.loads(MODEL_JSON.read_text(encoding="utf-8"))

        m = re.search(r'^\s*default_model:\s*([^\s#]+)', yaml_text, re.M)
        assert m, "model.yaml 缺 default_model"
        assert m.group(1) == json_data["default_model"], \
            "model.yaml 与 model.json 的 default_model 不一致"

    def test_models_table_matches_json(self):
        yaml_text = MODEL_YAML.read_text(encoding="utf-8")
        json_data = json.loads(MODEL_JSON.read_text(encoding="utf-8"))

        yaml_names = re.findall(r'^\s*-\s*name:\s*(\S+)', yaml_text, re.M)
        json_names = [m.get("name") for m in json_data.get("models", [])]
        assert yaml_names == json_names, \
            f"model.yaml models 表与 model.json 不一致: {yaml_names} != {json_names}"

        # v3 表格必填字段（model_id 即调用时的模型名，api_key_env 可空）
        for m in json_data.get("models", []):
            for field in ("name", "mode", "api_format", "base_url", "model_id"):
                assert field in m, f"model.json 模型行缺 {field}: {m.get('name', '?')}"


class TestOrchestrationKeyFallbackCoversModel:
    """T5: orchestration key fallback 链覆盖 model.yaml 的 OpenAI 兼容 provider。"""

    # orchestration 为 OpenAI 兼容客户端，覆盖 openai/deepseek/anthropic 三个兼容
    # provider 的 bearer key。google（generativelanguage 协议）与 local（无 key）
    # 不属兼容范围，由 llm_d 侧另行处理。
    OPENAI_COMPAT_KEYS = {"OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY"}

    def test_fallback_chain_covers_providers(self):
        model_text = MODEL_YAML.read_text(encoding="utf-8")
        llm_text = ORCHESTRATION_LLM.read_text(encoding="utf-8")

        used_keys = set(re.findall(r'api_key_env:\s*"([^"]+)"', model_text))
        used_keys.discard("")

        compat_keys = used_keys & self.OPENAI_COMPAT_KEYS

        # _resolve_api_key 内声明的 fallback 变量（顺序保持 OPENAI → DEEPSEEK → ANTHROPIC）
        m = re.search(
            r'for var in \(([^)]*)\)', llm_text
        )
        assert m, "orchestration _resolve_api_key 未定义 fallback 链"
        chain = {v.strip().strip('"') for v in m.group(1).split(",") if v.strip()}

        missing = compat_keys - chain
        assert not missing, \
            f"orchestration fallback 链未覆盖 model.yaml 的 OpenAI 兼容 provider key: {missing}"

    def test_deepseek_in_fallback_chain(self):
        """默认提供商 DeepSeek 的 key 变量必须在 fallback 链中。"""
        llm_text = ORCHESTRATION_LLM.read_text(encoding="utf-8")
        assert "DEEPSEEK_API_KEY" in llm_text

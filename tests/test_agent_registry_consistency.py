# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""Agent 注册表一致性测试（S-2 生态 SSoT 收敛门禁）。

守卫「执行体权威 = ecosystem/agents/registry/agents.yaml；manager 侧
agent/registry.yaml 仅补充运维增强字段」的 SSoT，防止基础字段漂移：

  - A1: 两注册表 agent_id 集合完全一致（以 agents.yaml 为权威）
  - A2: 共享基础字段（role/source/version/enabled）逐 agent 一致
  - A3: contract_path 指向的契约文件真实存在（悬空引用清零）
  - A4: 计数元数据（total/implemented/planned）与清单一致

文件定位均基于测试文件相对路径推导，不依赖本地绝对路径。
"""

from __future__ import annotations

from pathlib import Path

import yaml

# 仓库内文件定位（相对测试文件推导）
_MANAGER_DIR = Path(__file__).resolve().parent.parent
_ECOSYSTEM_DIR = _MANAGER_DIR.parent

MANAGER_AGENT_REGISTRY = _MANAGER_DIR / "agent" / "registry.yaml"
AUTHORITATIVE_AGENTS = _ECOSYSTEM_DIR / "agents" / "registry" / "agents.yaml"

# 基础字段对齐集合（manager 侧仅可补充运维增强字段，不得改写以下字段）
BASE_FIELDS = ("agent_id", "role", "source", "version", "enabled")


def _load_registry(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict) and "agents" in data, f"registry 缺少 agents 列表: {path}"
    return data


class TestAgentRegistryConsistency:
    """A1/A2: 两注册表 agent 集合与基础字段一致。"""

    @staticmethod
    def _agent_map(path: Path) -> dict:
        data = _load_registry(path)
        agents = {}
        for entry in data["agents"]:
            aid = entry.get("agent_id")
            assert aid, f"{path.name} 存在无 agent_id 条目"
            agents[aid] = entry
        return agents

    def test_agent_id_sets_match(self):
        """A1: agent_id 集合一致（以 agents.yaml 为权威）。"""
        auth = self._agent_map(AUTHORITATIVE_AGENTS)
        mgr = self._agent_map(MANAGER_AGENT_REGISTRY)
        missing = sorted(set(auth) - set(mgr))
        extra = sorted(set(mgr) - set(auth))
        assert not missing, f"manager registry 缺少权威 agent: {missing}"
        assert not extra, f"manager registry 多出非权威 agent: {extra}"
        assert len(mgr) == len(auth) == 14

    def test_base_fields_aligned(self):
        """A2: 共享基础字段逐 agent 一致（漂移即失败）。"""
        auth = self._agent_map(AUTHORITATIVE_AGENTS)
        mgr = self._agent_map(MANAGER_AGENT_REGISTRY)
        drift = []
        for aid, a_entry in sorted(auth.items()):
            m_entry = mgr[aid]
            for field in BASE_FIELDS:
                a_val = a_entry.get(field)
                m_val = m_entry.get(field)
                if a_val != m_val:
                    drift.append(f"{aid}.{field}: agents={a_val!r} manager={m_val!r}")
        assert not drift, "基础字段漂移:\n" + "\n".join(drift)


class TestContractPathExistence:
    """A3: contract_path 悬空引用清零（planned agent 允许 null）。"""

    def test_contract_paths_exist(self):
        auth = _load_registry(AUTHORITATIVE_AGENTS)
        missing = []
        for entry in auth["agents"]:
            cp = entry.get("contract_path")
            if not cp:
                continue
            # 三种布局候选（P2-1 独立组装兼容）：
            #  1) 伞仓内 <ecosystem>/<cp>             （cp 以 ecosystem/ 开头）
            #  2) 伞仓根 <ecosystem 父目录>/<cp>        （monorepo 相对路径）
            #  3) 独立组装 <assembly>/<cp 去 ecosystem/ 前缀>（agents 并列子仓）
            stripped = cp[len("ecosystem/"):] if cp.startswith("ecosystem/") else cp
            candidates = (
                _ECOSYSTEM_DIR / cp,
                _ECOSYSTEM_DIR.parent / cp,
                _ECOSYSTEM_DIR / stripped,
            )
            if not any(c.exists() for c in candidates):
                missing.append(f"{entry.get('agent_id')}: {cp}")
        assert not missing, "悬空 contract_path:\n" + "\n".join(missing)


class TestAgentCounts:
    """A4: 计数元数据与清单一致。"""

    def test_counts_match(self):
        auth = _load_registry(AUTHORITATIVE_AGENTS)
        mgr = _load_registry(MANAGER_AGENT_REGISTRY)
        agents = auth["agents"]
        total = len(agents)
        implemented = sum(1 for a in agents if a.get("implementation_status") == "implemented")
        planned = sum(1 for a in agents if a.get("implementation_status") == "planned")
        for name, reg in (("agents.yaml", auth), ("manager/agent/registry.yaml", mgr)):
            meta = reg.get("_metadata") or reg.get("_summary") or {}
            t = meta.get("total_agents") or meta.get("total_agents")
            i = meta.get("implemented_agents") or meta.get("enabled_agents")
            p = meta.get("planned_agents")
            if t is not None:
                assert t == total, f"{name}: total_agents={t} != 清单 {total}"
            if i is not None:
                assert i == implemented, f"{name}: implemented={i} != 清单 {implemented}"
            if p is not None:
                assert p == planned, f"{name}: planned={p} != 清单 {planned}"

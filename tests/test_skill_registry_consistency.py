# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""技能注册表一致性测试（S-1 生态 SSoT 收敛门禁）。

守卫「技能定义单一权威 = ecosystem/skills 叶仓；manager/skill/registry.yaml
仅引用（source: skills + contract_path 指向契约文件）」的 SSoT：

  - S1: source=skills 的官方技能与 skills/definitions/ 契约文件一一对应
  - S2: contract_path 指向的契约文件真实存在（悬空引用清零）
  - S3: source 枚举合法（builtin/community/skills），且 community 实验技能
       必须默认禁用（S-5 双契约隔离，禁止冒充内置能力）

文件定位均基于测试文件相对路径推导，不依赖本地绝对路径。
"""

from __future__ import annotations

from pathlib import Path

import yaml

# 仓库内文件定位（相对测试文件推导）
_MANAGER_DIR = Path(__file__).resolve().parent.parent
_ECOSYSTEM_DIR = _MANAGER_DIR.parent

MANAGER_SKILL_REGISTRY = _MANAGER_DIR / "skill" / "registry.yaml"
SKILLS_DEFINITIONS_DIR = _ECOSYSTEM_DIR / "skills" / "definitions"

# source 枚举（skill-registry.schema.json）：builtin = 底座内置；skills =
# 引用 skills 叶仓官方技能（SSoT 权威）；community = 社区实验区（S-5 隔离）
VALID_SOURCES = ("builtin", "community", "skills")


def _load_skill_registry(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict) and "skills" in data, f"registry 缺少 skills 列表: {path}"
    return data


def _contract_path_candidates(cp: str):
    """三种布局候选（P2-1 独立组装兼容）：
      1) <ecosystem>/<cp>                      （cp 以 ecosystem/ 开头）
      2) <ecosystem>/<cp 去 agent-workload/ecosystem/ 前缀>（monorepo 伞仓相对）
      3) 独立组装 <assembly>/<cp 去前缀>        （skills 并列子仓）
    """
    if cp.startswith("agent-workload/ecosystem/"):
        stripped = cp[len("agent-workload/ecosystem/"):]
        yield _ECOSYSTEM_DIR / stripped
    if cp.startswith("ecosystem/"):
        stripped = cp[len("ecosystem/"):]
        yield _ECOSYSTEM_DIR / stripped
    for k in ("agent-workload/ecosystem/", "ecosystem/"):
        if cp.startswith(k):
            yield _ECOSYSTEM_DIR.parent / cp[len(k):]


class TestSkillRegistryConsistency:
    """S1: source=skills 官方技能与 skills/definitions/ 一一对应。"""

    @staticmethod
    def _official_skills(path: Path) -> dict:
        data = _load_skill_registry(path)
        official = {}
        for entry in data["skills"]:
            if entry.get("source") != "skills":
                continue
            sid = entry.get("skill_id")
            assert sid, f"{path.name} 存在无 skill_id 的 skills 源条目"
            official[sid] = entry
        return official

    def test_source_enum_valid(self):
        """S3 前半：source 取值必须属于合法枚举。"""
        data = _load_skill_registry(MANAGER_SKILL_REGISTRY)
        invalid = []
        for entry in data["skills"]:
            src = entry.get("source")
            if src not in VALID_SOURCES:
                invalid.append(f"{entry.get('skill_id')}: source={src!r}")
        assert not invalid, "非法 source 枚举:\n" + "\n".join(invalid)

    def test_community_skills_disabled(self):
        """S3 后半：community 实验技能必须默认禁用（S-5 双契约隔离）。"""
        data = _load_skill_registry(MANAGER_SKILL_REGISTRY)
        enabled_community = [
            f"{e.get('skill_id')}: enabled={e.get('enabled')}"
            for e in data["skills"]
            if e.get("source") == "community" and e.get("enabled") is not False
        ]
        assert not enabled_community, \
            "community 实验技能不得默认启用（冒充内置能力）:\n" + "\n".join(enabled_community)

    def test_official_skills_have_contract_file(self):
        """S1: 每个 source=skills 技能在 skills/definitions/ 有契约文件。"""
        official = self._official_skills(MANAGER_SKILL_REGISTRY)
        assert official, "registry 无 source=skills 的官方技能登记"
        if not SKILLS_DEFINITIONS_DIR.is_dir():
            # 独立组装时 skills 叶仓并列，路径不同；伞仓场景必测
            pytest_skip = __import__("pytest").skip
            pytest_skip("skills 叶仓不在独立 clone 中（伞仓组装场景才断言）")

        contract_files = {p.stem for p in SKILLS_DEFINITIONS_DIR.glob("*.md")
                          if p.stem not in ("README", "README_zh")}
        missing = sorted(set(official) - contract_files)
        extra = sorted(contract_files - set(official))
        assert not missing, f"skills 叶仓缺契约定义: {missing}"
        # 官方技能契约必须被 registry 引用，禁止"定义了却未登记"漂移
        assert not extra, f"skills/definitions 存在未登记契约: {extra}"


class TestSkillContractPathExistence:
    """S2: contract_path 悬空引用清零。"""

    def test_contract_paths_exist(self):
        data = _load_skill_registry(MANAGER_SKILL_REGISTRY)
        missing = []
        for entry in data["skills"]:
            cp = entry.get("contract_path")
            if not cp:
                continue
            if not any(c.exists() for c in _contract_path_candidates(cp)):
                missing.append(f"{entry.get('skill_id')}: {cp}")
        assert not missing, "悬空 contract_path:\n" + "\n".join(missing)

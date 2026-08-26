#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025-2026 SPHARX Ltd.
# SPDX-License-Identifier: AGPL-3.0-or-later OR Apache-2.0

"""AgentRT 生态管理器 — 统一运维 CLI。

将生态内零散的运维脚本（drift_detector / config_diff / schema_diff /
audit_log_generator / benchmark_manager / config_version_cleanup 等）之外
的日常管理操作收敛到单一入口，提供:

- ``daemon status``     列出所有 daemon 的运行状态（进程 + unix socket 监听）
- ``daemon start/stop`` 启动 / 停止单个 daemon（nohup 启动、SIGTERM 停止）
- ``health``            对在线 daemon 经 unix socket 发起 JSON-RPC 2.0
                        ``health_check``，汇总健康状态
- ``model show/validate`` 查看 / 校验 ``model/model.yaml`` 的 provider 配置
- ``logs``              查看指定 daemon 日志尾部

仅依赖 Python 标准库（YAML 解析优先使用系统已装的 PyYAML，缺失时回退
读取同源 ``model/model.json``，保证零第三方依赖可运行）。

用法示例::

    python3 manager.py daemon status
    python3 manager.py daemon start llm_d
    python3 manager.py daemon stop llm_d
    python3 manager.py health
    python3 manager.py model show
    python3 manager.py model validate
    python3 manager.py logs llm_d -n 100
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────
# 路径常量
# ─────────────────────────────────────────────────────────────

#: 默认 AIRY_HOME：AgentRT 运行根（bin/run/logs/config）
DEFAULT_AIRY_HOME = Path("/home/spharx/SpharxWorks/.airymaxrt")

#: manager 模块根目录（本文件所在目录）
MANAGER_ROOT = Path(__file__).resolve().parent


def resolve_airy_home(explicit: Optional[str]) -> Path:
    """解析 AIRY_HOME：显式参数 > 环境变量 > 默认值。"""
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("AIRY_HOME", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_AIRY_HOME


# ─────────────────────────────────────────────────────────────
# daemon 枚举与进程探测
# ─────────────────────────────────────────────────────────────


def discover_daemons(airy_home: Path) -> List[str]:
    """扫描 ``bin/`` 下形如 ``*_d`` 的 daemon 可执行文件，返回排序后的名称列表。

    若 ``bin/`` 目录不存在则返回空列表。
    """
    bin_dir = airy_home / "bin"
    if not bin_dir.is_dir():
        return []
    names = []
    for entry in sorted(bin_dir.iterdir()):
        if entry.name.endswith("_d") and entry.is_file():
            # 跳过非可执行文件（如 .sh 辅助脚本名巧合带 _d 后缀的兜底）
            if os.access(entry, os.X_OK):
                names.append(entry.name)
    return names


def daemon_bin_path(airy_home: Path, name: str) -> Path:
    """返回 daemon 可执行文件路径；不存在则返回 None。"""
    path = airy_home / "bin" / name
    return path if path.is_file() else None


def daemon_socket_candidates(airy_home: Path, name: str) -> List[Path]:
    """daemon 的 unix socket 候选路径。

    daemon 实际监听名可能带 ``_d`` 后缀（``run/llm_d.sock``），也可能不带
    （``run/llm.sock``，C 侧 ``airy_runtime_dir_socket()`` 以服务名命名），
    因此两种形态都作为候选并按优先级尝试。
    """
    run_dir = airy_home / "run"
    base = name[:-2] if name.endswith("_d") else name
    return [
        run_dir / f"{name}.sock",
        run_dir / f"{base}.sock",
    ]


def process_alive(name: str, bin_path: Optional[Path]) -> bool:
    """用 pgrep 检查 daemon 进程是否存活。

    先按完整路径匹配（覆盖以绝对路径启动的情况），再按进程名精确匹配。
    pgrep 不可用或均未命中时返回 False。
    """
    patterns = []
    if bin_path is not None:
        patterns.append(str(bin_path))
    patterns.append(name)
    for pattern in patterns:
        try:
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        if result.returncode == 0 and result.stdout.strip():
            return True
    return False


def socket_listening(path: Path, timeout: float = 0.5) -> bool:
    """尝试连接 unix socket，连接成功说明 daemon 正在监听。"""
    if not path.exists():
        return False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(str(path))
        return True
    except (OSError, socket.timeout):
        return False
    finally:
        sock.close()


# ─────────────────────────────────────────────────────────────
# JSON-RPC 2.0 健康检查
# ─────────────────────────────────────────────────────────────


def rpc_call(sock_path: Path, method: str, params: Optional[Dict[str, Any]] = None,
             timeout: float = 2.0) -> Dict[str, Any]:
    """通过 unix socket 发起 JSON-RPC 2.0 调用并解析响应。

    响应可能不以换行分隔，因此边 recv 边尝试 ``json.loads``：一旦累积的
    字节可解析为完整 JSON 即返回。超时 / 连接失败抛 ``OSError``。
    """
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(str(sock_path))
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1,
        }
        sock.sendall(json.dumps(request).encode("utf-8"))
        buffer = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buffer += chunk
            # 响应无分隔符：尝试解析，成功即视为完整
            try:
                return json.loads(buffer.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        # 对端关闭连接但未解析出合法 JSON
        raise OSError("connection closed before a complete JSON response")
    finally:
        sock.close()


def health_check_daemon(airy_home: Path, name: str) -> Dict[str, Any]:
    """对单个 daemon 执行 health_check，返回状态描述 dict。"""
    result: Dict[str, Any] = {"daemon": name}
    candidates = daemon_socket_candidates(airy_home, name)
    sock_path = next((p for p in candidates if p.exists()), None)
    if sock_path is None:
        # gateway_d 监听 TCP（默认 8080/8081/8082），无 unix socket：
        # 用 TCP 端口可达性判定健康状态
        if name == "gateway_d":
            port = int(os.environ.get("AIRY_GATEWAY_PORT", "8080"))
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                    result["status"] = "UP"
                    result["service"] = "gateway_d"
                    result["detail"] = {"tcp_port": port}
                    return result
            except OSError as exc:
                result["status"] = "DOWN"
                result["reason"] = f"tcp connect failed: {exc}"
                return result
        result["status"] = "DOWN"
        result["reason"] = "socket missing"
        return result
    try:
        resp = rpc_call(sock_path, "health_check")
    except OSError as exc:
        result["status"] = "DOWN"
        result["reason"] = f"rpc failed: {exc}"
        return result
    if "error" in resp:
        result["status"] = "DOWN"
        result["reason"] = f"rpc error: {resp['error']}"
        return result
    payload = resp.get("result", {})
    # 兼容两种健康响应：{"healthy": bool}（channel_d 等）或
    # {"status": "ok", ...}（info_d/notify_d/observe_d 等）
    healthy = bool(payload.get("healthy", payload.get("status") == "ok"))
    result["status"] = "UP" if healthy else "DOWN"
    result["service"] = payload.get("service", name)
    result["timestamp"] = payload.get("timestamp")
    result["detail"] = payload
    return result


# ─────────────────────────────────────────────────────────────
# daemon 启停
# ─────────────────────────────────────────────────────────────


def start_daemon(airy_home: Path, name: str) -> int:
    """以 nohup 方式启动 daemon，日志写入 ``logs/<name>.log``。"""
    bin_path = daemon_bin_path(airy_home, name)
    if bin_path is None:
        print(f"错误：未找到 daemon 可执行文件 {airy_home / 'bin' / name}", file=sys.stderr)
        return 1
    if process_alive(name, bin_path):
        print(f"{name} 已在运行，跳过启动")
        return 0

    log_dir = airy_home / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}.log"

    env = dict(os.environ)
    env["AIRY_HOME"] = str(airy_home)

    try:
        with open(log_file, "ab") as fh:
            proc = subprocess.Popen(
                [str(bin_path)],
                stdin=subprocess.DEVNULL,
                stdout=fh,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )
    except OSError as exc:
        print(f"错误：启动 {name} 失败：{exc}", file=sys.stderr)
        return 1

    print(f"{name} 已启动 (pid={proc.pid})，日志：{log_file}")
    return 0


def stop_daemon(airy_home: Path, name: str) -> int:
    """向 daemon 进程发送 SIGTERM 停止。"""
    bin_path = daemon_bin_path(airy_home, name)
    pids = []
    if bin_path is not None:
        try:
            result = subprocess.run(
                ["pgrep", "-f", str(bin_path)], capture_output=True, text=True, timeout=5
            )
            pids = result.stdout.split()
        except (OSError, subprocess.TimeoutExpired):
            pids = []
    if not pids:
        try:
            result = subprocess.run(
                ["pgrep", "-x", name], capture_output=True, text=True, timeout=5
            )
            pids = result.stdout.split()
        except (OSError, subprocess.TimeoutExpired):
            pids = []

    if not pids:
        print(f"{name} 未在运行，无需停止")
        return 0

    stopped = 0
    for pid in pids:
        try:
            os.kill(int(pid), signal.SIGTERM)
            stopped += 1
        except (ProcessLookupError, PermissionError) as exc:
            print(f"警告：停止 pid={pid} 失败：{exc}", file=sys.stderr)
    print(f"{name} 已发送 SIGTERM（{stopped} 个进程）")
    return 0


# ─────────────────────────────────────────────────────────────
# model 配置
# ─────────────────────────────────────────────────────────────

#: model.yaml provider 必填字段
MODEL_REQUIRED_FIELDS = ("name", "base_url", "default_model", "api_key_env")


def _load_model_config() -> Tuple[Dict[str, Any], str]:
    """加载模型配置，返回 (配置 dict, 来源说明)。

    优先读取 ``model/model.yaml``（PyYAML 可用时）；PyYAML 缺失或解析失败
    时回退到同源 ``model/model.json``（与 model.yaml 保持同步的 JSON 版本），
    保证仅标准库环境也可运行。
    """
    yaml_path = MANAGER_ROOT / "model" / "model.yaml"
    json_path = MANAGER_ROOT / "model" / "model.json"

    if yaml_path.is_file():
        try:
            import yaml  # type: ignore
        except ImportError:
            pass
        else:
            try:
                with open(yaml_path, "r", encoding="utf-8") as fh:
                    return yaml.safe_load(fh), f"model/model.yaml ({yaml_path})"
            except Exception:
                pass

    if json_path.is_file():
        with open(json_path, "r", encoding="utf-8") as fh:
            return json.load(fh), f"model/model.json ({json_path})"

    raise FileNotFoundError(
        f"未找到模型配置：{yaml_path}（及同源 {json_path}）"
    )


def model_providers(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """提取 providers 列表（兼容旧 providers 段与 v2/v3 models 表格两种形态）。"""
    providers = config.get("providers", [])
    if isinstance(providers, dict):
        providers = list(providers.values())
    elif not isinstance(providers, list):
        providers = []
    # v2/v3：models 表格（每行一个模型连接，model_id 即默认模型名）
    models = config.get("models", [])
    if isinstance(models, list):
        for m in models:
            if not isinstance(m, dict):
                continue
            providers.append(
                {
                    "name": m.get("name", "-"),
                    "base_url": m.get("base_url", ""),
                    "default_model": m.get("model_id", ""),
                    "api_key_env": m.get("api_key_env", ""),
                }
            )
    return providers


# ─────────────────────────────────────────────────────────────
# 日志查看
# ─────────────────────────────────────────────────────────────


def tail_log(airy_home: Path, name: str, lines: int) -> int:
    """输出 ``logs/<name>.log`` 尾部 lines 行。"""
    log_file = airy_home / "logs" / f"{name}.log"
    if not log_file.is_file():
        print(f"错误：日志文件不存在：{log_file}", file=sys.stderr)
        return 1
    with open(log_file, "r", encoding="utf-8", errors="replace") as fh:
        # 直接 seek 到末尾向前回溯，避免读入超大文件
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        block = 8192
        data = b""
        pos = size
        while pos > 0 and data.count(b"\n") < lines:
            read_size = min(block, pos)
            pos -= read_size
            fh.seek(pos)
            chunk = fh.read(read_size).encode("utf-8", errors="replace")
            data = chunk + data
        text = data.decode("utf-8", errors="replace")
        tail_lines = text.splitlines()[-lines:]
        sys.stdout.write("\n".join(tail_lines))
        if tail_lines:
            sys.stdout.write("\n")
    return 0


# ─────────────────────────────────────────────────────────────
# 子命令实现
# ─────────────────────────────────────────────────────────────


def cmd_daemon_status(args: argparse.Namespace) -> int:
    """daemon status：列出所有 daemon 的进程与 socket 监听状态表格。"""
    airy_home = args.airy_home
    daemons = discover_daemons(airy_home)
    if not daemons:
        print(f"提示：{airy_home / 'bin'} 下未发现 *_d daemon", file=sys.stderr)
        return 1

    print(f"AIRY_HOME: {airy_home}")
    print(f"{'DAEMON':<16} {'PROCESS':<10} {'SOCKET':<14} SOCKET_PATH")
    print("-" * 90)
    online = 0
    for name in daemons:
        alive = process_alive(name, daemon_bin_path(airy_home, name))
        sock_path = next(
            (p for p in daemon_socket_candidates(airy_home, name) if p.exists()),
            None,
        )
        listening = socket_listening(sock_path) if sock_path is not None else False
        if alive:
            online += 1
        proc_state = "UP" if alive else "DOWN"
        sock_state = "LISTEN" if listening else ("EXISTS" if sock_path else "-")
        print(f"{name:<16} {proc_state:<10} {sock_state:<14} {sock_path or '-'}")
    print("-" * 90)
    print(f"在线 daemon：{online}/{len(daemons)}")
    return 0


def cmd_daemon_start(args: argparse.Namespace) -> int:
    """daemon start <name>。"""
    return start_daemon(args.airy_home, args.name)


def cmd_daemon_stop(args: argparse.Namespace) -> int:
    """daemon stop <name>。"""
    return stop_daemon(args.airy_home, args.name)


def cmd_health(args: argparse.Namespace) -> int:
    """health：对在线 daemon 执行 JSON-RPC health_check 并汇总。"""
    airy_home = args.airy_home
    daemons = discover_daemons(airy_home)
    if not daemons:
        print(f"提示：{airy_home / 'bin'} 下未发现 *_d daemon", file=sys.stderr)
        return 1

    print(f"AIRY_HOME: {airy_home}")
    print(f"{'DAEMON':<16} {'STATUS':<8} DETAIL")
    print("-" * 90)
    up = down = 0
    for name in daemons:
        bin_path = daemon_bin_path(airy_home, name)
        if not process_alive(name, bin_path):
            print(f"{name:<16} {'DOWN':<8} process not running")
            down += 1
            continue
        result = health_check_daemon(airy_home, name)
        status = result.get("status", "DOWN")
        if status == "UP":
            up += 1
            detail = result.get("detail", {})
            print(
                f"{name:<16} {'UP':<8} service={result.get('service')} "
                f"timestamp={detail.get('timestamp')}"
            )
        else:
            down += 1
            print(f"{name:<16} {'DOWN':<8} {result.get('reason', 'unknown')}")
    print("-" * 90)
    print(f"健康 daemon：{up}，异常 daemon：{down}")
    return 1 if down > 0 else 0


def cmd_model_show(args: argparse.Namespace) -> int:
    """model show：展示每个 provider 的 name/base_url/default_model/api_key_env。"""
    try:
        config, source = _load_model_config()
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    providers = model_providers(config)
    if not providers:
        print("提示：配置中未定义任何 provider", file=sys.stderr)
        return 1

    print(f"模型配置来源：{source}")
    print(f"{'NAME':<14} {'BASE_URL':<46} {'DEFAULT_MODEL':<20} API_KEY_ENV")
    print("-" * 110)
    for p in providers:
        print(
            f"{str(p.get('name', '-')):<14} "
            f"{str(p.get('base_url', '-')):<46} "
            f"{str(p.get('default_model', '-')):<20} "
            f"{p.get('api_key_env', '') or '(none)'}"
        )
    print("-" * 110)
    print(f"共 {len(providers)} 个 provider")
    return 0


def cmd_model_validate(args: argparse.Namespace) -> int:
    """model validate：校验 provider 必填字段完整性。"""
    try:
        config, source = _load_model_config()
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    providers = model_providers(config)
    if not providers:
        print("提示：配置中未定义任何 provider", file=sys.stderr)
        return 1

    print(f"模型配置来源：{source}")
    errors: List[str] = []
    warnings: List[str] = []
    seen_names: Dict[str, int] = {}

    for idx, p in enumerate(providers):
        if not isinstance(p, dict):
            errors.append(f"providers[{idx}] 不是对象")
            continue
        name = str(p.get("name", ""))
        seen_names[name] = seen_names.get(name, 0) + 1
        for field in MODEL_REQUIRED_FIELDS:
            if field not in p:
                errors.append(f"provider {name or idx}: 缺少必填字段 {field}")
            elif field != "api_key_env" and not str(p[field]).strip():
                errors.append(f"provider {name or idx}: 字段 {field} 为空")
        default_model = p.get("default_model")
        models = p.get("models") or []
        if default_model and models and default_model not in models:
            warnings.append(
                f"provider {name}: default_model {default_model} 不在 models 列表中"
            )

    for name, count in seen_names.items():
        if count > 1:
            errors.append(f"provider 名称重复：{name} (x{count})")

    for err in errors:
        print(f"[错误] {err}")
    for warn in warnings:
        print(f"[警告] {warn}")

    if not errors:
        print(f"校验通过：{len(providers)} 个 provider 必填字段完整")
        return 0
    print(f"校验失败：{len(errors)} 个错误，{len(warnings)} 个警告")
    return 1


def cmd_logs(args: argparse.Namespace) -> int:
    """logs <name>：查看 daemon 日志尾部。"""
    return tail_log(args.airy_home, args.name, args.lines)


# ─────────────────────────────────────────────────────────────
# CLI 装配
# ─────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """构建子命令解析器。"""
    parser = argparse.ArgumentParser(
        prog="manager.py",
        description="AgentRT 生态管理器 — daemon 生命周期 / 健康检查 / 模型配置 / 日志查看",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python3 manager.py daemon status\n"
            "  python3 manager.py daemon start llm_d\n"
            "  python3 manager.py daemon stop llm_d\n"
            "  python3 manager.py health\n"
            "  python3 manager.py model show\n"
            "  python3 manager.py model validate\n"
            "  python3 manager.py logs llm_d -n 100\n"
        ),
    )
    parser.add_argument(
        "--airy-home",
        default=None,
        help=f"AIRY_HOME 路径（默认环境变量 AIRY_HOME，否则 {DEFAULT_AIRY_HOME}）",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # daemon
    p_daemon = sub.add_parser("daemon", help="daemon 生命周期管理")
    p_daemon.add_argument("action", choices=["status", "start", "stop"],
                          help="status=查看状态 / start=启动 / stop=停止")
    p_daemon.add_argument("name", nargs="?", help="daemon 名称（start/stop 必填，如 llm_d）")

    # health
    p_health = sub.add_parser("health", help="对在线 daemon 执行健康检查（JSON-RPC health_check）")

    # model
    p_model = sub.add_parser("model", help="模型配置管理")
    p_model.add_argument("action", choices=["show", "validate"],
                         help="show=查看 provider 配置 / validate=校验必填字段")

    # logs
    p_logs = sub.add_parser("logs", help="查看 daemon 日志尾部")
    p_logs.add_argument("name", help="daemon 名称（如 llm_d）")
    p_logs.add_argument("-n", "--lines", type=int, default=50,
                        help="显示行数（默认 50）")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI 入口，返回进程退出码。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    args.airy_home = resolve_airy_home(args.airy_home)

    if args.command is None:
        parser.print_help()
        return 0

    try:
        if args.command == "daemon":
            if args.action == "status":
                return cmd_daemon_status(args)
            if args.name is None:
                parser.error("daemon start/stop 需要指定 daemon 名称")
            return cmd_daemon_start(args) if args.action == "start" else cmd_daemon_stop(args)
        if args.command == "health":
            return cmd_health(args)
        if args.command == "model":
            return cmd_model_show(args) if args.action == "show" else cmd_model_validate(args)
        if args.command == "logs":
            return cmd_logs(args)
    except KeyboardInterrupt:
        print("\n已中断", file=sys.stderr)
        return 130
    except Exception as exc:  # 兜底：所有未预期错误统一收敛为退出码 1
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

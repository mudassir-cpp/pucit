"""Docker helpers for Oracle lifecycle."""

from __future__ import annotations

import secrets
import string
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from pucit import config as cfg
from pucit.util import (
    config_dir,
    fail,
    first_existing,
    info,
    ok,
    run_cmd,
    warn,
    which,
)


def docker_bin() -> Optional[str]:
    return first_existing(("docker", "podman"))


def docker_available() -> bool:
    binary = docker_bin()
    if not binary:
        return False
    result = run_cmd([binary, "info"], capture=True)
    return result.returncode == 0


def docker_argv(*args: str) -> List[str]:
    binary = docker_bin()
    if not binary:
        raise RuntimeError("Docker/Podman not found. Run: pucit install docker")
    return [binary, *args]


def container_name() -> str:
    return str(cfg.get("oracle_container", "pucit-oracle"))


def oracle_image() -> str:
    return str(cfg.get("oracle_image"))


def oracle_port() -> int:
    return int(cfg.get("oracle_port", 1521))


def oracle_env_path() -> Path:
    return config_dir() / "oracle.env"


def load_oracle_password() -> Optional[str]:
    path = oracle_env_path()
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("ORACLE_PWD="):
            return line.split("=", 1)[1].strip()
    return None


def save_oracle_password(password: str) -> None:
    path = oracle_env_path()
    path.write_text(f"ORACLE_PWD={password}\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    # Oracle passwords often want a mix; ensure letter+digit
    pwd = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    pwd += [secrets.choice(alphabet) for _ in range(length - 3)]
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)


def container_exists(name: Optional[str] = None) -> bool:
    name = name or container_name()
    result = run_cmd(
        docker_argv("ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"),
        capture=True,
    )
    if result.returncode != 0:
        return False
    names = {line.strip() for line in (result.stdout or "").splitlines() if line.strip()}
    return name in names


def container_running(name: Optional[str] = None) -> bool:
    name = name or container_name()
    result = run_cmd(
        docker_argv("ps", "--filter", f"name=^{name}$", "--format", "{{.Names}}"),
        capture=True,
    )
    if result.returncode != 0:
        return False
    names = {line.strip() for line in (result.stdout or "").splitlines() if line.strip()}
    return name in names


def build_run_argv(password: str, name: Optional[str] = None) -> List[str]:
    name = name or container_name()
    port = oracle_port()
    return docker_argv(
        "run",
        "-d",
        "--name",
        name,
        "-p",
        f"{port}:1521",
        "-e",
        f"ORACLE_PWD={password}",
        "-v",
        f"{name}-data:/opt/oracle/oradata",
        oracle_image(),
    )


def pull_image() -> Tuple[bool, str]:
    argv = docker_argv("pull", oracle_image())
    result = run_cmd(argv, capture=True)
    if result.returncode == 0:
        return True, result.stdout or ""
    combined = (result.stderr or "") + (result.stdout or "")
    return False, combined


def print_connect_info(password: Optional[str] = None) -> None:
    password = password or load_oracle_password() or "<your-password>"
    port = oracle_port()
    info(f"Host: localhost  Port: {port}  Service: FREEPDB1")
    info(f"SYSTEM / {password}")
    info(f"sqlplus system/{password}@//localhost:{port}/FREEPDB1")

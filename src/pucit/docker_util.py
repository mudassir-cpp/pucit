"""Docker helpers for Oracle lifecycle."""

from __future__ import annotations

import secrets
import string
import time
from pathlib import Path
from typing import List, Optional, Tuple

from pucit import config as cfg
from pucit.util import (
    config_dir,
    fail,
    first_existing,
    info,
    is_linux,
    is_windows,
    ok,
    run_cmd,
    run_streaming,
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
    """Pull the Oracle image with live docker progress (do not capture stdout)."""
    argv = docker_argv("pull", oracle_image())
    info("Image is several GB — layer progress from docker will print below.")
    code = run_streaming(argv)
    if code == 0:
        return True, ""
    return False, f"docker pull exited with code {code}"


def docker_desktop_exe() -> Optional[Path]:
    if not is_windows():
        return None
    candidates = [
        Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe"),
        Path.home() / "AppData" / "Local" / "Docker" / "Docker Desktop.exe",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def try_start_docker_daemon() -> bool:
    """Best-effort start Docker Desktop (Windows) or systemd docker (Linux)."""
    if is_windows():
        exe = docker_desktop_exe()
        if not exe:
            warn("Docker Desktop executable not found")
            return False
        info(f"Starting Docker Desktop: {exe}")
        # DETACHED_PROCESS so we don't wait on the GUI
        run_cmd(["cmd", "/c", "start", "", str(exe)], capture=True)
        return True
    if is_linux() and which("systemctl"):
        info("Trying to start docker via systemctl …")
        result = run_cmd(["sudo", "systemctl", "enable", "--now", "docker"], capture=True)
        return result.returncode == 0
    return False


def wait_for_docker(timeout: float = 90.0, interval: float = 3.0) -> bool:
    """Poll until `docker info` succeeds or timeout."""
    deadline = time.monotonic() + timeout
    info(f"Waiting for Docker daemon (up to {int(timeout)}s) …")
    while time.monotonic() < deadline:
        if docker_available():
            ok("Docker daemon is ready")
            return True
        time.sleep(interval)
    return False


def ensure_docker(*, install_if_missing: bool = True) -> bool:
    """
    Ensure a usable Docker/Podman daemon.
    Returns True if ready; prints guidance and returns False otherwise.
    """
    if docker_available():
        return True

    if not docker_bin():
        if not install_if_missing:
            fail("Docker/Podman not found. Run: pucit install docker")
            return False
        warn("Docker not found — installing …")
        from pucit.platform import PackageError, docker_packages, install_packages

        try:
            code = install_packages(docker_packages(), title="Docker")
        except PackageError as exc:
            fail(str(exc))
            return False
        if code != 0:
            return False
        if is_windows():
            info("If Docker Desktop was just installed, finish its setup wizard, then retry.")
        try_start_docker_daemon()
        if wait_for_docker():
            return True
        fail("Docker installed but daemon not ready yet.")
        if is_windows():
            info("Open Docker Desktop from the Start menu, wait until it says Running, then:")
            info("  pucit install oracle")
        else:
            info("Try: sudo systemctl start docker")
            info("And add yourself to the docker group: sudo usermod -aG docker $USER")
        return False

    # CLI present, daemon not usable
    warn("Docker CLI found but daemon not usable — trying to start it …")
    try_start_docker_daemon()
    if wait_for_docker():
        return True

    fail("Docker is installed but not usable.")
    if is_windows():
        info("Start Docker Desktop from the Start menu and wait until it is fully running, then retry.")
    else:
        info("Try: sudo systemctl start docker")
        info("If permission denied: sudo usermod -aG docker $USER  (then log out/in)")
    return False


def jdbc_url(port: Optional[int] = None) -> str:
    port = port or oracle_port()
    return f"jdbc:oracle:thin:@//localhost:{port}/FREEPDB1"


def print_connect_info(password: Optional[str] = None) -> None:
    password = password or load_oracle_password() or "<your-password>"
    port = oracle_port()
    ok("Local Oracle connection (for labs / DBeaver)")
    info(f"Host:     localhost")
    info(f"Port:     {port}")
    info(f"Service:  FREEPDB1")
    info(f"User:     system")
    info(f"Password: {password}")
    info("")
    info("sqlplus:")
    info(f"  sqlplus system/{password}@//localhost:{port}/FREEPDB1")
    info("")
    info("DBeaver / SQL Developer (New Connection → Oracle → Basic):")
    info(f"  Host: localhost   Port: {port}   Database: FREEPDB1")
    info(f"  Username: system")
    info(f"  JDBC: {jdbc_url(port)}")

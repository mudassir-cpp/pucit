"""Shared helpers for subprocess, paths, and console output."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from rich.console import Console

console = Console(stderr=False)
err_console = Console(stderr=True)


def which(name: str) -> Optional[str]:
    return shutil.which(name)


def is_windows() -> bool:
    return sys.platform.startswith("win")


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def config_dir() -> Path:
    if is_windows():
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        path = base / "pucit"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        path = base / "pucit"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_cmd(
    argv: Sequence[str],
    *,
    check: bool = False,
    capture: bool = False,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    input_text: Optional[str] = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(argv),
        check=check,
        capture_output=capture,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=env,
        input=input_text,
    )


def run_streaming(argv: Sequence[str], *, cwd: Optional[Path] = None, env: Optional[dict] = None) -> int:
    proc = subprocess.Popen(
        list(argv),
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    return proc.wait()


def ok(msg: str) -> None:
    console.print(f"[green]✓[/green] {msg}")


def warn(msg: str) -> None:
    console.print(f"[yellow]![/yellow] {msg}")


def fail(msg: str) -> None:
    err_console.print(f"[red]✗[/red] {msg}")


def info(msg: str) -> None:
    console.print(f"[cyan]i[/cyan] {msg}")


def detect_pkg_manager() -> Optional[str]:
    if is_windows():
        for name in ("winget", "choco"):
            if which(name):
                return name
        return None
    for name in ("dnf", "apt-get", "apt", "pacman", "zypper"):
        if which(name):
            return name
    return None


def split_flags(flags: Optional[str]) -> List[str]:
    if not flags:
        return []
    # simple whitespace split; students pass e.g. "-O2 -std=c++20"
    return [part for part in flags.split() if part]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def first_existing(candidates: Iterable[str]) -> Optional[str]:
    for name in candidates:
        found = which(name)
        if found:
            return found
    return None

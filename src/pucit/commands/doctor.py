"""Environment doctor and component listing."""

from __future__ import annotations

import platform
import sys

import typer
from rich.table import Table

from pucit import __version__
from pucit import docker_util as d
from pucit.cpp_build import find_compiler
from pucit.util import console, which

doctor_app = typer.Typer(help="Health checks (also available as top-level pucit doctor).")


def _row(table: Table, name: str, ok: bool, detail: str) -> None:
    mark = "[green]ok[/green]" if ok else "[red]missing[/red]"
    table.add_row(name, mark, detail)


def run_doctor() -> int:
    table = Table(title=f"pucit doctor (v{__version__})")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    _row(table, "OS", True, f"{platform.system()} {platform.release()} ({platform.machine()})")
    _row(table, "Python", True, sys.version.split()[0])

    compiler = find_compiler()
    _row(table, "C++ compiler", bool(compiler), compiler or "run: pucit install pf")
    _row(table, "make", bool(which("make")), which("make") or "—")
    _row(table, "gdb", bool(which("gdb")), which("gdb") or "—")
    _row(table, "cmake", bool(which("cmake")), which("cmake") or "—")

    docker = d.docker_bin()
    docker_ok = bool(docker) and d.docker_available()
    detail = docker or "run: pucit install docker"
    if docker and not d.docker_available():
        detail = f"{docker} found but daemon not usable"
    _row(table, "Docker", docker_ok, detail)

    name = d.container_name()
    if docker_ok and d.container_exists(name):
        state = "running" if d.container_running(name) else "stopped"
        _row(table, "Oracle container", True, f"{name} ({state})")
    else:
        _row(table, "Oracle container", False, "run: pucit install oracle")

    bypass = which("bypass_pucit")
    _row(table, "bypass_pucit", bool(bypass), bypass or "pip install bypass-pucit")

    sqlplus = which("sqlplus")
    _row(table, "sqlplus", bool(sqlplus), sqlplus or "optional: pucit install sqlclient")

    console.print(table)
    return 0


def run_list() -> int:
    table = Table(title="pucit managed components")
    table.add_column("Component")
    table.add_column("Status")

    compiler = find_compiler()
    table.add_row("pf / C++", "ready" if compiler else "not installed")
    docker_ok = bool(d.docker_bin()) and d.docker_available()
    table.add_row("docker", "ready" if docker_ok else "not ready")
    name = d.container_name()
    if docker_ok and d.container_exists(name):
        table.add_row("oracle", "running" if d.container_running(name) else "stopped")
    else:
        table.add_row("oracle", "not installed")
    table.add_row("bypass_pucit", "ready" if which("bypass_pucit") else "not installed")
    table.add_row("sqlplus", "ready" if which("sqlplus") else "not installed")
    console.print(table)
    return 0

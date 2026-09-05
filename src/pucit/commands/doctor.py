"""Environment doctor and component listing."""

from __future__ import annotations

import platform
import sys

import typer
from rich.table import Table

from pucit import __version__
from pucit import docker_util as d
from pucit.cpp_build import find_c_compiler, find_cxx_compiler
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

    cxx = find_cxx_compiler()
    cc = find_c_compiler()
    _row(table, "C++ compiler", bool(cxx), cxx or "run: pucit install pf")
    _row(table, "C compiler", bool(cc), cc or "run: pucit install pf")
    _row(table, "make", bool(which("make") or which("mingw32-make")), which("make") or which("mingw32-make") or "—")
    _row(table, "gdb", bool(which("gdb")), which("gdb") or "—")
    _row(table, "cmake", bool(which("cmake")), which("cmake") or "—")

    docker = d.docker_bin()
    docker_ok = bool(docker) and d.docker_available()
    if not docker:
        detail = "run: pucit install docker"
    elif not d.docker_available():
        if sys.platform.startswith("win"):
            detail = f"{docker} found but Docker Desktop not running — start it, then retry"
        else:
            detail = f"{docker} found but daemon not usable — try: sudo systemctl start docker"
    else:
        detail = docker
    _row(table, "Docker", docker_ok, detail)

    name = d.container_name()
    if docker_ok and d.container_exists(name):
        state = "running" if d.container_running(name) else "stopped"
        _row(table, "Oracle container", True, f"{name} ({state})")
    else:
        _row(table, "Oracle container", False, "run: pucit install oracle")

    try:
        import bypass_pucit
        from bypass_pucit.__about__ import __version__ as bypass_ver

        bypass_ok = True
        bypass_detail = f"bundled v{bypass_ver}"
    except Exception as exc:  # pragma: no cover
        bypass_ok = False
        bypass_detail = str(exc)
    _row(table, "bypass", bypass_ok, bypass_detail)

    sqlplus = which("sqlplus")
    _row(table, "sqlplus", bool(sqlplus), sqlplus or "optional: pucit install sqlclient")

    console.print(table)
    return 0


def run_list() -> int:
    table = Table(title="pucit managed components")
    table.add_column("Component")
    table.add_column("Status")

    cxx = find_cxx_compiler()
    cc = find_c_compiler()
    table.add_row("pf / C++", "ready" if cxx else "not installed")
    table.add_row("pf / C", "ready" if cc else "not installed")
    docker_ok = bool(d.docker_bin()) and d.docker_available()
    table.add_row("docker", "ready" if docker_ok else "not ready")
    name = d.container_name()
    if docker_ok and d.container_exists(name):
        table.add_row("oracle", "running" if d.container_running(name) else "stopped")
    else:
        table.add_row("oracle", "not installed")
    try:
        import bypass_pucit  # noqa: F401

        table.add_row("bypass", "bundled")
    except Exception:
        table.add_row("bypass", "missing")
    table.add_row("sqlplus", "ready" if which("sqlplus") else "not installed")
    console.print(table)
    return 0

"""Install subcommands: oracle, pf, docker, sqlclient."""

from __future__ import annotations

from typing import Optional

import typer

from pucit.commands.oracle import oracle_install
from pucit.platform import PackageError, docker_packages, install_packages, pf_packages
from pucit.util import detect_pkg_manager, fail, info, is_windows, ok, run_cmd, which

install_app = typer.Typer(help="Install toolchains and services.")


@install_app.command("oracle")
def install_oracle(
    password: Optional[str] = typer.Option(None, "--password", "-p"),
    pull_only: bool = typer.Option(False, "--pull-only"),
) -> None:
    """Install Oracle Free via Docker."""
    oracle_install(password=password, pull_only=pull_only)


@install_app.command("pf")
def install_pf() -> None:
    """Install Programming Fundamentals C++ essentials."""
    try:
        code = install_packages(pf_packages(), title="PF / C++ essentials")
    except PackageError as exc:
        fail(str(exc))
        raise typer.Exit(1) from exc
    if which("g++") or which("clang++"):
        ok(f"Compiler: {which('g++') or which('clang++')}")
    else:
        info("Packages installed; open a new shell if g++ is still not on PATH.")
    raise typer.Exit(code)


@install_app.command("docker")
def install_docker() -> None:
    """Install Docker Engine / Docker Desktop."""
    try:
        code = install_packages(docker_packages(), title="Docker")
    except PackageError as exc:
        fail(str(exc))
        raise typer.Exit(1) from exc
    if is_windows():
        info("Start Docker Desktop from the Start menu, then re-open your terminal.")
    else:
        if which("systemctl"):
            run_cmd(["sudo", "systemctl", "enable", "--now", "docker"], capture=True)
            info("If needed, add yourself to the docker group: sudo usermod -aG docker $USER")
    raise typer.Exit(code)


@install_app.command("sqlclient")
def install_sqlclient() -> None:
    """Install or guide Oracle Instant Client / sqlplus."""
    if which("sqlplus"):
        ok(f"sqlplus already present: {which('sqlplus')}")
        return

    if is_windows():
        info("Windows: download Instant Client (Basic + SQL*Plus) from Oracle:")
        info("  https://www.oracle.com/database/technologies/instant-client/downloads.html")
        info("Add the unzipped folder to PATH, then reopen the terminal.")
        raise typer.Exit(0)

    manager = detect_pkg_manager()
    pkgs = ["oracle-instantclient-sqlplus"] if manager == "dnf" else []
    if pkgs:
        try:
            code = install_packages(pkgs, title="Oracle SQL*Plus")
            raise typer.Exit(code)
        except PackageError:
            pass

    info("sqlplus is not in your distro repos by default.")
    info("Download Instant Client Basic + SQL*Plus RPMs/ZIPs from:")
    info("  https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html")
    info("Then: sudo alien/rpm install or unzip and export LD_LIBRARY_PATH + PATH.")
    raise typer.Exit(0)

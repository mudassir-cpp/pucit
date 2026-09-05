"""Oracle Database Free via Docker."""

from __future__ import annotations

import os
from typing import Optional

import typer

from pucit import docker_util as d
from pucit.platform import PackageError, docker_packages, install_packages
from pucit.util import fail, info, ok, run_cmd, warn

oracle_app = typer.Typer(help="Manage the local Oracle Free container.")


@oracle_app.command("install")
def oracle_install(
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="ORACLE_PWD (generated if omitted)"
    ),
    pull_only: bool = typer.Option(False, "--pull-only", help="Only pull the image"),
) -> None:
    """Install (pull + create) Oracle Free Docker container."""
    if not d.docker_bin():
        warn("Docker not found — trying to install it first")
        try:
            code = install_packages(docker_packages(), title="docker")
        except PackageError as exc:
            fail(str(exc))
            raise typer.Exit(1) from exc
        if code != 0:
            raise typer.Exit(code)

    if not d.docker_available():
        fail("Docker is installed but not usable. Start the Docker daemon/Desktop and retry.")
        raise typer.Exit(1)

    info(f"Pulling {d.oracle_image()} …")
    success, output = d.pull_image()
    if not success:
        fail("Image pull failed.")
        if "unauthorized" in output.lower() or "denied" in output.lower() or "login" in output.lower():
            info("Oracle Container Registry may require login / license accept:")
            info("  1) Visit https://container-registry.oracle.com/ and accept the Database Free terms")
            info("  2) docker login container-registry.oracle.com")
            info("  3) pucit install oracle")
        else:
            print(output)
        raise typer.Exit(1)
    ok("Image ready")

    if pull_only:
        return

    name = d.container_name()
    if d.container_exists(name):
        ok(f"Container '{name}' already exists. Use: pucit start oracle")
        d.print_connect_info()
        return

    pwd = password or os.environ.get("PUCIT_ORACLE_PWD") or d.load_oracle_password() or d.generate_password()
    d.save_oracle_password(pwd)
    argv = d.build_run_argv(pwd, name)
    display = [a.replace(f"ORACLE_PWD={pwd}", "ORACLE_PWD=***") for a in argv]
    info(" ".join(display))
    result = run_cmd(argv, capture=True)
    if result.returncode != 0:
        fail((result.stderr or result.stdout or "docker run failed").strip())
        raise typer.Exit(result.returncode)
    ok(f"Created container '{name}'")
    info("Oracle may take 1–2 minutes to become ready. Check: pucit status oracle")
    d.print_connect_info(pwd)


@oracle_app.command("start")
def oracle_start() -> None:
    """Start the Oracle container."""
    name = d.container_name()
    if not d.container_exists(name):
        fail(f"Container '{name}' not found. Run: pucit install oracle")
        raise typer.Exit(1)
    if d.container_running(name):
        ok(f"'{name}' is already running")
        return
    result = run_cmd(d.docker_argv("start", name), capture=True)
    if result.returncode != 0:
        fail((result.stderr or "start failed").strip())
        raise typer.Exit(result.returncode)
    ok(f"Started '{name}'")


@oracle_app.command("stop")
def oracle_stop() -> None:
    """Stop the Oracle container."""
    name = d.container_name()
    if not d.container_exists(name):
        fail(f"Container '{name}' not found")
        raise typer.Exit(1)
    result = run_cmd(d.docker_argv("stop", name), capture=True)
    if result.returncode != 0:
        fail((result.stderr or "stop failed").strip())
        raise typer.Exit(result.returncode)
    ok(f"Stopped '{name}'")


@oracle_app.command("status")
def oracle_status() -> None:
    """Show Oracle container status."""
    name = d.container_name()
    if not d.docker_bin():
        fail("Docker/Podman not found")
        raise typer.Exit(1)
    if not d.container_exists(name):
        warn(f"Container '{name}' is not installed")
        raise typer.Exit(1)
    state = "running" if d.container_running(name) else "stopped"
    ok(f"{name}: {state}")
    d.print_connect_info()


@oracle_app.command("logs")
def oracle_logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", help="Lines to show"),
) -> None:
    """Show Oracle container logs."""
    name = d.container_name()
    argv = d.docker_argv("logs", "--tail", str(tail))
    if follow:
        argv.append("-f")
    argv.append(name)
    raise typer.Exit(run_cmd(argv).returncode)


@oracle_app.command("rm")
def oracle_rm(
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Also remove data volume"),
    force: bool = typer.Option(False, "--force", "-f", help="Force remove"),
) -> None:
    """Remove the Oracle container."""
    name = d.container_name()
    if not d.container_exists(name):
        warn(f"Container '{name}' not found")
        return
    argv = d.docker_argv("rm")
    if force:
        argv.append("-f")
    if volumes:
        argv.append("-v")
    argv.append(name)
    result = run_cmd(argv, capture=True)
    if result.returncode != 0:
        fail((result.stderr or "rm failed").strip())
        raise typer.Exit(result.returncode)
    ok(f"Removed '{name}'")


@oracle_app.command("connect")
def oracle_connect(
    launch: bool = typer.Option(False, "--launch", "-l", help="Launch sqlplus if available"),
) -> None:
    """Print (or launch) a sqlplus connection."""
    from pucit.util import which

    d.print_connect_info()
    if not launch:
        return
    sqlplus = which("sqlplus")
    if not sqlplus:
        fail("sqlplus not found. Try: pucit install sqlclient")
        raise typer.Exit(1)
    pwd = d.load_oracle_password() or "oracle"
    port = d.oracle_port()
    conn = f"system/{pwd}@//localhost:{port}/FREEPDB1"
    raise typer.Exit(run_cmd([sqlplus, conn]).returncode)

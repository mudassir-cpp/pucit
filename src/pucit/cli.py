"""pucit — PUCIT student toolkit CLI."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer

from pucit import __version__
from pucit import cpp_build
from pucit import docker_util as d
from pucit.commands.bypass import bypass_app
from pucit.commands.doctor import run_doctor, run_list
from pucit.commands.install import install_app
from pucit.commands.oracle import oracle_app
from pucit.commands.scaffold import init_project, new_file
from pucit.util import fail, first_existing, info, ok, run_cmd, run_streaming, which

app = typer.Typer(
    name="pucit",
    help="PUCIT student toolkit — Oracle, PF C/C++, bypass, and lab ease commands.",
    no_args_is_help=True,
    add_completion=False,
)

app.add_typer(install_app, name="install")
app.add_typer(bypass_app, name="bypass")
app.add_typer(oracle_app, name="oracle")


def _oracle_target(target: str) -> None:
    if target.lower() not in {"oracle", "db", "oracledb"}:
        fail(f"Unknown target '{target}'. Try: oracle")
        raise typer.Exit(1)


@app.command("start")
def start_cmd(target: str = typer.Argument(..., help="Service to start (oracle)")) -> None:
    """Start a managed service: pucit start oracle"""
    _oracle_target(target)
    from pucit.commands.oracle import oracle_start

    oracle_start()


@app.command("stop")
def stop_cmd(target: str = typer.Argument(..., help="Service to stop (oracle)")) -> None:
    """Stop a managed service: pucit stop oracle"""
    _oracle_target(target)
    from pucit.commands.oracle import oracle_stop

    oracle_stop()


@app.command("status")
def status_cmd(target: str = typer.Argument("oracle", help="Service (oracle)")) -> None:
    """Show service status: pucit status oracle"""
    _oracle_target(target)
    from pucit.commands.oracle import oracle_status

    oracle_status()


@app.command("logs")
def logs_cmd(
    target: str = typer.Argument("oracle"),
    follow: bool = typer.Option(False, "--follow", "-f"),
    tail: int = typer.Option(100, "--tail"),
) -> None:
    """Show service logs: pucit logs oracle"""
    _oracle_target(target)
    from pucit.commands.oracle import oracle_logs

    oracle_logs(follow=follow, tail=tail)


@app.command("run")
def run_cmd(
    sources: Optional[List[str]] = typer.Argument(None, help="C/C++ sources (default: main.cpp or main.c)"),
    flags: Optional[str] = typer.Option(None, "--flags", "-f", help='Extra flags e.g. "-O2"'),
    std: Optional[str] = typer.Option(None, "--std", help="Language standard"),
    out: Optional[str] = typer.Option(None, "--out", "-o", help="Output binary"),
    input_file: Optional[str] = typer.Option(None, "--input", "-i", help="stdin from file"),
) -> None:
    """Compile and run: pucit run main.cpp  |  pucit run main.c"""
    try:
        code = cpp_build.execute_run(
            list(sources or []),
            flags=flags,
            std=std,
            out=out,
            input_file=input_file,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        fail(str(exc))
        raise typer.Exit(1) from exc
    raise typer.Exit(code)


@app.command("compile")
def compile_cmd(
    sources: Optional[List[str]] = typer.Argument(None),
    flags: Optional[str] = typer.Option(None, "--flags", "-f"),
    std: Optional[str] = typer.Option(None, "--std"),
    out: Optional[str] = typer.Option(None, "--out", "-o"),
) -> None:
    """Compile only: pucit compile main.cpp"""
    try:
        code = cpp_build.execute_run(
            list(sources or []),
            flags=flags,
            std=std,
            out=out,
            compile_only=True,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        fail(str(exc))
        raise typer.Exit(1) from exc
    raise typer.Exit(code)


@app.command("debug")
def debug_cmd(
    sources: Optional[List[str]] = typer.Argument(None),
    flags: Optional[str] = typer.Option(None, "--flags", "-f"),
    std: Optional[str] = typer.Option(None, "--std"),
    out: Optional[str] = typer.Option(None, "--out", "-o"),
) -> None:
    """Compile with -g and open gdb."""
    try:
        resolved = cpp_build.resolve_sources(list(sources or []))
        code, binary, _ = cpp_build.compile_sources(
            resolved, out=out, flags=flags, std=std, debug=True
        )
    except (FileNotFoundError, RuntimeError) as exc:
        fail(str(exc))
        raise typer.Exit(1) from exc
    if code != 0:
        raise typer.Exit(code)
    gdb = which("gdb")
    if not gdb:
        fail("gdb not found. Run: pucit install pf")
        raise typer.Exit(1)
    info(f"Starting gdb on {binary}")
    raise typer.Exit(run_streaming([gdb, str(binary)]))


@app.command("watch")
def watch_cmd(
    sources: Optional[List[str]] = typer.Argument(None),
    flags: Optional[str] = typer.Option(None, "--flags", "-f"),
    std: Optional[str] = typer.Option(None, "--std"),
    out: Optional[str] = typer.Option(None, "--out", "-o"),
    input_file: Optional[str] = typer.Option(None, "--input", "-i"),
) -> None:
    """Recompile + run on file change."""
    try:
        code = cpp_build.watch_run(
            list(sources or []),
            flags=flags,
            std=std,
            out=out,
            input_file=input_file,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        fail(str(exc))
        raise typer.Exit(1) from exc
    raise typer.Exit(code)


@app.command("clean")
def clean_cmd() -> None:
    """Remove build/ and a.out in the current directory."""
    removed = cpp_build.clean_artifacts()
    if not removed:
        info("Nothing to clean")
    else:
        for path in removed:
            ok(f"Removed {path}")


@app.command("new")
def new_cmd(
    name: str = typer.Argument(..., help="File or stem, e.g. hello, hello.c, or hello.cpp"),
    force: bool = typer.Option(False, "--force", "-f"),
    lang: Optional[str] = typer.Option(None, "--lang", "-l", help="c or cpp (default: from extension, else cpp)"),
) -> None:
    """Create a new C or C++ file from template."""
    new_file(name, force=force, lang=lang)


@app.command("init")
def init_cmd(
    lang: Optional[str] = typer.Argument("cpp", help="Language: c or cpp (default: cpp)"),
    force: bool = typer.Option(False, "--force", "-f"),
) -> None:
    """Scaffold a PF lab folder: pucit init  |  pucit init c  |  pucit init cpp"""
    init_project(force=force, lang=lang or "cpp")


@app.command("doctor")
def doctor_cmd() -> None:
    """Check compilers, Docker, Oracle, bypass, and friends."""
    raise typer.Exit(run_doctor())


@app.command("list")
def list_cmd() -> None:
    """List managed components and their status."""
    raise typer.Exit(run_list())


@app.command("version")
def version_cmd() -> None:
    """Show pucit version."""
    typer.echo(__version__)


@app.command("which")
def which_cmd(tool: str = typer.Argument(..., help="Tool name, e.g. g++ or docker")) -> None:
    """Show resolved path for a tool."""
    # allow g++ style
    path = which(tool) or first_existing((tool,))
    if not path and tool in {"g++", "cxx", "compiler"}:
        path = cpp_build.find_cxx_compiler() or cpp_build.find_compiler()
    if not path and tool in {"gcc", "cc"}:
        path = cpp_build.find_c_compiler()
    if not path and tool == "docker":
        path = d.docker_bin()
    if path:
        typer.echo(path)
    else:
        fail(f"{tool} not found")
        raise typer.Exit(1)


@app.command("open")
def open_cmd(path: str = typer.Argument(".", help="Path to open")) -> None:
    """Open a folder/file in VS Code, Cursor, or the file manager."""
    target = Path(path).resolve()
    editors = ("cursor", "code", "codium")
    for editor in editors:
        binary = which(editor)
        if binary:
            raise typer.Exit(run_cmd([binary, str(target)]).returncode)
    # fallback file manager / start
    import sys

    if sys.platform.startswith("win"):
        raise typer.Exit(run_cmd(["explorer", str(target)]).returncode)
    opener = which("xdg-open")
    if opener:
        raise typer.Exit(run_cmd([opener, str(target)]).returncode)
    fail("No editor or file manager found")
    raise typer.Exit(1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

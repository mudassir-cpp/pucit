"""Campus proxy via bypass-pucit."""

from __future__ import annotations

import shutil
import subprocess
from typing import Optional

import typer

from pucit import config as cfg
from pucit.util import fail, info, ok, which

bypass_app = typer.Typer(help="Campus internet bypass (wraps bypass-pucit).")


def _bypass_argv() -> list:
    binary = which("bypass_pucit")
    if binary:
        return [binary]
    # fallback: python -m bypass_pucit
    return [shutil.which("python3") or shutil.which("python") or "python3", "-m", "bypass_pucit"]


@bypass_app.command("set")
def bypass_set(
    proxy: Optional[str] = typer.Option(
        None, "--proxy", "-p", help="Proxy URL (default from config / bypass-pucit)"
    ),
) -> None:
    """Apply campus proxy settings via bypass_pucit."""
    argv = _bypass_argv() + ["set"]
    proxy_url = proxy or str(cfg.get("proxy"))
    if proxy_url:
        argv.extend(["--proxy", proxy_url])
    info(" ".join(argv))
    result = subprocess.run(argv)
    if result.returncode == 0:
        ok("Proxy applied")
    else:
        fail("bypass_pucit set failed")
    raise typer.Exit(result.returncode)


@bypass_app.command("unset")
def bypass_unset() -> None:
    """Remove campus proxy settings."""
    argv = _bypass_argv() + ["unset"]
    info(" ".join(argv))
    result = subprocess.run(argv)
    if result.returncode == 0:
        ok("Proxy removed")
    else:
        fail("bypass_pucit unset failed")
    raise typer.Exit(result.returncode)

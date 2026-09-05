"""Campus proxy — bundled bypass_pucit (no separate package)."""

from __future__ import annotations

from typing import Optional

import typer

from pucit import config as cfg
from pucit.util import fail, info, ok

bypass_app = typer.Typer(help="Campus internet bypass (bundled).")


@bypass_app.command("set")
def bypass_set(
    proxy: Optional[str] = typer.Option(
        None, "--proxy", "-p", help="Proxy URL (default from config)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Detailed progress"),
) -> None:
    """Apply campus proxy settings."""
    from bypass_pucit.cli import main as bypass_main

    argv = ["set"]
    proxy_url = proxy or str(cfg.get("proxy") or "")
    if proxy_url:
        argv.extend(["--proxy", proxy_url])
    if verbose:
        argv.append("--verbose")
    info("bypass set " + " ".join(argv[1:]))
    code = bypass_main(argv)
    if code == 0:
        ok("Proxy applied")
    else:
        fail("Proxy set failed")
    raise typer.Exit(code if code is not None else 0)


@bypass_app.command("unset")
def bypass_unset(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Detailed progress"),
) -> None:
    """Remove campus proxy settings."""
    from bypass_pucit.cli import main as bypass_main

    argv = ["unset"]
    if verbose:
        argv.append("--verbose")
    info("bypass unset")
    code = bypass_main(argv)
    if code == 0:
        ok("Proxy removed")
    else:
        fail("Proxy unset failed")
    raise typer.Exit(code if code is not None else 0)

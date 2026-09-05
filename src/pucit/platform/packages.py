"""OS package installation adapters."""

from __future__ import annotations

from typing import List, Sequence

from pucit.util import detect_pkg_manager, fail, info, is_windows, ok, run_cmd, which


class PackageError(RuntimeError):
    pass


def install_packages(packages: Sequence[str], *, title: str = "packages") -> int:
    packages = [p for p in packages if p]
    if not packages:
        ok(f"Nothing to install for {title}")
        return 0

    manager = detect_pkg_manager()
    if not manager:
        raise PackageError(
            "No supported package manager found "
            "(need dnf/apt on Linux, or winget/choco on Windows)."
        )

    info(f"Installing {title} via {manager}: {', '.join(packages)}")
    argv = _install_argv(manager, packages)
    result = run_cmd(argv)
    if result.returncode == 0:
        ok(f"Installed {title}")
    else:
        fail(f"Failed to install {title} (exit {result.returncode})")
    return result.returncode


def _install_argv(manager: str, packages: Sequence[str]) -> List[str]:
    pkgs = list(packages)
    if manager == "dnf":
        return ["sudo", "dnf", "install", "-y", *pkgs]
    if manager in ("apt", "apt-get"):
        # refresh quietly then install
        run_cmd(["sudo", "apt-get", "update"], capture=True)
        return ["sudo", "apt-get", "install", "-y", *pkgs]
    if manager == "pacman":
        return ["sudo", "pacman", "-S", "--noconfirm", *pkgs]
    if manager == "zypper":
        return ["sudo", "zypper", "install", "-y", *pkgs]
    if manager == "winget":
        # winget installs one id at a time typically
        return ["winget", "install", "--accept-package-agreements", "--accept-source-agreements", pkgs[0]]
    if manager == "choco":
        return ["choco", "install", "-y", *pkgs]
    raise PackageError(f"Unsupported package manager: {manager}")


def pf_packages() -> List[str]:
    if is_windows():
        # Prefer winget package id when winget is present
        if which("winget"):
            return ["mingw-w64"]  # may vary; doctor still verifies g++
        return ["mingw"]
    manager = detect_pkg_manager()
    if manager == "dnf":
        return ["gcc-c++", "make", "gdb", "cmake"]
    if manager in ("apt", "apt-get"):
        return ["build-essential", "g++", "make", "gdb", "cmake"]
    if manager == "pacman":
        return ["base-devel", "gdb", "cmake"]
    if manager == "zypper":
        return ["gcc-c++", "make", "gdb", "cmake"]
    return ["g++", "make", "gdb", "cmake"]


def docker_packages() -> List[str]:
    if is_windows():
        if which("winget"):
            return ["Docker.DockerDesktop"]
        return ["docker-desktop"]
    manager = detect_pkg_manager()
    if manager == "dnf":
        return ["docker"]
    if manager in ("apt", "apt-get"):
        return ["docker.io"]
    if manager == "pacman":
        return ["docker"]
    if manager == "zypper":
        return ["docker"]
    return ["docker"]

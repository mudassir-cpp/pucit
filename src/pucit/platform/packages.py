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
    if manager == "winget":
        # winget installs one package id at a time
        code = 0
        for pkg in packages:
            argv = [
                "winget",
                "install",
                "--accept-package-agreements",
                "--accept-source-agreements",
                pkg,
            ]
            info(f"  winget install {pkg}")
            result = run_cmd(argv)
            if result.returncode != 0:
                fail(f"Failed to install {pkg} (exit {result.returncode})")
                code = result.returncode
                break
        if code == 0:
            ok(f"Installed {title}")
        return code

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
        run_cmd(["sudo", "apt-get", "update"], capture=True)
        return ["sudo", "apt-get", "install", "-y", *pkgs]
    if manager == "pacman":
        return ["sudo", "pacman", "-S", "--noconfirm", *pkgs]
    if manager == "zypper":
        return ["sudo", "zypper", "install", "-y", *pkgs]
    if manager == "choco":
        return ["choco", "install", "-y", *pkgs]
    if manager == "winget":
        return ["winget", "install", "--accept-package-agreements", "--accept-source-agreements", pkgs[0]]
    raise PackageError(f"Unsupported package manager: {manager}")


def pf_packages() -> List[str]:
    if is_windows():
        if which("winget"):
            # WinLibs MinGW-w64 ships gcc, g++, mingw32-make
            return ["BrechtSanders.WinLibs.POSIX.UCRT"]
        return ["mingw"]
    manager = detect_pkg_manager()
    if manager == "dnf":
        return ["gcc", "gcc-c++", "make", "gdb", "cmake"]
    if manager in ("apt", "apt-get"):
        return ["build-essential", "gcc", "g++", "make", "gdb", "cmake"]
    if manager == "pacman":
        return ["base-devel", "gdb", "cmake"]
    if manager == "zypper":
        return ["gcc", "gcc-c++", "make", "gdb", "cmake"]
    return ["gcc", "g++", "make", "gdb", "cmake"]


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

from __future__ import annotations

from typer.testing import CliRunner

from pucit.cli import app
from pucit.commands.scaffold import init_project, new_file
from pucit.platform.packages import pf_packages

runner = CliRunner()


def test_new_and_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    new_file("hello")
    assert (tmp_path / "hello.cpp").exists()
    init_project()
    assert (tmp_path / "main.cpp").exists()
    assert (tmp_path / "Makefile").exists()


def test_init_c(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_project(lang="c")
    assert (tmp_path / "main.c").exists()
    assert (tmp_path / "Makefile").exists()
    makefile = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert "gcc" in makefile
    assert "main.c" in makefile


def test_new_c_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    new_file("hello.c")
    assert (tmp_path / "hello.c").exists()
    text = (tmp_path / "hello.c").read_text(encoding="utf-8")
    assert "stdio.h" in text


def test_cli_init_c(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "c"])
    assert result.exit_code == 0
    assert (tmp_path / "main.c").exists()


def test_bypass_help():
    result = runner.invoke(app, ["bypass", "--help"])
    assert result.exit_code == 0
    assert "set" in result.stdout
    assert "unset" in result.stdout
    assert "bundled" in result.stdout.lower() or "bypass" in result.stdout.lower()


def test_bypass_bundled_import():
    import bypass_pucit
    from bypass_pucit.__about__ import __version__

    assert __version__
    assert bypass_pucit.DEFAULT_PROXY


def test_install_help():
    result = runner.invoke(app, ["install", "--help"])
    assert result.exit_code == 0
    assert "oracle" in result.stdout
    assert "pf" in result.stdout


def test_pf_packages_windows_winget(monkeypatch):
    monkeypatch.setattr("pucit.platform.packages.is_windows", lambda: True)
    monkeypatch.setattr("pucit.platform.packages.which", lambda name: "winget" if name == "winget" else None)
    pkgs = pf_packages()
    assert pkgs == ["BrechtSanders.WinLibs.POSIX.UCRT"]

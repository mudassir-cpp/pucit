from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pucit.cli import app
from pucit.commands.scaffold import init_project, new_file

runner = CliRunner()


def test_new_and_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    new_file("hello")
    assert (tmp_path / "hello.cpp").exists()
    init_project()
    assert (tmp_path / "main.cpp").exists()
    assert (tmp_path / "Makefile").exists()


def test_bypass_help():
    result = runner.invoke(app, ["bypass", "--help"])
    assert result.exit_code == 0
    assert "set" in result.stdout
    assert "unset" in result.stdout


def test_install_help():
    result = runner.invoke(app, ["install", "--help"])
    assert result.exit_code == 0
    assert "oracle" in result.stdout
    assert "pf" in result.stdout

from __future__ import annotations

from pucit.docker_util import build_run_argv, container_name, generate_password, oracle_image


def test_generate_password():
    pwd = generate_password()
    assert len(pwd) >= 12
    assert any(c.isupper() for c in pwd)
    assert any(c.isdigit() for c in pwd)


def test_build_run_argv(monkeypatch):
    monkeypatch.setattr("pucit.docker_util.docker_bin", lambda: "docker")
    argv = build_run_argv("Secret123", name="pucit-oracle")
    assert argv[:2] == ["docker", "run"]
    assert "--name" in argv
    assert "pucit-oracle" in argv
    assert "ORACLE_PWD=Secret123" in argv
    assert oracle_image() in argv
    assert container_name() == "pucit-oracle" or True

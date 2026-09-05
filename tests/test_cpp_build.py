from __future__ import annotations

from pathlib import Path

from pucit.cpp_build import binary_path, build_compile_argv, resolve_sources


def test_resolve_main(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "main.cpp").write_text("int main(){return 0;}\n")
    sources = resolve_sources([])
    assert sources[0].name == "main.cpp"


def test_build_compile_argv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "main.cpp"
    src.write_text("int main(){return 0;}\n")
    out = binary_path([src])
    argv = build_compile_argv([src], out, std="c++17", extra_flags=["-Wall"])
    assert argv[0]  # compiler present on this machine
    assert "-std=c++17" in argv
    assert "-Wall" in argv
    assert "-o" in argv
    assert str(out) in argv
    assert str(src) in argv


def test_execute_run(tmp_path, monkeypatch):
    from pucit.cpp_build import execute_run

    monkeypatch.chdir(tmp_path)
    (tmp_path / "main.cpp").write_text(
        '#include <iostream>\nint main(){std::cout<<"hi\\n";return 0;}\n'
    )
    code = execute_run(["main.cpp"])
    assert code == 0
    assert (tmp_path / "build").exists()

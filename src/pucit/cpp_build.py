"""Compile and run C / C++ sources for PF labs."""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Literal, Optional, Sequence, Tuple

from pucit import config as cfg
from pucit.util import (
    fail,
    first_existing,
    info,
    is_windows,
    ok,
    run_cmd,
    run_streaming,
    split_flags,
    warn,
)

Lang = Literal["c", "cpp"]

CPP_EXTS = {".cpp", ".cc", ".cxx", ".c++"}
C_EXTS = {".c"}
ALL_EXTS = CPP_EXTS | C_EXTS


def find_cxx_compiler() -> Optional[str]:
    return first_existing(("g++", "clang++", "c++"))


def find_c_compiler() -> Optional[str]:
    return first_existing(("gcc", "clang", "cc"))


def find_compiler() -> Optional[str]:
    """Prefer C++ compiler for doctor / which; fall back to C."""
    return find_cxx_compiler() or find_c_compiler()


def detect_lang(sources: Sequence[Path]) -> Lang:
    if not sources:
        return "cpp"
    if any(p.suffix.lower() in C_EXTS for p in sources):
        if any(p.suffix.lower() in CPP_EXTS for p in sources):
            raise RuntimeError("Mix of .c and .cpp sources is not supported in one command")
        return "c"
    return "cpp"


def default_std(lang: Lang) -> str:
    if lang == "c":
        return str(cfg.get("c_std", "c17"))
    return str(cfg.get("cxx_std", "c++17"))


def default_extra_flags(lang: Lang) -> List[str]:
    key = "c_flags" if lang == "c" else "cxx_flags"
    return split_flags(str(cfg.get(key, "-Wall -Wextra -O0")))


def resolve_sources(sources: Sequence[str]) -> List[Path]:
    if not sources:
        cwd = Path.cwd()
        for name in ("main.cpp", "main.c"):
            main = cwd / name
            if main.exists():
                return [main]
        lab_files = sorted(p for p in cwd.iterdir() if p.is_file() and p.suffix.lower() in ALL_EXTS)
        if len(lab_files) == 1:
            return lab_files
        if not lab_files:
            raise FileNotFoundError("No .c/.cpp files found. Pass a file: pucit run main.cpp")
        raise FileNotFoundError(
            "Multiple source files found. Pass one or more explicitly, e.g. pucit run main.cpp util.cpp"
        )

    resolved: List[Path] = []
    for item in sources:
        path = Path(item)
        if path.is_dir():
            for name in ("main.cpp", "main.c"):
                main = path / name
                if main.exists():
                    resolved.append(main.resolve())
                    break
            else:
                raise FileNotFoundError(f"No main.cpp or main.c in directory: {path}")
            continue
        if not path.exists():
            raise FileNotFoundError(f"Source not found: {path}")
        resolved.append(path.resolve())
    return resolved


def binary_path(sources: Sequence[Path], out: Optional[str] = None) -> Path:
    if out:
        return Path(out).resolve()
    stem = sources[0].stem
    build_dir = Path.cwd() / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    name = f"{stem}.exe" if is_windows() else stem
    return (build_dir / name).resolve()


def build_compile_argv(
    sources: Sequence[Path],
    output: Path,
    *,
    std: Optional[str] = None,
    extra_flags: Optional[Sequence[str]] = None,
    debug: bool = False,
) -> List[str]:
    lang = detect_lang(sources)
    if lang == "c":
        compiler = find_c_compiler()
        if not compiler:
            raise RuntimeError("No C compiler found. Run: pucit install pf")
    else:
        compiler = find_cxx_compiler()
        if not compiler:
            raise RuntimeError("No C++ compiler found. Run: pucit install pf")

    argv: List[str] = [compiler, f"-std={std or default_std(lang)}"]
    flags = list(extra_flags) if extra_flags is not None else default_extra_flags(lang)
    argv.extend(flags)
    if debug and "-g" not in argv:
        argv.append("-g")
    argv.extend(["-o", str(output)])
    argv.extend(str(src) for src in sources)
    return argv


def compile_sources(
    sources: Sequence[Path],
    *,
    out: Optional[str] = None,
    flags: Optional[str] = None,
    std: Optional[str] = None,
    debug: bool = False,
) -> Tuple[int, Path, List[str]]:
    output = binary_path(sources, out)
    extra = split_flags(flags) if flags is not None else None
    argv = build_compile_argv(sources, output, std=std, extra_flags=extra, debug=debug)
    info(" ".join(argv))
    result = run_cmd(argv, capture=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    if result.returncode == 0:
        ok(f"Built {output}")
    else:
        fail("Compile failed")
    return result.returncode, output, argv


def run_binary(binary: Path, args: Sequence[str]) -> int:
    argv = [str(binary), *args]
    info("Running: " + " ".join(argv))
    return run_streaming(argv)


def run_with_input_file(binary: Path, args: Sequence[str], input_file: str) -> int:
    import subprocess

    with open(input_file, "r", encoding="utf-8") as handle:
        proc = subprocess.Popen([str(binary), *args], stdin=handle)
        return proc.wait()


def execute_run(
    sources: Sequence[str],
    *,
    prog_args: Sequence[str] = (),
    flags: Optional[str] = None,
    std: Optional[str] = None,
    out: Optional[str] = None,
    input_file: Optional[str] = None,
    compile_only: bool = False,
    debug: bool = False,
) -> int:
    resolved = resolve_sources(sources)
    code, binary, _ = compile_sources(
        resolved, out=out, flags=flags, std=std, debug=debug
    )
    if code != 0:
        return code
    if compile_only:
        return 0
    if input_file:
        return run_with_input_file(binary, prog_args, input_file)
    return run_binary(binary, prog_args)


def watch_run(
    sources: Sequence[str],
    *,
    prog_args: Sequence[str] = (),
    flags: Optional[str] = None,
    std: Optional[str] = None,
    out: Optional[str] = None,
    input_file: Optional[str] = None,
    interval: float = 1.0,
) -> int:
    resolved = resolve_sources(sources)
    last_mtime = -1.0
    info(f"Watching {[str(p) for p in resolved]} (Ctrl+C to stop)")
    try:
        while True:
            mtime = max(p.stat().st_mtime for p in resolved)
            if mtime != last_mtime:
                last_mtime = mtime
                print()
                execute_run(
                    [str(p) for p in resolved],
                    prog_args=prog_args,
                    flags=flags,
                    std=std,
                    out=out,
                    input_file=input_file,
                )
            time.sleep(interval)
    except KeyboardInterrupt:
        warn("Watch stopped")
        return 0


def clean_artifacts() -> List[Path]:
    removed: List[Path] = []
    cwd = Path.cwd()
    candidates = [cwd / "a.out", cwd / "a.exe"]
    build = cwd / "build"
    if build.exists() and build.is_dir():
        for path in build.iterdir():
            if path.is_file():
                path.unlink()
                removed.append(path)
        try:
            build.rmdir()
            removed.append(build)
        except OSError:
            pass
    for path in candidates:
        if path.exists():
            path.unlink()
            removed.append(path)
    return removed

"""Scaffold helpers: new / init."""

from __future__ import annotations

from pathlib import Path

import typer

from pucit.util import fail, ok, warn

MAIN_TEMPLATE = """#include <iostream>
using namespace std;

int main() {
    cout << "Hello, PUCIT!" << endl;
    return 0;
}
"""

MAKEFILE_TEMPLATE = """CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O0
TARGET = build/main

all: $(TARGET)

$(TARGET): main.cpp
\tmkdir -p build
\t$(CXX) $(CXXFLAGS) -o $(TARGET) main.cpp

run: $(TARGET)
\t./$(TARGET)

clean:
\trm -rf build a.out
"""

GITIGNORE_TEMPLATE = """build/
a.out
*.exe
*.o
.idea/
.vscode/
"""


def write_file(path: Path, content: str, force: bool = False) -> bool:
    if path.exists() and not force:
        warn(f"Skip existing {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    ok(f"Created {path}")
    return True


def new_file(name: str, force: bool = False) -> None:
    stem = name
    if stem.endswith((".cpp", ".cc", ".cxx")):
        path = Path(stem)
    else:
        path = Path(f"{stem}.cpp")
    body = MAIN_TEMPLATE.replace("Hello, PUCIT!", f"Hello from {path.stem}!")
    if not write_file(path, body, force=force):
        raise typer.Exit(1)


def init_project(force: bool = False) -> None:
    write_file(Path("main.cpp"), MAIN_TEMPLATE, force=force)
    write_file(Path("Makefile"), MAKEFILE_TEMPLATE, force=force)
    write_file(Path(".gitignore"), GITIGNORE_TEMPLATE, force=force)
    ok("PF lab ready. Try: pucit run main.cpp")

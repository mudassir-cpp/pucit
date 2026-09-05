"""Scaffold helpers: new / init for C and C++."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import typer

from pucit.util import fail, ok, warn

Lang = Literal["c", "cpp"]

CPP_TEMPLATE = """#include <iostream>
using namespace std;

int main() {
    cout << "Hello, PUCIT!" << endl;
    return 0;
}
"""

C_TEMPLATE = """#include <stdio.h>

int main(void) {
    printf("Hello, PUCIT!\\n");
    return 0;
}
"""

CPP_MAKEFILE = """CXX = g++
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

C_MAKEFILE = """CC = gcc
CFLAGS = -std=c17 -Wall -Wextra -O0
TARGET = build/main

all: $(TARGET)

$(TARGET): main.c
\tmkdir -p build
\t$(CC) $(CFLAGS) -o $(TARGET) main.c

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


def normalize_lang(lang: str) -> Lang:
    key = lang.strip().lower()
    if key in {"c", "cc"}:
        return "c"
    if key in {"cpp", "c++", "cxx", "pf"}:
        return "cpp"
    fail(f"Unknown language '{lang}'. Use: c or cpp")
    raise typer.Exit(1)


def new_file(name: str, force: bool = False, lang: Optional[str] = None) -> None:
    lower = name.lower()
    if lower.endswith((".c",)):
        chosen: Lang = "c"
        path = Path(name if name.endswith(".c") else f"{Path(name).stem}.c")
    elif lower.endswith((".cpp", ".cc", ".cxx")):
        chosen = "cpp"
        path = Path(name)
    elif lang:
        chosen = normalize_lang(lang)
        path = Path(f"{name}.c" if chosen == "c" else f"{name}.cpp")
    else:
        chosen = "cpp"
        path = Path(f"{name}.cpp")

    template = C_TEMPLATE if chosen == "c" else CPP_TEMPLATE
    body = template.replace("Hello, PUCIT!", f"Hello from {path.stem}!")
    if not write_file(path, body, force=force):
        raise typer.Exit(1)


def init_project(force: bool = False, lang: str = "cpp") -> None:
    chosen = normalize_lang(lang)
    if chosen == "c":
        write_file(Path("main.c"), C_TEMPLATE, force=force)
        write_file(Path("Makefile"), C_MAKEFILE, force=force)
        write_file(Path(".gitignore"), GITIGNORE_TEMPLATE, force=force)
        ok("C lab ready. Try: pucit run main.c")
    else:
        write_file(Path("main.cpp"), CPP_TEMPLATE, force=force)
        write_file(Path("Makefile"), CPP_MAKEFILE, force=force)
        write_file(Path(".gitignore"), GITIGNORE_TEMPLATE, force=force)
        ok("C++ lab ready. Try: pucit run main.cpp")

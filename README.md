# pucit

PUCIT student toolkit CLI — local Oracle for labs (Docker), PF C/C++ essentials, campus proxy bypass, and compile/run in one command.

```bash
pip install pucit
# or from source:
pip install -e ".[dev]"
```

## Quick start

```bash
pucit doctor
pucit install pf
pucit init          # or: pucit init c
pucit run main.cpp
```

## Commands

### C / C++ labs

| Command | What it does |
|---|---|
| `pucit run main.cpp` | Compile with `g++` into `build/`, then run |
| `pucit run main.c` | Compile with `gcc` into `build/`, then run |
| `pucit compile …` | Compile only |
| `pucit debug …` | Compile with `-g` and open `gdb` |
| `pucit watch …` | Recompile + run on save |
| `pucit clean` | Remove `build/` and `a.out` |
| `pucit new hello` | Create `hello.cpp` |
| `pucit new hello.c` | Create `hello.c` |
| `pucit init` | Scaffold C++ lab (`main.cpp` + Makefile) |
| `pucit init c` | Scaffold C lab (`main.c` + Makefile) |
| `pucit init cpp` | Same as `pucit init` |

Extras:

```bash
pucit run main.cpp util.cpp
pucit run main.cpp -f "-O2 -std=c++20"
pucit run main.c -i input.txt
```

### Local Oracle (for labs / DBeaver)

```bash
pucit install oracle      # installs/starts Docker if needed, then creates local DB
pucit start oracle
pucit stop oracle
pucit status oracle
pucit logs oracle
pucit oracle connect      # Host/Port/User for DBeaver + sqlplus
pucit oracle rm
```

Uses Oracle Database Free image as container `pucit-oracle` on port `1521`. Password is saved under `~/.config/pucit/oracle.env` (Windows: `%APPDATA%\pucit\oracle.env`).

`pucit oracle connect` prints fields you can paste into **DBeaver** (New Connection → Oracle → Basic): Host `localhost`, Port `1521`, Database `FREEPDB1`, User `system`.

If Docker Desktop is installed but not running (common on Windows), `install oracle` tries to start it and waits. If that fails, open Docker Desktop manually, wait until it says Running, then retry.

If image pull fails with auth errors, accept the license on [Oracle Container Registry](https://container-registry.oracle.com/), then `docker login container-registry.oracle.com` and retry.

### Tooling / campus net

```bash
pucit install pf          # gcc, g++, make, gdb, cmake (WinLibs on Windows)
pucit install docker
pucit install sqlclient   # Instant Client / sqlplus guidance
pucit bypass set
pucit bypass unset
pucit doctor
pucit list
pucit which g++
pucit open .
```

## Supported OS

Linux (dnf/apt/…) and Windows (winget/choco) for installers. `run` / `compile` work anywhere `gcc`/`g++` (or clang) is available.

On Windows after `pucit install pf`, **open a new terminal** so WinLibs is on PATH, then `pucit doctor`.

## Development / CI

```bash
pip install -e ".[dev]"
pytest -q
```

GitHub Actions:

- **CI** (`.github/workflows/ci.yml`) — tests on Linux + Windows for Python 3.10–3.13
- **Publish** (`.github/workflows/publish.yml`) — uploads to PyPI on GitHub Release (Trusted Publisher / OIDC)

### First PyPI publish

1. On PyPI → **Publishing** → add a **pending trusted publisher**:
   - Project: `pucit`
   - Owner: `mudassir-cpp`
   - Repo: `pucit`
   - Workflow: `publish.yml`
   - Environment: `pypi`
2. On GitHub → **Settings → Environments → New** → name it `pypi` (optional approval rule recommended).
3. Create a Release (e.g. tag `v0.1.0`) — the publish workflow runs and creates the PyPI project.

## License

MIT — see `LICENSE.txt`.

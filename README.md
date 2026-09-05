# pucit

PUCIT student toolkit CLI — install Oracle (Docker), set up PF/C++ essentials, campus proxy bypass, and compile/run lab code in one command.

```bash
pip install pucit
# or from source:
pip install -e ".[dev]"
```

## Quick start

```bash
pucit doctor
pucit install pf
pucit run main.cpp
```

## Commands

### C++ labs (ease)

| Command | What it does |
|---|---|
| `pucit run main.cpp` | Compile with `g++` into `build/`, then run — no `./a.out` |
| `pucit compile main.cpp` | Compile only |
| `pucit debug main.cpp` | Compile with `-g` and open `gdb` |
| `pucit watch main.cpp` | Recompile + run on save |
| `pucit clean` | Remove `build/` and `a.out` |
| `pucit new hello` | Create `hello.cpp` from template |
| `pucit init` | Scaffold `main.cpp` + `Makefile` + `.gitignore` |

Extras:

```bash
pucit run main.cpp util.cpp
pucit run main.cpp -f "-O2 -std=c++20"
pucit run main.cpp -i input.txt
```

### Oracle (Docker)

```bash
pucit install oracle
pucit start oracle
pucit stop oracle
pucit status oracle
pucit logs oracle
pucit oracle connect
pucit oracle rm
```

Uses Oracle Database Free image `container-registry.oracle.com/database/free:latest` as container `pucit-oracle` on port `1521`. Password is saved under `~/.config/pucit/oracle.env`.

If pull fails with auth errors, accept the license on [Oracle Container Registry](https://container-registry.oracle.com/), then `docker login container-registry.oracle.com` and retry.

### Tooling / campus net

```bash
pucit install pf          # g++, make, gdb, cmake
pucit install docker
pucit install sqlclient   # Instant Client / sqlplus guidance
pucit bypass set          # wraps bypass-pucit
pucit bypass unset
pucit doctor
pucit list
pucit which g++
pucit open .
```

## Supported OS

Linux (dnf/apt/…) and Windows (winget/choco) for installers. `run` / `compile` work anywhere `g++` or `clang++` is available.

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

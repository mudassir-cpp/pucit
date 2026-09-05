# pucit

**CLI toolkit for [PUCIT](https://pucit.edu.pk) students** — Programming Fundamentals (C/C++), local Oracle for DB labs, campus proxy, and one-command checks.

```bash
pip install pucit
pucit doctor
```

Built by students, for students. Works on **Linux** and **Windows**.

---

## Why this exists

Lab setup should not take longer than the lab itself. `pucit` helps you:

| Need | Command |
|---|---|
| Install compiler tools | `pucit install pf` |
| Start a lab folder | `pucit init` or `pucit init c` |
| Compile & run without `./a.out` | `pucit run main.cpp` |
| Local Oracle for DB labs / DBeaver | `pucit install oracle` |
| Campus terminal internet (proxy) | `pucit bypass set` |
| See what’s missing | `pucit doctor` |

---

## Install

**Requirements:** Python 3.8+

```bash
pip install -U pucit
```

Check your machine:

```bash
pucit doctor
```

Upgrade later:

```bash
pip install -U pucit
```

---

## Quick start (PF / C++ or C)

```bash
pucit install pf          # gcc, g++, make, … (WinLibs on Windows)
pucit init                # C++ lab: main.cpp + Makefile
# or:  pucit init c       # C lab: main.c + Makefile
pucit run main.cpp
```

**Windows:** after `install pf`, **open a new terminal** so the compiler is on PATH, then run `pucit doctor` again.

### C / C++ commands

| Command | What it does |
|---|---|
| `pucit run main.cpp` | Compile with `g++` → `build/`, then run |
| `pucit run main.c` | Compile with `gcc` → `build/`, then run |
| `pucit compile …` | Compile only |
| `pucit debug …` | Compile with `-g`, open `gdb` |
| `pucit watch …` | Recompile + run on save |
| `pucit clean` | Remove `build/` and `a.out` |
| `pucit new hello` | Create `hello.cpp` |
| `pucit new hello.c` | Create `hello.c` |
| `pucit init` / `pucit init cpp` | Scaffold C++ lab |
| `pucit init c` | Scaffold C lab |

```bash
pucit run main.cpp util.cpp
pucit run main.cpp -f "-O2 -std=c++20"
pucit run main.c -i input.txt
```

---

## Oracle labs (local DB + DBeaver)

You get a **local** Oracle Free database in Docker — good for practice and connecting from **DBeaver** / SQL Developer.

```bash
pucit install oracle      # installs/starts Docker if needed, then creates DB
pucit oracle connect      # print Host / Port / User / Password
pucit start oracle        # after reboot / stop
pucit stop oracle
pucit status oracle
pucit logs oracle
pucit oracle rm           # remove container
```

### Connect in DBeaver

1. Run `pucit oracle connect`
2. DBeaver → **New Connection** → **Oracle** → **Basic**
3. Paste:

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `1521` |
| Database / Service | `FREEPDB1` |
| Username | `system` |
| Password | *(shown by `pucit oracle connect`)* |

Password is stored in `~/.config/pucit/oracle.env` (Windows: `%APPDATA%\pucit\oracle.env`).

### Oracle tips

- First pull is **large** (several GB). Let `docker pull` finish; progress prints in the terminal.
- If Docker Desktop is installed but not running (Windows), `install oracle` tries to start it. If it still fails, open Docker Desktop, wait until it says **Running**, then retry.
- Auth / license errors: accept terms on [Oracle Container Registry](https://container-registry.oracle.com/), then:

  ```bash
  docker login container-registry.oracle.com
  pucit install oracle
  ```

- Container stopped? Connection details still print, but DBeaver will fail until `pucit start oracle`.

Optional SQL\*Plus:

```bash
pucit install sqlclient
pucit oracle connect -l
```

---

## Campus proxy (lab / hostel net)

Proxy helpers are **bundled** — you do **not** need a separate `pip install bypass-pucit`.

```bash
pucit bypass set          # apply campus proxy (may ask for sudo / admin)
pucit bypass unset        # remove
pucit bypass set -p http://172.16.0.6:8080
```

The `bypass_pucit` command is also installed for compatibility.

---

## Other useful commands

```bash
pucit install docker      # Docker Engine / Desktop
pucit list                # component status
pucit which g++
pucit which gcc
pucit open .              # open folder in Cursor / VS Code
pucit version
```

---

## Troubleshooting

| Problem | What to try |
|---|---|
| `g++` / `gcc` not found after install (Windows) | New terminal; confirm WinLibs on PATH; `pucit doctor` |
| `winget` “No package found” | Update `pucit` (`pip install -U pucit`); we use WinLibs package id |
| Docker found but not usable | Start Docker Desktop / `sudo systemctl start docker` |
| Oracle pull looks stuck | Large image — wait for layer progress (v0.1.2+) |
| DBeaver can’t connect | `pucit status oracle` → `pucit start oracle` |
| Proxy needs root | Normal — `bypass set` elevates on Linux/Windows |

Still stuck? Open an [issue](https://github.com/mudassir-cpp/pucit/issues) with `pucit doctor` output (paste text, not screenshots of secrets if any).

---

## Contributing (PUCIT students welcome)

You do **not** need to be a maintainer. Good first contributions:

- Fix Windows / Linux install edge cases
- Clearer doctor messages
- Docs / README typos (especially lab steps)
- Small features that help **your** course (PF, OOP, DB)
- Tests for bugs you hit

### How to contribute

1. **Fork** [mudassir-cpp/pucit](https://github.com/mudassir-cpp/pucit) and clone your fork.
2. Create a branch:

   ```bash
   git checkout -b fix/short-description
   ```

3. Set up a editable install:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

4. Make changes. Keep them focused (one problem per PR).
5. Run tests:

   ```bash
   pytest -q
   pucit doctor
   ```

6. Commit with a clear message, push, and open a **Pull Request** to `main`.

### PR checklist

- [ ] `pytest -q` passes
- [ ] README / help text updated if commands changed
- [ ] No secrets (passwords, tokens) committed
- [ ] Describe *why* (what lab / OS / error you hit)

### Code layout

```
src/pucit/           # main CLI (Typer)
src/bypass_pucit/    # bundled campus proxy (vendored)
tests/               # pytest
.github/workflows/   # CI + PyPI publish
run.sh               # maintainer release helper
```

Questions? Open a Discussion/Issue, or ping via the repo.

---

## Development & release (maintainers)

```bash
pip install -e ".[dev]"
pytest -q
```

**CI:** Linux + Windows, Python 3.10–3.13 (`.github/workflows/ci.yml`).

**Publish to PyPI:** on GitHub Release via Trusted Publisher (`.github/workflows/publish.yml`).

```bash
./run.sh          # bump patch, commit, tag, push, create Release
./run.sh 0.2.0    # set exact version
```

PyPI: [pypi.org/project/pucit](https://pypi.org/project/pucit/)

---

## License

MIT — see [`LICENSE.txt`](LICENSE.txt).

Campus proxy code under `src/bypass_pucit/` is also MIT (from [bypass_pucit](https://github.com/mudassir-cpp/bypass_pucit)), vendored into this project so students install **one** package.

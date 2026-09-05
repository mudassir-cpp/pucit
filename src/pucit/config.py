"""Simple JSON config stored under the user config dir."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from pucit.util import config_dir

DEFAULTS: Dict[str, Any] = {
    "cxx_std": "c++17",
    "c_std": "c17",
    "cxx_flags": "-Wall -Wextra -O0",
    "c_flags": "-Wall -Wextra -O0",
    "proxy": "http://172.16.0.6:8080",
    "oracle_image": "container-registry.oracle.com/database/free:latest",
    "oracle_container": "pucit-oracle",
    "oracle_port": 1521,
}


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> Dict[str, Any]:
    path = config_path()
    data = dict(DEFAULTS)
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save_config(data: Dict[str, Any]) -> None:
    path = config_path()
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def get(key: str, default: Any = None) -> Any:
    cfg = load_config()
    return cfg.get(key, DEFAULTS.get(key, default))

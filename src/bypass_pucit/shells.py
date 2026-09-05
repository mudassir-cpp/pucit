import os
import ntpath
from pathlib import Path


def _normalize_shell_name(shell_value):
    shell_name = ntpath.basename(shell_value or "").lower()
    if shell_name in {"pwsh", "powershell.exe", "powershell"}:
        return "powershell"
    return shell_name


def detect_shell_name(sudo_user=None, shell_value=None, user_shell=None):
    if user_shell:
        return _normalize_shell_name(user_shell)
    if sudo_user and shell_value:
        return _normalize_shell_name(shell_value)
    return _normalize_shell_name(shell_value or os.environ.get("SHELL", ""))


def shell_profile_path(home_dir, shell_name):
    shell_name = _normalize_shell_name(shell_name)
    if shell_name == "zsh":
        return home_dir / ".zshrc"
    if shell_name == "bash":
        return home_dir / ".bashrc"
    if shell_name == "fish":
        return home_dir / ".config" / "fish" / "config.fish"
    if shell_name == "xonsh":
        return home_dir / ".xonshrc"
    if shell_name == "powershell":
        return home_dir / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1"
    return home_dir / ".profile"

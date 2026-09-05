import os
import shutil
import subprocess
import sys


def is_linux_root():
    return hasattr(os, "geteuid") and os.geteuid() == 0


def relaunch_with_sudo(argv, launcher=os.execvp, sudo_path=None):
    sudo_binary = sudo_path or "sudo"
    if shutil.which(sudo_binary) is None:
        raise RuntimeError("sudo is not installed.")
    command = [sudo_binary, "-E", sys.executable, "-m", "bypass_pucit.main"]
    command.extend(argv)
    launcher(sudo_binary, command)
    return True


def is_windows_admin():
    if os.name != "nt":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_with_uac(argv):
    import ctypes

    parameters = subprocess.list2cmdline(["-m", "bypass_pucit.main"] + argv)
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, parameters, None, 1)
    if int(result) <= 32:
        raise RuntimeError("Windows elevation failed.")
    return True

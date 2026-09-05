import ctypes
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from ..messages import print_info
from ..shells import detect_shell_name, shell_profile_path
from ..tools import command_exists


class ProxyReport(object):
    def __init__(self):
        self.applied = []
        self.skipped = []

    def add_applied(self, item):
        if item not in self.applied:
            self.applied.append(item)

    def add_skipped(self, item):
        if item not in self.skipped:
            self.skipped.append(item)


class WindowsProxyManager(object):
    def __init__(self, proxy_url, runner=None, verbose=False):
        self.proxy_url = proxy_url
        self.runner = runner or subprocess.run
        self.verbose = verbose

    def _log(self, message):
        if self.verbose:
            print_info(message)

    def apply(self):
        report = ProxyReport()
        self._log("Applying Windows proxy settings.")
        self._configure_internet_settings(report)
        self._configure_environment(report)
        self._apply_powershell_profile(report)
        self._apply_wget(report)
        self._apply_maven(report)
        self._apply_gradle(report)
        self._apply_docker(report)
        self._apply_pnpm(report)
        self._configure_winhttp(report)
        self.broadcast_environment_change()
        return report

    def unset(self):
        report = ProxyReport()
        self._log("Removing Windows proxy settings.")
        self._clear_internet_settings(report)
        self._clear_environment(report)
        self._unset_powershell_profile(report)
        self._unset_wget(report)
        self._unset_maven(report)
        self._unset_gradle(report)
        self._unset_docker(report)
        self._unset_pnpm(report)
        self._clear_winhttp(report)
        self.broadcast_environment_change()
        return report

    def _run_reg(self, command, report, tool_name):
        if not command_exists("reg"):
            report.add_skipped(tool_name)
            return
        self.runner(command, check=True)
        report.add_applied(tool_name)

    def _configure_internet_settings(self, report):
        self._run_reg(
            [
                "reg",
                "add",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                "/v",
                "ProxyEnable",
                "/t",
                "REG_DWORD",
                "/d",
                "1",
                "/f",
            ],
            report,
            "internet-settings",
        )
        self._run_reg(
            [
                "reg",
                "add",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                "/v",
                "ProxyServer",
                "/t",
                "REG_SZ",
                "/d",
                self.proxy_url,
                "/f",
            ],
            report,
            "internet-settings",
        )
        self._run_reg(
            [
                "reg",
                "add",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                "/v",
                "ProxyOverride",
                "/t",
                "REG_SZ",
                "/d",
                "localhost;127.0.0.1;::1",
                "/f",
            ],
            report,
            "internet-settings",
        )

    def _clear_internet_settings(self, report):
        self._run_reg(
            [
                "reg",
                "add",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                "/v",
                "ProxyEnable",
                "/t",
                "REG_DWORD",
                "/d",
                "0",
                "/f",
            ],
            report,
            "internet-settings",
        )
        self._run_reg(
            [
                "reg",
                "delete",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                "/v",
                "ProxyServer",
                "/f",
            ],
            report,
            "internet-settings",
        )
        self._run_reg(
            [
                "reg",
                "delete",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                "/v",
                "ProxyOverride",
                "/f",
            ],
            report,
            "internet-settings",
        )

    def _configure_environment(self, report):
        commands = [
            ["reg", "add", r"HKCU\Environment", "/v", "HTTP_PROXY", "/t", "REG_SZ", "/d", self.proxy_url, "/f"],
            ["reg", "add", r"HKCU\Environment", "/v", "HTTPS_PROXY", "/t", "REG_SZ", "/d", self.proxy_url, "/f"],
            ["reg", "add", r"HKCU\Environment", "/v", "ALL_PROXY", "/t", "REG_SZ", "/d", self.proxy_url, "/f"],
            ["reg", "add", r"HKCU\Environment", "/v", "NO_PROXY", "/t", "REG_SZ", "/d", "localhost;127.0.0.1;::1", "/f"],
        ]
        for command in commands:
            self._run_reg(command, report, "environment")

    def _clear_environment(self, report):
        commands = [
            ["reg", "delete", r"HKCU\Environment", "/v", "HTTP_PROXY", "/f"],
            ["reg", "delete", r"HKCU\Environment", "/v", "HTTPS_PROXY", "/f"],
            ["reg", "delete", r"HKCU\Environment", "/v", "ALL_PROXY", "/f"],
            ["reg", "delete", r"HKCU\Environment", "/v", "NO_PROXY", "/f"],
        ]
        for command in commands:
            self._run_reg(command, report, "environment")

    def _proxy_host_port(self):
        parsed = urlparse(self.proxy_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return host, port

    def _user_home(self):
        return Path.home()

    def _detect_shell(self):
        return detect_shell_name(shell_value=os.environ.get("SHELL"))

    def _shell_profile(self):
        return shell_profile_path(self._user_home(), self._detect_shell())

    def _apply_powershell_profile(self, report):
        shell_name = self._detect_shell()
        if shell_name != "powershell":
            report.add_skipped("powershell")
            return
        profile_path = self._shell_profile()
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        self._log("Writing PowerShell profile: {0}".format(profile_path))
        profile_path.write_text(
            '$env:HTTP_PROXY = "{0}"\n'
            '$env:HTTPS_PROXY = "{0}"\n'
            '$env:ALL_PROXY = "{0}"\n'
            '$env:NO_PROXY = "localhost;127.0.0.1;::1"\n'.format(self.proxy_url)
        )
        report.add_applied("powershell")

    def _unset_powershell_profile(self, report):
        shell_name = self._detect_shell()
        if shell_name != "powershell":
            report.add_skipped("powershell")
            return
        profile_path = self._shell_profile()
        if profile_path.exists():
            self._log("Removing PowerShell profile: {0}".format(profile_path))
            profile_path.unlink()
            report.add_applied("powershell")

    def _wgetrc_path(self):
        return self._user_home() / ".wgetrc"

    def _apply_wget(self, report):
        self._wgetrc_path().write_text(
            "use_proxy = on\n"
            "http_proxy = {0}\n"
            "https_proxy = {0}\n".format(self.proxy_url)
        )
        report.add_applied("wget")

    def _unset_wget(self, report):
        wgetrc_path = self._wgetrc_path()
        if wgetrc_path.exists():
            wgetrc_path.unlink()
            report.add_applied("wget")

    def _maven_settings_path(self):
        return self._user_home() / ".m2" / "settings.xml"

    def _apply_maven(self, report):
        host, port = self._proxy_host_port()
        settings_path = self._maven_settings_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<settings>\n"
            "  <proxies>\n"
            "    <proxy>\n"
            "      <active>true</active>\n"
            "      <protocol>http</protocol>\n"
            "      <host>{0}</host>\n"
            "      <port>{1}</port>\n"
            "      <nonProxyHosts>localhost|127.0.0.1|::1</nonProxyHosts>\n"
            "    </proxy>\n"
            "    <proxy>\n"
            "      <active>true</active>\n"
            "      <protocol>https</protocol>\n"
            "      <host>{0}</host>\n"
            "      <port>{1}</port>\n"
            "      <nonProxyHosts>localhost|127.0.0.1|::1</nonProxyHosts>\n"
            "    </proxy>\n"
            "  </proxies>\n"
            "</settings>\n".format(host, port)
        )
        report.add_applied("maven")

    def _unset_maven(self, report):
        settings_path = self._maven_settings_path()
        if settings_path.exists():
            settings_path.unlink()
            report.add_applied("maven")

    def _gradle_properties_path(self):
        return self._user_home() / ".gradle" / "gradle.properties"

    def _apply_gradle(self, report):
        host, port = self._proxy_host_port()
        properties_path = self._gradle_properties_path()
        properties_path.parent.mkdir(parents=True, exist_ok=True)
        properties_path.write_text(
            "systemProp.http.proxyHost={0}\n"
            "systemProp.http.proxyPort={1}\n"
            "systemProp.https.proxyHost={0}\n"
            "systemProp.https.proxyPort={1}\n"
            "systemProp.http.nonProxyHosts=localhost|127.0.0.1|::1\n"
            "systemProp.https.nonProxyHosts=localhost|127.0.0.1|::1\n".format(host, port)
        )
        report.add_applied("gradle")

    def _unset_gradle(self, report):
        properties_path = self._gradle_properties_path()
        if properties_path.exists():
            properties_path.unlink()
            report.add_applied("gradle")

    def _docker_config_path(self):
        return self._user_home() / ".docker" / "config.json"

    def _apply_docker(self, report):
        config_path = self._docker_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(
                {
                    "proxies": {
                        "default": {
                            "httpProxy": self.proxy_url,
                            "httpsProxy": self.proxy_url,
                            "noProxy": "localhost,127.0.0.1,::1",
                        }
                    }
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        report.add_applied("docker")

    def _unset_docker(self, report):
        config_path = self._docker_config_path()
        if config_path.exists():
            config_path.unlink()
            report.add_applied("docker")

    def _apply_pnpm(self, report):
        if not command_exists("pnpm"):
            report.add_skipped("pnpm")
            return
        self.runner(["pnpm", "config", "set", "proxy", self.proxy_url], check=True)
        self.runner(["pnpm", "config", "set", "https-proxy", self.proxy_url], check=True)
        report.add_applied("pnpm")

    def _unset_pnpm(self, report):
        if not command_exists("pnpm"):
            report.add_skipped("pnpm")
            return
        self.runner(["pnpm", "config", "delete", "proxy"], check=True)
        self.runner(["pnpm", "config", "delete", "https-proxy"], check=True)
        report.add_applied("pnpm")

    def _configure_winhttp(self, report):
        if not command_exists("netsh"):
            report.add_skipped("winhttp")
            return
        self.runner(
            [
                "netsh",
                "winhttp",
                "set",
                "proxy",
                'proxy-server="{0}"'.format(self.proxy_url),
                'bypass-list="localhost;127.0.0.1;::1"',
            ],
            check=True,
        )
        report.add_applied("winhttp")

    def _clear_winhttp(self, report):
        if not command_exists("netsh"):
            report.add_skipped("winhttp")
            return
        self.runner(["netsh", "winhttp", "reset", "proxy"], check=True)
        report.add_applied("winhttp")

    def broadcast_environment_change(self):
        try:
            ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 1000, None)
        except Exception:
            pass

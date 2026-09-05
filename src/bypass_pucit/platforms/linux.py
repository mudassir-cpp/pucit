import os
import pwd
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from ..messages import print_info
from ..shells import detect_shell_name, shell_profile_path
from ..tools import command_exists, python_module_exists


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


class LinuxProxyManager(object):
    def __init__(self, proxy_url, runner=None, verbose=False):
        self.proxy_url = proxy_url
        self.runner = runner or subprocess.run
        self.verbose = verbose

    def _log(self, message):
        if self.verbose:
            print_info(message)

    def apply(self):
        report = ProxyReport()
        target_home = self._target_home()
        shell_rc = self._shell_rc_path(target_home)
        self._log("Detected shell profile: {0}".format(shell_rc))
        self._apply_shell_rc(shell_rc)
        report.add_applied(str(shell_rc))
        self._apply_environment_file(report)
        self._apply_git(report)
        self._apply_pip(target_home, report)
        self._apply_npm(report)
        self._apply_pnpm(report)
        self._apply_wget(target_home, report)
        self._apply_maven(target_home, report)
        self._apply_gradle(target_home, report)
        self._apply_docker(target_home, report)
        self._apply_apt(report)
        self._apply_yarn(report)
        self._apply_snap(report)
        print_info("Linux proxy settings were updated.")
        return report

    def unset(self):
        report = ProxyReport()
        target_home = self._target_home()
        shell_rc = self._shell_rc_path(target_home)
        self._log("Detected shell profile: {0}".format(shell_rc))
        self._remove_shell_rc(shell_rc)
        report.add_applied(str(shell_rc))
        self._unset_environment_file(report)
        self._unset_git(report)
        self._unset_pip(target_home, report)
        self._unset_npm(report)
        self._unset_pnpm(report)
        self._unset_wget(target_home, report)
        self._unset_maven(target_home, report)
        self._unset_gradle(target_home, report)
        self._unset_docker(target_home, report)
        self._unset_apt(report)
        self._unset_yarn(report)
        self._unset_snap(report)
        print_info("Linux proxy settings were removed.")
        return report

    def _target_home(self):
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user:
            try:
                return Path(pwd.getpwnam(sudo_user).pw_dir)
            except KeyError:
                pass
        return Path.home()

    def _target_shell(self):
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user:
            try:
                shell_path = pwd.getpwnam(sudo_user).pw_shell
                return detect_shell_name(sudo_user=sudo_user, shell_value=shell_path)
            except KeyError:
                pass
        return detect_shell_name(shell_value=os.environ.get("SHELL", ""))

    def _shell_rc_path(self, target_home):
        return shell_profile_path(target_home, self._target_shell())

    def _proxy_lines(self):
        return [
            'export http_proxy="{0}"'.format(self.proxy_url),
            'export https_proxy="{0}"'.format(self.proxy_url),
            'export all_proxy="{0}"'.format(self.proxy_url),
            'export no_proxy="localhost,127.0.0.1,::1"',
        ]

    def _proxy_host_port(self):
        parsed = urlparse(self.proxy_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return host, port

    def _strip_proxy_lines(self, lines):
        cleaned = []
        for line in lines:
            if "http_proxy" in line:
                continue
            if "https_proxy" in line:
                continue
            if "all_proxy" in line:
                continue
            if "no_proxy" in line:
                continue
            cleaned.append(line)
        return cleaned

    def _apply_shell_rc(self, shell_rc_path):
        shell_rc_path.parent.mkdir(parents=True, exist_ok=True)
        self._log("Writing shell profile: {0}".format(shell_rc_path))
        if shell_rc_path.exists():
            existing = shell_rc_path.read_text()
            lines = existing.splitlines()
        else:
            lines = []
        lines = self._strip_proxy_lines(lines)
        lines.extend(self._proxy_lines())
        shell_rc_path.write_text("\n".join(lines) + "\n")

    def _remove_shell_rc(self, shell_rc_path):
        if not shell_rc_path.exists():
            return
        self._log("Removing shell profile entries: {0}".format(shell_rc_path))
        lines = self._strip_proxy_lines(shell_rc_path.read_text().splitlines())
        if lines:
            shell_rc_path.write_text("\n".join(lines) + "\n")
        else:
            shell_rc_path.unlink()

    def _environment_path(self):
        return Path("/etc/environment")

    def _apply_environment_file(self, report):
        env_path = self._environment_path()
        if env_path.exists():
            lines = env_path.read_text().splitlines()
        else:
            lines = []
        lines = self._strip_proxy_lines(lines)
        lines.extend(self._proxy_lines())
        env_path.write_text("\n".join(lines) + "\n")
        report.add_applied("/etc/environment")

    def _unset_environment_file(self, report):
        env_path = self._environment_path()
        if not env_path.exists():
            return
        lines = self._strip_proxy_lines(env_path.read_text().splitlines())
        if lines:
            env_path.write_text("\n".join(lines) + "\n")
        else:
            env_path.unlink()
        report.add_applied("/etc/environment")

    def _run_if_available(self, tool_name, command, report):
        if not command_exists(tool_name):
            report.add_skipped(tool_name)
            return
        self.runner(command, check=True)
        report.add_applied(tool_name)

    def _apply_git(self, report):
        self._run_if_available("git", ["git", "config", "--global", "http.proxy", self.proxy_url], report)
        self._run_if_available("git", ["git", "config", "--global", "https.proxy", self.proxy_url], report)

    def _unset_git(self, report):
        self._run_if_available("git", ["git", "config", "--global", "--unset", "http.proxy"], report)
        self._run_if_available("git", ["git", "config", "--global", "--unset", "https.proxy"], report)

    def _pip_config_path(self, target_home):
        return target_home / ".config" / "pip" / "pip.conf"

    def _apply_pip(self, target_home, report):
        if not python_module_exists("pip"):
            report.add_skipped("pip")
            return
        pip_path = self._pip_config_path(target_home)
        pip_path.parent.mkdir(parents=True, exist_ok=True)
        pip_path.write_text("[global]\nproxy = {0}\n".format(self.proxy_url))
        report.add_applied("pip")

    def _unset_pip(self, target_home, report):
        pip_path = self._pip_config_path(target_home)
        if not pip_path.exists():
            return
        pip_path.unlink()
        report.add_applied("pip")

    def _apply_npm(self, report):
        if not command_exists("npm"):
            report.add_skipped("npm")
            return
        self.runner(["npm", "config", "set", "proxy", self.proxy_url], check=True)
        self.runner(["npm", "config", "set", "https-proxy", self.proxy_url], check=True)
        report.add_applied("npm")

    def _unset_npm(self, report):
        if not command_exists("npm"):
            report.add_skipped("npm")
            return
        self.runner(["npm", "config", "delete", "proxy"], check=True)
        self.runner(["npm", "config", "delete", "https-proxy"], check=True)
        report.add_applied("npm")

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

    def _apt_proxy_path(self):
        return Path("/etc/apt/apt.conf.d/95bypass-pucit-proxy")

    def _apply_apt(self, report):
        if not command_exists("apt-get") and not command_exists("apt"):
            report.add_skipped("apt")
            return
        apt_path = self._apt_proxy_path()
        apt_path.write_text(
            'Acquire::http::Proxy "{0}";\nAcquire::https::Proxy "{0}";\n'.format(self.proxy_url)
        )
        report.add_applied("apt")

    def _unset_apt(self, report):
        apt_path = self._apt_proxy_path()
        if apt_path.exists():
            apt_path.unlink()
            report.add_applied("apt")

    def _apply_yarn(self, report):
        if not command_exists("yarn"):
            report.add_skipped("yarn")
            return
        self.runner(["yarn", "config", "set", "proxy", self.proxy_url], check=True)
        self.runner(["yarn", "config", "set", "https-proxy", self.proxy_url], check=True)
        report.add_applied("yarn")

    def _unset_yarn(self, report):
        if not command_exists("yarn"):
            report.add_skipped("yarn")
            return
        self.runner(["yarn", "config", "delete", "proxy"], check=True)
        self.runner(["yarn", "config", "delete", "https-proxy"], check=True)
        report.add_applied("yarn")

    def _wgetrc_path(self, target_home):
        return target_home / ".wgetrc"

    def _apply_wget(self, target_home, report):
        wgetrc_path = self._wgetrc_path(target_home)
        wgetrc_path.write_text(
            "use_proxy = on\n"
            "http_proxy = {0}\n"
            "https_proxy = {0}\n".format(self.proxy_url)
        )
        report.add_applied("wget")

    def _unset_wget(self, target_home, report):
        wgetrc_path = self._wgetrc_path(target_home)
        if wgetrc_path.exists():
            wgetrc_path.unlink()
            report.add_applied("wget")

    def _maven_settings_path(self, target_home):
        return target_home / ".m2" / "settings.xml"

    def _apply_maven(self, target_home, report):
        host, port = self._proxy_host_port()
        settings_path = self._maven_settings_path(target_home)
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

    def _unset_maven(self, target_home, report):
        settings_path = self._maven_settings_path(target_home)
        if settings_path.exists():
            settings_path.unlink()
            report.add_applied("maven")

    def _gradle_properties_path(self, target_home):
        return target_home / ".gradle" / "gradle.properties"

    def _apply_gradle(self, target_home, report):
        host, port = self._proxy_host_port()
        properties_path = self._gradle_properties_path(target_home)
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

    def _unset_gradle(self, target_home, report):
        properties_path = self._gradle_properties_path(target_home)
        if properties_path.exists():
            properties_path.unlink()
            report.add_applied("gradle")

    def _docker_config_path(self, target_home):
        return target_home / ".docker" / "config.json"

    def _apply_docker(self, target_home, report):
        config_path = self._docker_config_path(target_home)
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

    def _unset_docker(self, target_home, report):
        config_path = self._docker_config_path(target_home)
        if config_path.exists():
            config_path.unlink()
            report.add_applied("docker")

    def _apply_snap(self, report):
        if not command_exists("snap"):
            report.add_skipped("snap")
            return
        report.add_applied("snap")

    def _unset_snap(self, report):
        if not command_exists("snap"):
            report.add_skipped("snap")
            return
        report.add_applied("snap")

from .config import DEFAULT_PROXY
from .platforms.linux import LinuxProxyManager


def setForLinux(proxy_url=DEFAULT_PROXY):
    return LinuxProxyManager(proxy_url).apply()


def unsetAllProxiesForLinux(proxy_url=DEFAULT_PROXY):
    return LinuxProxyManager(proxy_url).unset()

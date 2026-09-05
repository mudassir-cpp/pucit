from .config import DEFAULT_PROXY
from .platforms.windows import WindowsProxyManager


def setForWindow(proxy_url=DEFAULT_PROXY):
    return WindowsProxyManager(proxy_url).apply()


def unsetForWindow(proxy_url=DEFAULT_PROXY):
    return WindowsProxyManager(proxy_url).unset()

import platform

from .config import load_proxy_url


class UnsupportedPlatformError(RuntimeError):
    pass


def create_manager(proxy_url, runner=None, verbose=False):
    system_name = platform.system()
    proxy = load_proxy_url(proxy_url)
    if system_name == "Linux":
        from .platforms.linux import LinuxProxyManager

        return LinuxProxyManager(proxy, runner=runner, verbose=verbose)
    if system_name == "Windows":
        from .platforms.windows import WindowsProxyManager

        return WindowsProxyManager(proxy, runner=runner, verbose=verbose)
    raise UnsupportedPlatformError(system_name)

import os


DEFAULT_PROXY = "http://172.16.0.6:8080"


def load_proxy_url(explicit_proxy):
    if explicit_proxy:
        return explicit_proxy
    return os.environ.get("BYPASS_PUCIT_PROXY", DEFAULT_PROXY)

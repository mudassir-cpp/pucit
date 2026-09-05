from .cli import main


def setProxyGlobally(proxy_url=None):
    arguments = ["set"]
    if proxy_url:
        arguments.extend(["--proxy", proxy_url])
    return main(arguments)


def unsetProxyGlobally():
    return main(["unset"])

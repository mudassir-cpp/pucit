from .ColorDTO import Color
from .config import DEFAULT_PROXY


def help_text():
    return (
        f"{Color.BLUE}bypass_pucit{Color.RESET} makes common proxy settings easier to apply.\n"
        "\n"
        f"{Color.GREEN}Commands{Color.RESET}\n"
        "  bypass_pucit set [--proxy URL] [--verbose]\n"
        "  bypass_pucit unset\n"
        "\n"
        f"{Color.GREEN}What it updates{Color.RESET}\n"
        "  shell proxy vars, pip, git, npm, pnpm, wget, Maven, Gradle, Docker, APT, and WinHTTP/registry\n"
        "\n"
        f"{Color.GREEN}Interactive feel{Color.RESET}\n"
        "  each target is reported as applied, skipped, or removed after the command runs\n"
        "\n"
        f"{Color.GREEN}Examples{Color.RESET}\n"
        f"  bypass_pucit set --proxy {DEFAULT_PROXY}\n"
        "  bypass_pucit set --verbose\n"
        "  bypass_pucit unset\n"
        "  python3 -m bypass_pucit.main set --proxy http://proxy.local:8080\n"
        
    )


def print_help():
    print(help_text())


def print_error(message):
    print(f"{Color.RED}ERROR:{Color.RESET} {message}")


def print_info(message):
    print(f"{Color.BLUE}{message}{Color.RESET}")


def print_success(message):
    print(f"{Color.GREEN}{message}{Color.RESET}")


def print_warning(message):
    print(f"{Color.YELLOW}{message}{Color.RESET}")


def print_section(title):
    print(f"\n{Color.BLUE}{title}{Color.RESET}")


def print_tool_list(title, tools):
    print_section(title)
    for tool in tools:
        print(f"  {Color.GREEN}- {tool}{Color.RESET}")


def format_items(items):
    return ", ".join(items) if items else "nothing"

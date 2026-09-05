import argparse
import sys

from .config import DEFAULT_PROXY
from .elevation import is_linux_root, is_windows_admin, relaunch_with_sudo, relaunch_with_uac
from .manager import UnsupportedPlatformError, create_manager
from .messages import format_items, help_text, print_error, print_help, print_info, print_success, print_warning


def build_parser():
    parser = argparse.ArgumentParser(
        prog="bypass_pucit",
        add_help=True,
        description=help_text(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    set_parser = subparsers.add_parser("set", help="apply proxy settings")
    set_parser.add_argument("--proxy", default=None, help="proxy url to apply")
    set_parser.add_argument("--verbose", action="store_true", help="show detailed progress output")

    subparsers.add_parser("unset", help="remove proxy settings")
    return parser, set_parser


def _ensure_elevated(argv):
    import platform

    system_name = platform.system()
    if system_name == "Linux":
        if is_linux_root():
            return False
        relaunch_with_sudo(argv)
        return True
    if system_name == "Windows":
        if is_windows_admin():
            return False
        relaunch_with_uac(argv)
        return True
    return False


def main(argv=None):
    arguments = list(argv if argv is not None else sys.argv[1:])
    parser, _ = build_parser()
    if not arguments:
        print_help()
        return 0
    parsed = parser.parse_args(arguments)
    if parsed.command is None:
        print_help()
        return 0
    if parsed.command == "set":
        try:
            if _ensure_elevated(arguments):
                return 0
        except RuntimeError as exc:
            print_error(str(exc))
            return 1
        try:
            manager = create_manager(parsed.proxy or DEFAULT_PROXY, verbose=getattr(parsed, "verbose", False))
            report = manager.apply()
        except UnsupportedPlatformError as exc:
            print_error("{0} is not supported yet.".format(exc))
            return 1
        print_success("Proxy setup completed.")
        print_info("Applied: {0}".format(format_items(report.applied)))
        if report.skipped:
            print_warning("Skipped: {0}".format(format_items(report.skipped)))
        return 0
    if parsed.command == "unset":
        try:
            if _ensure_elevated(arguments):
                return 0
        except RuntimeError as exc:
            print_error(str(exc))
            return 1
        try:
            manager = create_manager(None, verbose=getattr(parsed, "verbose", False))
            report = manager.unset()
        except UnsupportedPlatformError as exc:
            print_error("{0} is not supported yet.".format(exc))
            return 1
        print_success("Proxy removal completed.")
        print_info("Removed: {0}".format(format_items(report.applied)))
        if report.skipped:
            print_warning("Skipped: {0}".format(format_items(report.skipped)))
        return 0
    print_error("Unknown command.")
    return 1

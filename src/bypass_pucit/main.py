import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from bypass_pucit.cli import main as cli_main
else:
    from .cli import main as cli_main


def main(argv=None):
    cli_main(argv)
    print("\033[31m"+"ads to chl nahi sktay!!! So Follow me on Github!!!\n\033[34mhttps://github.com/mudassir-cpp"+ "\033[0m")



if __name__ == "__main__":
    raise SystemExit(main())





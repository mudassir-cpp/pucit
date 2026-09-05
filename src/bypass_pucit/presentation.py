from .messages import print_error, print_help, print_info


def showHelpPage():
    print_help()


def httpFailure(whatNotFound):
    print_error("{0} shell is not supported for proxy file updates.".format(whatNotFound))
    print_info("The tool will still configure proxy settings where it can.")
    

def showError(errStr):
    print_error(errStr)


def showHowToContributeInTool():
    print_info("Extend support by adding a backend in src/bypass_pucit/platforms.")

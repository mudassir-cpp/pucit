import importlib.util
import shutil


def command_exists(command_name):
    return shutil.which(command_name) is not None


def python_module_exists(module_name):
    return importlib.util.find_spec(module_name) is not None

import os
import imp
import traceback

yaml = None
try:
    import yaml
except:
    import ruamel_yaml as yaml


def check_executable(executable):
    """ Checks to see if an executable is available.

    Args:
        executable (str): The name of executable without extension.

    Returns:
        bool: True for executable existance, False for non-existance.
    """

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(executable)
    if fpath:
        if is_exe(executable):
            return True
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, executable)
            if is_exe(exe_file):
                return True
            if is_exe(exe_file + ".exe"):
                return True

    return False


def check_module(module_name):
    """ Checks if python module is available for import.

    Args:
        module_name (string): The name of the module, ei. "os" in "import os".

    Returns:
        bool: True for module existance, False for non-existance.
    """

    try:
        imp.find_module(module_name)
        return True
    except ImportError:
        return False


def get_configuration():

    yaml_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                             "environment.yml"))
    with open(yaml_file, "r") as stream:
        try:
            return yaml.load(stream)
        except:
            print traceback.format_exc()

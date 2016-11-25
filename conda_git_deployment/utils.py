import os
import imp
import subprocess


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


def ensure_yaml():

    if not check_module("yaml"):
        subprocess.call(["conda", "install", "yaml", "-y"])


def read_yaml(yaml_data):

    ensure_yaml()

    import yaml

    if os.path.isfile(yaml_data):
        with open(yaml_data, "r") as stream:
                return yaml.load(stream)

    if isinstance(yaml_data, str) or isinstance(yaml_data, unicode):
        return yaml.load(yaml_data)


def write_yaml(data, file_path):

    ensure_yaml()
    import yaml

    f = open(file_path, "w")
    try:
        yaml.dump(data, f, default_flow_style=False)
    finally:
        f.close()

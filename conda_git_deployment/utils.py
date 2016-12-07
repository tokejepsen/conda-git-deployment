import os
import imp
import subprocess
import argparse
import tempfile


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


def read_yaml(yaml_file):

    ensure_yaml()
    import yaml

    if os.path.isfile(yaml_file):
        with open(yaml_file, "r") as stream:
                return yaml.load(stream)

    if isinstance(yaml_file, str) or isinstance(yaml_file, unicode):
        return yaml.load(yaml_file)


def write_yaml(data, yaml_file):

    ensure_yaml()
    import yaml

    f = open(yaml_file, "w")
    try:
        yaml.dump(data, f, default_flow_style=False)
    finally:
        f.close()


def get_arguments():

    parser = argparse.ArgumentParser(description="conda-git-deployment")

    parser.add_argument('--update', action="store_true", default=False,
                        dest="update",
                        help="Rebuild and updates an environment.")
    parser.add_argument('--environment', action="store", default="",
                        dest="environment",
                        help="Environment to process.")

    args, unknown = parser.parse_known_args()
    results = vars(args)
    results["unknown"] = unknown
    return results


def write_environment(dictionary):

    yaml_file = os.path.join(
        tempfile.gettempdir(), "conda_git_deployment.yml"
    )

    write_yaml(dictionary, yaml_file)


def read_environment():

    yaml_file = os.path.join(
        tempfile.gettempdir(), "conda_git_deployment.yml"
    )

    if os.path.exists(yaml_file):
        return read_yaml(yaml_file)
    else:
        return {}

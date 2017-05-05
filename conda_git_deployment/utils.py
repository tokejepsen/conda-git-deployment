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

    parser.add_argument(
        "--update-environment",
        action="store_true",
        default=False,
        dest="update-environment",
        help="Update and rebuild environment."
    )
    parser.add_argument(
        "--update-repositories",
        action="store_true",
        default=False,
        dest="update-repositories",
        help="Update and rebuild repositories."
    )
    parser.add_argument(
        "--environment",
        action="store",
        default="",
        dest="environment",
        help="Environment to process."
    )
    parser.add_argument(
        "--attached",
        action="store_true",
        default=False,
        dest="attached",
        help="Spawn non-detached processes."
    )
    parser.add_argument(
        "--export",
        action="store_true",
        default=False,
        dest="export",
        help="Exports the environment."
    )
    parser.add_argument(
        "--export-without-commit",
        action="store_true",
        default=False,
        dest="export-without-commit",
        help="Exports the environment, without commit ids."
    )

    args, unknown = parser.parse_known_args()
    results = vars(args)
    results["unknown"] = unknown
    return results


def get_environment_path():

    return os.path.join(
        tempfile.gettempdir(), "conda_git_deployment.yml"
    )


def write_environment(env):

    yaml_file = get_environment_path()

    # Setting environment.
    output_data = {}
    for variable in env:
        path = ""
        for item in env[variable]:
            if item not in os.environ.get(variable, "").split(os.pathsep):
                path += os.pathsep + item

        try:
            os.environ[variable] += path
        except:
            os.environ[variable] = path[1:]

        output_data[variable] = os.environ[variable]

    write_yaml(output_data, yaml_file)


def read_environment():

    yaml_file = get_environment_path()

    if os.path.exists(yaml_file):
        return read_yaml(yaml_file)
    else:
        return {}

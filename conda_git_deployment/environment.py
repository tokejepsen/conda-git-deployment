import os
import subprocess
import platform
import tempfile
import requests


import utils


def main():

    # Add conda_git_deployment module to environment.
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.environ["PYTHONPATH"] += os.pathsep + path

    # Get environment path
    path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "environment.conf")
    )
    environment = None
    if os.path.exists(path):
        with open(path, "r") as f:
            environment = f.read().rstrip()

    # Create a default enviroment if no environment file was found.
    # NOT FINISHED!
    if not environment:
        msg = "\n\nCould not find the environment.yml file in {path}."
        msg += "\nPlease create an environment file and save it as "
        msg += "{path}/environment.yml."
        msg += "\nYou can also modify the included example "
        msg += "{path}/environment.yml.example, and rename to "
        msg += "{path}/environment.yml."
        msg += "\n\nA default environment will be created."
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        path = path.replace("\\", "/")

        print msg.format(path=path)

        subprocess.call(["conda", "create", "-n", "default", "python", "-y"])

        args = []
        if platform.system().lower() == "windows":
            args.extend(["start", "activate", "default"])

        if platform.system().lower() == "linux":
            terminal_commands = ["gnome-terminal", "xterm", "konsole"]
            for cmd in terminal_commands:
                if utils.check_executable(cmd):
                    args.extend([cmd, "-e", "source activate default"])

        subprocess.call(args, shell=True)
        return

    # Get environment data.
    env_conf = None
    if os.path.exists(environment):
        f = open(environment, "r")
        env_conf = utils.read_yaml(f.read())
        f.close()

    if not env_conf:
        env_conf = utils.read_yaml(requests.get(environment).text)

    data_file = os.path.join(
        tempfile.gettempdir(), 'data_%s.yml' % os.getpid()
    )
    utils.write_yaml(env_conf, data_file)

    # Create environment.
    # Remove git from environment as its not supported by conda (yet).
    for item in env_conf["dependencies"]:
        if "git" in item:
            index = env_conf["dependencies"].index(item)
            del env_conf["dependencies"][index]

    # Create environment file from passed environment.
    filename = os.path.join(
        tempfile.gettempdir(), 'env_%s.yml' % os.getpid()
    )

    utils.write_yaml(env_conf, filename)

    args = ["conda", "env", "create"]
    if utils.get_arguments()["update"]:
        args.append("--force")
    args.extend(["-f", filename])

    return_code = subprocess.call(args)

    os.remove(filename)

    # Spawning a new process to get the correct python executable and
    # passing data via file on disk.
    args = [os.path.join(os.path.dirname(__file__), "environment.bat"),
            env_conf["name"],
            os.path.join(os.path.dirname(__file__), "install.py"),
            data_file]

    if utils.get_arguments()["update"]:
        args.append("--update")

    # If its the first installation, we need to pass update to install.py
    if not return_code:
        args.append("--update")

    subprocess.call(args)


if __name__ == "__main__":

    main()

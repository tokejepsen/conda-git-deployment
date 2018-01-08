import os
import subprocess
import tempfile
import sys
import platform


import utils


def main():

    # If no environment is defined, put user in root environment.
    # Or if requested to put user into the root environment.
    if not utils.get_environment() or utils.get_environment() == "root":

        msg = ""

        if not utils.get_environment():
            msg += (
                "\n\nCould not find the \"environment.conf\" file in "
                "\"{path}\".\nPlease create an environment pointer file and "
                "save it as \"{path}/environment.conf\".\nYou can also modify "
                "the included example \"{path}/environment.conf.example\", and"
                " rename to \"{path}/environment.conf\"."
            )

        msg += (
            "\n\nYou are in the root environment of Conda. The \"conda\", "
            "\"activate\" and \"deactivate\" command is ""available to use "
            "now."
        )
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        path = path.replace("\\", "/")

        print(msg.format(path=path))

        return

    # Add conda_git_deployment module to environment.
    # Also removing PYTHONPATH that conda root environment needs.
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.environ["PYTHONPATH"] = path

    # Get environment data.
    environment_string = utils.get_environment_string()
    environment_data = utils.read_yaml(environment_string)

    os.environ["CONDA_ENVIRONMENT_NAME"] = environment_data["name"]

    # Writing original environment to disk
    data_file = os.path.join(
        tempfile.gettempdir(), 'data_%s.yml' % os.getpid()
    )
    utils.write_yaml(environment_data, data_file)

    # Remove git from environment as its not supported by conda (yet).
    for item in environment_data["dependencies"]:
        if "git" in item:
            index = environment_data["dependencies"].index(item)
            del environment_data["dependencies"][index]

    # Create environment file from passed environment.
    environment_filename = os.path.join(
        tempfile.gettempdir(), 'env_%s.yml' % os.getpid()
    )

    utils.write_yaml(environment_data, environment_filename)

    args = ["conda", "env", "create"]

    # Force environment update/rebuild when requested by command.
    if utils.get_arguments()["update-environment"]:
        args.append("--force")

    # Check whether the environment installed is different from the requested
    # environment. Force environment update/rebuild if different.
    environment_update = False

    if utils.updates_available():
        environment_update = True
        if "--force" not in args:
            args.append("--force")

    path = utils.get_md5_path()
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    with open(path, "w") as the_file:
        the_file.write(utils.get_incoming_md5())

    # Create environment
    args.extend(["-f", environment_filename])

    return_code = subprocess.call(args)

    os.remove(environment_filename)

    # Spawning a new process to get the correct python executable and
    # passing data via file on disk.
    platform_script = "environment.sh"
    if platform.system().lower() == "windows":
        platform_script = "environment.bat"

    args = [os.path.join(os.path.dirname(__file__), platform_script),
            environment_data["name"],
            os.path.join(os.path.dirname(__file__), "install.py"),
            data_file]

    args.extend(sys.argv[1:])

    # If its the first installation, we need to pass update to install.py
    if not return_code:
        args.append("--update-environment")

    if platform.system().lower() != "windows":
        args.insert(0, "bash")

    if environment_update and "--update-environment" not in args:
        args.append("--update-environment")

    subprocess.call(args)


if __name__ == "__main__":

    main()

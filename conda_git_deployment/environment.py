import os
import subprocess
import tempfile
import sys
import platform
import zipfile


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
    environment_data = {}
    if utils.get_arguments()["environment"].endswith(".yml"):
        environment_string = utils.get_environment_string()
        environment_data = utils.read_yaml(environment_string)
    if utils.get_arguments()["environment"].endswith(".zip"):
        environment_data["name"] = os.path.basename(
            utils.get_arguments()["environment"]
        ).replace(".zip", "")

    os.environ["CONDA_ENVIRONMENT_NAME"] = environment_data["name"]

    # Create environment
    return_code = True
    environment_update = False
    data_file = os.path.join(
        tempfile.gettempdir(), 'data_%s.yml' % os.getpid()
    )
    if utils.get_arguments()["environment"].endswith(".yml"):
        # Writing original environment to disk
        utils.write_yaml(environment_data, data_file)

        # Remove git from environment as its not supported by conda (yet).
        for item in environment_data["dependencies"]:
            if "git" in item:
                index = environment_data["dependencies"].index(item)
                del environment_data["dependencies"][index]

        environment_filename = os.path.join(
            tempfile.gettempdir(), 'env_%s.yml' % os.getpid()
        )

        utils.write_yaml(environment_data, environment_filename)

        args = ["conda", "env", "create"]

        # Force environment update/rebuild when requested by command.
        if utils.get_arguments()["update-environment"]:
            args.append("--force")

        # Check whether the environment installed is different from the
        # requested environment. Force environment update/rebuild if different.
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

    if (utils.get_arguments()["environment"].endswith(".zip") and
       utils.get_arguments()["update-environment"]):
        # Remove existing environment
        subprocess.call(
            [
                "conda",
                "env",
                "remove",
                "--name",
                environment_data["name"],
                "-y"
            ]
        )

        # Unzip environment
        print "Unzipping environment..."
        zip_ref = zipfile.ZipFile(utils.get_arguments()["environment"], "r")
        zip_ref.extractall(
            os.path.abspath(os.path.join(sys.executable, "..", "envs"))
        )
        zip_ref.close()

    # Enabling activation of environment to run the environment commands.
    path = os.path.abspath(
        os.path.join(
            sys.executable,
            "..",
            "envs",
            environment_data["name"],
            "etc",
            "conda",
            "activate.d",
            "run_commands.bat"
        )
    )

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    with open(path, "w") as the_file:
        the_file.write("set CONDA_ENVIRONMENT_CWD=\"%cd%\"")
        the_file.write(
            "\nset CONDA_ENVIRONMENT_PATH=%~dp0../../../Lib/site-packages/"
            "repositories/{0}/environment.yml".format(environment_data["name"])
        )
        the_file.write(
            "\npython -c \"from conda_git_deployment import install;"
            "install.try_run_commands()\""
        )

    # Spawning a new process to get the correct python executable and
    # passing data via file on disk.
    args = [
        os.path.abspath(
            os.path.join(sys.executable, "..", "Scripts", "activate.bat")
        ),
        environment_data["name"],
    ]

    # If its the first installation, we need to pass update to install.py
    update_environment = False
    if not return_code:
        update_environment = True

    if environment_update and "--update-environment" not in args:
        update_environment = True

    # Only if we are updating the environment, are we going to run the
    # repositories installation. Else the environment is self contained.
    if update_environment:
        os.environ["CONDA_SKIP_COMMANDS"] = ""

        args.extend(
            [
                "&",
                "python",
                os.path.join(os.path.dirname(__file__), "install.py"),
                data_file
            ]
        )

        args.append("--update-environment")

        args.extend(sys.argv[1:])

    # If exporting the environment we can skip the commands.
    if (utils.get_arguments()["export"] or
       utils.get_arguments()["export-without-commit"] or
       utils.get_arguments()["export-zip-environment"]):
        os.environ["CONDA_SKIP_COMMANDS"] = ""

        args.extend(
            [
                "&",
                "python",
                os.path.join(os.path.dirname(__file__), "install.py"),
                data_file
            ]
        )

        args.extend(sys.argv[1:])

    subprocess.call(args, env=os.environ)


if __name__ == "__main__":

    main()

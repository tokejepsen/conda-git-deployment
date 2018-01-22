import os
import subprocess
import tempfile
import sys
import zipfile

import utils


def export_deployment():
    # Export deployment
    print("Exporting deployment...")
    zip_file = zipfile.ZipFile("deployment.zip", "w", zipfile.ZIP_DEFLATED)

    path = os.path.abspath(os.path.join(__file__, "..", ".."))
    files_to_zip = []
    file_exclusion = [
        os.path.abspath(os.path.join(__file__, "..", "..", "deployment.zip"))
    ]
    extension_exclusion = [".pyc"]
    directory_exclusion = [
        os.path.abspath(os.path.join(__file__, "..", "..", "installers")),
        os.path.abspath(os.path.join(__file__, "..", "..", "repositories")),
        os.path.abspath(
            os.path.join(
                __file__, "..", "..", "installation", "windows", "pkgs"
            )
        ),
    ]

    # Only export the environment requested
    environment_string = utils.get_environment_string()
    environment_data = utils.read_yaml(environment_string)
    envs_directory = os.path.abspath(
        os.path.join(
            __file__, "..", "..", "installation", "windows", "envs"
        )
    )
    for directory in os.listdir(envs_directory):
        if directory != environment_data["name"]:
            directory_exclusion.append(os.path.join(envs_directory, directory))

    # Find all files to zip
    for root, dirs, files in os.walk(path, topdown=True, followlinks=True):
        valid_directories = []
        for d in dirs:
            # Exclude git histories
            if d == ".git":
                continue

            if os.path.join(root, d) not in directory_exclusion:
                valid_directories.append(d)
        dirs[:] = valid_directories

        for f in files:
            path = os.path.join(root, f)
            if path in file_exclusion:
                continue

            # Exclude compiled python files
            if os.path.splitext(f)[1] in extension_exclusion:
                continue

            files_to_zip.append(path)

    # Zip deployment
    if not utils.check_module("tqdm"):
        subprocess.call(["pip", "install", "tqdm"])

    from tqdm import tqdm

    path = os.path.abspath(os.path.join(__file__, "..", ".."))
    for f in tqdm(files_to_zip, "Zipping deployment"):
        zip_file.write(f, os.path.relpath(f, path))

    zip_file.close()


def main():

    # If no environment is defined, put user in root environment.
    # Or if requested to put user into the root environment.
    environment = utils.get_arguments()["environment"]
    if not environment or environment == "root":
        print(
            "You are in the base environment of Conda. The \"conda\", "
            "\"activate\" and \"deactivate\" command is available to use now."
        )
        return

    # Add conda_git_deployment module to environment.
    # Also removing PYTHONPATH that conda root environment needs.
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.environ["PYTHONPATH"] = path

    # Get environment data.
    environment_string = utils.get_environment_string()
    environment_data = utils.read_yaml(environment_string)

    os.environ["CONDA_ENVIRONMENT_NAME"] = environment_data["name"]

    # Export deployment
    if utils.get_arguments()["export-deployment"]:
        export_deployment()
        return

    # Create environment
    data_file = os.path.join(
        tempfile.gettempdir(), 'data_%s.yml' % os.getpid()
    )

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

    path = utils.get_md5_path()
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    with open(path, "w") as the_file:
        the_file.write(utils.get_incoming_md5())

    # Create environment
    args.extend(["-f", environment_filename])

    return_code = subprocess.call(args)

    os.remove(environment_filename)

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
        the_file.write("set CONDA_ENVIRONMENT_CWD=%cd%")
        the_file.write("\nset PYTHONPATH=%cd%")
        the_file.write(
            "\nset CONDA_ENVIRONMENT_PATH=%~dp0../../../Lib/site-packages/"
            "repositories/{0}/environment.yml".format(environment_data["name"])
        )
        the_file.write(
            "\npython -c \"from conda_git_deployment import install;"
            "install.run_commands()\""
        )

    # Setting environment variables
    repositories_path = os.path.abspath(
        os.path.join(
            sys.executable,
            "..",
            "envs",
            environment_data["name"],
            "Lib",
            "site-packages",
            "repositories"
        )
    )
    os.environ["CONDA_ENVIRONMENT_REPOSITORIES"] = repositories_path
    os.environ["CONDA_GIT_REPOSITORY"] = repositories_path

    # Spawning a new process to get the correct python executable and
    # passing data via file on disk.
    args = [
        os.path.abspath(
            os.path.join(sys.executable, "..", "Scripts", "activate.bat")
        ),
        environment_data["name"],
    ]

    # Only if we are updating the environment, are we going to run the
    # repositories installation. Else the environment is self contained.
    if not return_code or utils.get_arguments()["update-environment"]:
        os.environ["CONDA_SKIP_COMMANDS"] = ""

        args.extend(
            [
                "&",
                "python",
                os.path.join(os.path.dirname(__file__), "install.py"),
                data_file
            ]
        )

        if "--update-environment" not in args:
            args.append("--update-environment")

    # When exporting we need the install.py
    if (utils.get_arguments()["export"] or
       utils.get_arguments()["export-without-commit"]):
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
    print args
    subprocess.call(args, env=os.environ)


if __name__ == "__main__":

    main()

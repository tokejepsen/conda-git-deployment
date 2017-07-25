import os
import subprocess
import tempfile
import requests
import sys
import platform
import hashlib


import utils


def main():

    # Add conda_git_deployment module to environment.
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.environ["PYTHONPATH"] += os.pathsep + path

    # Get environment path
    environment_path = ""

    configuration_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "environment.conf")
    )
    if os.path.exists(configuration_path):
        with open(configuration_path, "r") as f:
            environment_path = f.read().rstrip()

    if utils.get_arguments()["environment"]:
        environment_path = utils.get_arguments()["environment"]

    # If no environment is defined, put user in root environment.
    if not environment_path:

        msg = "\n\nCould not find the \"environment.conf\" file in \"{path}\"."
        msg += "\nPlease create an environment pointer file and save it as "
        msg += "\"{path}/environment.conf\"."
        msg += "\nYou can also modify the included example "
        msg += "\"{path}/environment.conf.example\", and rename to "
        msg += "\"{path}/environment.conf\"."
        msg += "\n\nYou are in the root environment of Conda. "
        msg += "The \"conda\" command is available to use now."
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        path = path.replace("\\", "/")

        print msg.format(path=path)

        return

    # If requested to put user into the root environment.
    if environment_path == "root":

        msg = "You are in the root environment of Conda. "
        msg += "The \"conda\" command is available to use now."
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        path = path.replace("\\", "/")

        print msg.format(path=path)

        return

    # Get environment data.
    environment_string = ""
    if os.path.exists(environment_path):
        f = open(environment_path, "r")
        environment_string = f.read()
        f.close()
    else:
        msg = "Could not find \"{0}\" on disk."
        print msg.format(environment_path)

    if not environment_string:
        environment_string = requests.get(environment_path).text

    environment_data = utils.read_yaml(environment_string)

    # Export environment
    if (utils.get_arguments()["export"] or
       utils.get_arguments()["export-without-commit"]):
        repositories_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "repositories",
                environment_data["name"]
            )
        )

        # Get commit hash and name from repositories on disk.
        if not utils.check_executable("git"):
            subprocess.call(
                ["conda", "install", "-c", "anaconda", "git", "-y"]
            )
        disk_repos = {}
        for repo in os.listdir(repositories_path):

            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=os.path.join(repositories_path, repo)
            ).rsplit()[0]

            disk_repos[repo] = commit_hash

        # Construct new git dependencies.
        git_data = {"git": []}
        for item in environment_data["dependencies"]:
            if "git" in item:
                for repo in item["git"]:

                    # Get url from enviroment file.
                    url = ""
                    if isinstance(repo, str):
                        url = repo
                    if isinstance(repo, dict):
                        url = repo.keys()[0]

                    # Skip any repositories that aren't cloned yet.
                    name = url.split("/")[-1].replace(".git", "").split("@")[0]
                    if name not in disk_repos.keys():
                        continue

                    # Construct commit url if requested.
                    commit_url = url.split("@")[0]
                    if not utils.get_arguments()["export-without-commit"]:
                        commit_url += "@" + disk_repos[name]

                    if isinstance(repo, str):
                        git_data["git"].append(commit_url)

                    if isinstance(repo, dict):
                        git_data["git"].append({commit_url: repo[url]})

        # Replace git dependencies
        for item in environment_data["dependencies"]:
            if "git" in item:
                environment_data["dependencies"].remove(item)

        environment_data["dependencies"].append(git_data)

        # Write environment file
        utils.write_yaml(
            environment_data, os.path.join(os.getcwd(), "environment.yml")
        )

        return

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
    incoming_md5 = hashlib.md5(environment_string).hexdigest()
    existing_md5 = ""

    md5_path = os.path.join(
        os.path.expanduser("~"),
        "AppData",
        "Local",
        "Continuum",
        "Miniconda2",
        "environment.md5"
    )
    if os.path.exists(md5_path):
        f = open(md5_path, "r")
        existing_md5 = f.read()
        f.close()

    if incoming_md5 != existing_md5 and "--force" not in args:
        args.append("--force")

    with open(md5_path, "w") as the_file:
        the_file.write(incoming_md5)

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
        args.append("--update-repositories")

    if platform.system().lower() != "windows":
        args.insert(0, "bash")

    subprocess.call(args)


if __name__ == "__main__":

    main()

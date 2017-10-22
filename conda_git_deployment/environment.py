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

        print msg.format(path=path)

        return

    # Add conda_git_deployment module to environment.
    # Also removing PYTHONPATH that conda root environment needs.
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.environ["PYTHONPATH"] = path

    # Get environment data.
    environment_string = utils.get_environment_string()
    environment_data = utils.read_yaml(environment_string)

    os.environ["CONDA_ENVIRONMENT_NAME"] = environment_data["name"]

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
            path = os.path.join(repositories_path, repo)
            if not os.path.exists(os.path.join(path, ".git")):
                continue

            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=path
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
    # environment, and whether the conda-git-deployment is different.
    # Force environment update/rebuild if different.
    environment_update = False
    if not utils.get_arguments()["suppress-environment-update"]:

        if utils.updates_available():
            environment_update = True
            if "--force" not in args:
                args.append("--force")

        with open(utils.get_md5_path(), "w") as the_file:
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

import os
import subprocess
import tempfile
import requests
import sys


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

    if utils.get_arguments()["environment"]:
        environment = utils.get_arguments()["environment"]

    # If no environment is defined, put user in root environment.
    if not environment:

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

    # Get environment data.
    env_conf = None
    if os.path.exists(environment):
        f = open(environment, "r")
        env_conf = utils.read_yaml(f.read())
        f.close()
    else:
        msg = "Could not find \"{0}\" on disk."
        print msg.format(environment)

    if not env_conf:
        env_conf = utils.read_yaml(requests.get(environment).text)

    # Export environment
    if utils.get_arguments()["export"]:
        repositories_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "repositories",
                env_conf["name"]
            )
        )

        git_data = {"git": []}
        for repo in os.listdir(repositories_path):

            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=os.path.join(repositories_path, repo)
            ).rsplit()[0]

            url = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                cwd=os.path.join(repositories_path, repo)
            ).rsplit()[0]

            for item in env_conf["dependencies"]:
                if "git" in item:

                    for origin_repo in item["git"]:

                        origin_repo_url = ""
                        if isinstance(origin_repo, str):
                            origin_repo_url = origin_repo
                        if isinstance(origin_repo, dict):
                            origin_repo_url = origin_repo.keys()[0]

                        if url == origin_repo_url.split("@")[0]:
                            current_commit_url = url
                            if not utils.get_arguments()["no-commit"]:
                                current_commit_url += "@" + commit_hash
                            if isinstance(origin_repo, str):
                                git_data["git"].append(current_commit_url)
                            if isinstance(origin_repo, dict):
                                value = origin_repo[origin_repo_url]
                                git_data["git"].append({
                                    current_commit_url: value
                                })

        for item in env_conf["dependencies"]:
            if "git" in item:
                env_conf["dependencies"].remove(item)

        git_data["git"].reverse()
        env_conf["dependencies"].append(git_data)
        utils.write_yaml(
            env_conf, os.path.join(os.getcwd(), "environment.yml")
        )

        return

    # Writing original environment to disk
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

    args.extend(sys.argv[1:])

    # If its the first installation, we need to pass update to install.py
    if not return_code:
        args.append("--update")

    subprocess.call(args)


if __name__ == "__main__":

    main()

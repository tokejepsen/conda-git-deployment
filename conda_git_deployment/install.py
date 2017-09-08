import os
import sys
import subprocess
import tempfile
import platform
from difflib import SequenceMatcher

import utils


def main():

    conf = utils.read_yaml(utils.get_arguments()["unknown"][0])
    os.remove(utils.get_arguments()["unknown"][0])

    # Clone repositories. Using os.getcwd() because the drive letter needs to
    # be respected on Windows.
    repositories_path = os.path.abspath(
        os.path.join(
            os.getcwd(), "repositories", conf["name"]
        )
    )

    os.environ["CONDA_ENVIRONMENT_REPOSITORIES"] = repositories_path

    # Kept for backwards compatibility
    os.environ["CONDA_GIT_REPOSITORY"] = repositories_path

    repositories = []
    for item in conf["dependencies"]:
        if "git" in item:
            for repo in item["git"]:

                repo_path = ""
                if isinstance(repo, str):
                    repo_path = repo
                if isinstance(repo, dict):
                    repo_path = repo.keys()[0]

                data = {"url": repo_path}

                name = repo_path.split("/")[-1].replace(".git", "")
                if not name:
                    name = repo_path.split("/")[-2]
                if "@" in name:
                    name = name.split("@")[0]
                    repo_path = repo_path.split("@")[0]
                data["name"] = name

                if not os.path.exists(repositories_path):
                    os.makedirs(repositories_path)

                if name not in os.listdir(repositories_path):
                    subprocess.call(["git", "clone", repo_path],
                                    cwd=repositories_path)

                data["path"] = os.path.join(repositories_path, name)

                data["commands"] = {
                    "on_launch": [], "on_environment_update": []
                }
                if isinstance(repo, dict):
                    for item in repo[repo.keys()[0]]:
                        if isinstance(item, dict):
                            for event, commands in item.iteritems():
                                data["commands"][event].extend(commands)
                        else:
                            data["commands"]["on_launch"].append(item)

                repositories.append(data)

    # Update repositories.
    if utils.get_arguments()["update-repositories"]:
        for repo in repositories:
            print repo["name"]

            # Updating origin url
            subprocess.call(
                ["git", "remote", "set-url", "origin",
                 repo["url"].split("@")[0]], cwd=repo["path"]
            )

            # Update git repository
            subprocess.call(["git", "checkout", "master"], cwd=repo["path"])
            subprocess.call(["git", "pull"], cwd=repo["path"])
            subprocess.call(["git", "submodule", "update", "--init",
                             "--recursive"], cwd=repo["path"])
            subprocess.call(["git", "submodule", "update", "--recursive"],
                            cwd=repo["path"])

    # Checkout any commits/tags if there are newly cloned repositories or
    # updating the repositories.
    if utils.get_arguments()["update-repositories"]:
        for repo in repositories:
            if "@" in repo["url"]:
                tag = repo["url"].split("@")[1]
                if tag:
                    print repo["name"]
                    subprocess.call(["git", "checkout", tag], cwd=repo["path"])

        # Checkout environment repository
        environment_path = utils.get_environment()
        if not os.path.exists(environment_path):
            # Determine environment repositories by matching passed environment
            # with repositories
            environment_repo = None
            match = 0.0
            for repo in repositories:
                sequence_match = SequenceMatcher(
                    None, repo["url"], environment_path
                ).ratio()
                if match < sequence_match:
                    environment_repo = repo

            print environment_repo["name"]
            branch = environment_path.split("/")[-2]
            subprocess.call(
                ["git", "checkout", branch], cwd=environment_repo["path"]
            )

    # Install any setup.py if we are updating
    if (utils.get_arguments()["update-repositories"] or
       utils.get_arguments()["update-environment"]):
        for repo in repositories:
            if "setup.py" not in os.listdir(repo["path"]):
                continue

            args = ["python", "setup.py", "develop"]
            subprocess.call(args, cwd=repo["path"])

    # Add environment site packages to os.environ
    prefix = ""
    if platform.system().lower() == "windows":
        prefix = os.environ["CONDA_PREFIX"]
    else:
        prefix = os.environ["CONDA_ENV_PATH"]

    path = os.path.join(prefix, "lib", "site-packages")
    os.environ["PYTHONPATH"] += os.pathsep + path

    # Add sys.path to os.environ["PYTHONPATH"], because conda only modifies
    # sys.path which gets lost when launching any detached subprocesses.
    # This get a little complicated due to being in a process that hasn"t
    # picked up on the changes, hence going through a subprocess.
    python_file = os.path.join(os.path.dirname(__file__), "write_sys_path.py")
    data_file = os.path.join(
        tempfile.gettempdir(), "data_%s.yml" % os.getpid()
    )
    subprocess.call(["python", python_file, data_file])

    paths = []
    with open(data_file, "r") as f:
        paths += utils.read_yaml(f.read())
    os.remove(data_file)

    for path in paths:
        if path.lower().startswith(repositories_path.lower()):
            os.environ["PYTHONPATH"] += os.pathsep + path
        if path.endswith(".egg"):
            os.environ["PYTHONPATH"] += os.pathsep + path

    # Clean up any existing environment file
    if os.path.exists(utils.get_environment_path()):
        os.remove(utils.get_environment_path())

    # Ensure subprocess is detached so closing connect will not also
    # close launched applications.
    options = {}
    if not utils.get_arguments()["attached"]:
        if sys.platform == "win32":
            options["creationflags"] = subprocess.CREATE_NEW_CONSOLE
        else:
            options["preexec_fn"] = os.setsid

    # Setting update mode environment variable
    update_modes = []
    if utils.get_arguments()["update-environment"]:
        update_modes.append("environment")
    if utils.get_arguments()["update-repositories"]:
        update_modes.append("repositories")

    os.environ["CONDA_GIT_UPDATE"] = ""
    for mode in update_modes:
        os.environ["CONDA_GIT_UPDATE"] += mode + os.pathsep

    # Execute environment update commands.
    if utils.get_arguments()["update-environment"]:
        for repo in repositories:
            if "commands" in repo.keys():
                for cmd in repo["commands"]["on_environment_update"]:
                    os.environ.update(utils.read_environment())
                    cmd = cmd.replace("$REPO_PATH", repo["path"])
                    print "Executing: " + cmd
                    subprocess.call(
                        cmd, shell=True, cwd=repo["path"], **options
                    )

    # Execute launch commands.
    for repo in repositories:
        if "commands" in repo.keys():
            for cmd in repo["commands"]["on_launch"]:
                os.environ.update(utils.read_environment())
                cmd = cmd.replace("$REPO_PATH", repo["path"])
                print "Executing: " + cmd
                subprocess.call(cmd, shell=True, cwd=repo["path"], **options)


if __name__ == "__main__":

    main()

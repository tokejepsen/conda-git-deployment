import os
import subprocess

import utils


def main():

    conf = utils.read_yaml(utils.get_arguments()["unknown"][0])
    os.remove(utils.get_arguments()["unknown"][0])

    # Clone repositories.
    repositories_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "repositories", conf["name"]
        )
    )

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
                data["name"] = name

                if not os.path.exists(repositories_path):
                    os.makedirs(repositories_path)

                if name not in os.listdir(repositories_path):
                    subprocess.call(["git", "clone", repo_path],
                                    cwd=repositories_path)
                data["path"] = os.path.join(repositories_path, name)

                if isinstance(repo, dict):
                    data["commands"] = repo[repo.keys()[0]]

                repositories.append(data)

    # Update repositories.
    if utils.get_arguments()["update"]:
        for repo in repositories:
            print repo["name"]
            subprocess.call(["git", "pull"], cwd=repo["path"])
            subprocess.call(["git", "submodule", "update", "--init",
                             "--recursive"], cwd=repo["path"])
            subprocess.call(["git", "submodule", "update", "--recursive"],
                            cwd=repo["path"])

    # Checkout any commits/tags.
    for repo in repositories:
        if "@" in repo["url"]:
            tag = repo["url"].split("@")[1]
            if tag:
                subprocess.call(["git", "checkout", tag], cwd=repo["path"])

    # Install any setup.py
    # Query if a "build" directory is present to determine whether a repository
    # has been installed.
    for repo in repositories:
        list_dir = os.listdir(repo["path"])
        if (("setup.py" in list_dir and "build" not in list_dir) or
           utils.get_arguments()["update"]):
            args = ["python", "setup.py", "install"]
            subprocess.call(args, cwd=repo["path"])

    # Add environment site packages to os.environ
    path = os.path.join(os.environ["CONDA_PREFIX"], "lib", "site-packages")
    os.environ["PYTHONPATH"] += os.pathsep + path

    # Execute start commands.
    for repo in repositories:
        if "commands" in repo.keys():
            for cmd in repo["commands"]:
                cmd = cmd.replace("$REPO_PATH", repo["path"])
                print "Executing: " + cmd
                subprocess.call(cmd, shell=True, cwd=repo["path"])


if __name__ == "__main__":

    main()

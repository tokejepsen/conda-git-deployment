import os
import subprocess
import platform

import utils


def main():

    conf = utils.get_configuration()
    if not conf:
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

    # clone repositories
    repositories_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                     "..", "repositories"))

    repositories = []
    for item in conf["dependencies"]:
        if "git" in item:
            for repo in item["git"]:

                data = {}

                repo_path = ""
                if isinstance(repo, str):
                    repo_path = repo
                if isinstance(repo, dict):
                    repo_path = repo.keys()[0]

                name = repo_path.split("/")[-1].replace(".git", "")
                if not name:
                    name = repo_path.split("/")[-2]
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

    # update repositories
    for repo in repositories:
        print repo["name"]
        subprocess.call(["git", "pull"], cwd=repo["path"])
        subprocess.call(["git", "submodule", "update", "--init",
                         "--recursive"], cwd=repo["path"])
        subprocess.call(["git", "submodule", "update", "--recursive"],
                        cwd=repo["path"])

    # install repositories with pip
    source_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                               ".."))
    for repo in repositories:
        if "setup.py" in os.listdir(repo["path"]):
            url = "git+file://" + repo["path"]
            subprocess.call(["pip", "install", url], cwd=source_path)

    # execute start commands
    for repo in repositories:
        if "commands" in repo.keys():
            for cmd in repo["commands"]:
                cmd = cmd.replace("$REPO_PATH", repo["path"])
                print "Executing: " + cmd
                subprocess.Popen(cmd, shell=True)


if __name__ == "__main__":

    main()

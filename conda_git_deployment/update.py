import os
import subprocess

import utils

# install git
if not utils.check_executable("git"):
    subprocess.call(["conda", "install", "-c", "anaconda", "git", "-y"])

# update conda-git-deployment
print "conda-git-deployment"
path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
subprocess.call(["git", "pull"], cwd=path)

# clone repositories
repositories_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 "..", "repositories"))
if not os.path.exists(repositories_path):
    os.makedirs(repositories_path)

conf = utils.get_configuration()
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
    subprocess.call(["git", "submodule", "update", "--init", "--recursive"],
                    cwd=repo["path"])
    subprocess.call(["git", "submodule", "update", "--recursive"],
                    cwd=repo["path"])

# install repositories with pip
source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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

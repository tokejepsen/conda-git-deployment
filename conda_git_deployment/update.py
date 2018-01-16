import os
import subprocess
import tempfile
import shutil

import utils
import environment


def update():

    # Update conda-git-deployment
    print("conda-git-deployment")
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    subprocess.call(["git", "pull"], cwd=path)


def initialise_git():

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    repo_url = "https://github.com/tokejepsen/conda-git-deployment.git"

    # Return early if already initialised.
    if ".git" in os.listdir(path):
        return

    try:
        print("Making conda-git-deployment into git repository.")

        # Copy .git directory from cloned repository
        tempdir = tempfile.mkdtemp()
        subprocess.call(["git", "clone", repo_url], cwd=tempdir)
        src = os.path.join(tempdir, "conda-git-deployment", ".git")
        dst = os.path.join(path, ".git")
        shutil.copytree(src, dst)

        # Initialising git repository
        subprocess.call(["git", "init"], cwd=path)
        subprocess.call(["git", "add", "."], cwd=path)
    except:
        print("Making conda-git-deployment into git repository failed.")
        shutil.rmtree(tempdir)


if __name__ == "__main__":

    # Install git if its not available
    if not utils.check_executable("git"):
        subprocess.call(["conda", "install", "-c", "conda-forge", "git", "-y"])

    # Configure git to checkout long file names.
    subprocess.call(["git", "config", "--system", "core.longpaths", "true"])

    # Git initialise
    initialise_git()

    # Git update
    if (utils.get_arguments()["update-environment"] or
       utils.get_arguments()["update-repositories"]):
        update()

    os.environ["CONDA_ENVIRONMENT_PATH"] = utils.get_arguments()["environment"]
    os.environ["CONDA_ENVIRONMENT_CWD"] = os.getcwd()

    environment.main()

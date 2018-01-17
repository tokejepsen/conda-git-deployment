import os
import subprocess

import utils
import environment


def update():

    # Update conda-git-deployment
    print("conda-git-deployment")
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    subprocess.call(["git", "pull"], cwd=path)


if __name__ == "__main__":

    # Install git if its not available
    if not utils.check_executable("git"):
        subprocess.call(["conda", "install", "-c", "conda-forge", "git", "-y"])

    # Git update
    if (utils.get_arguments()["update-environment"] or
       utils.get_arguments()["update-repositories"]):
        update()

    os.environ["CONDA_ENVIRONMENT_PATH"] = utils.get_arguments()["environment"]
    os.environ["CONDA_ENVIRONMENT_CWD"] = os.getcwd()

    environment.main()

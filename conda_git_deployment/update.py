import os
import subprocess
import sys

import utils


def main():

    # Install git if its not available
    if not utils.check_executable("git"):
        subprocess.call(["conda", "install", "-c", "anaconda", "git", "-y"])

    # Update conda-git-deployment
    print "conda-git-deployment"
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    subprocess.call(["git", "pull"], cwd=path)


if __name__ == "__main__":

    if (utils.get_arguments()["update-environment"] or
       utils.get_arguments()["update-repositories"]):
        main()

    # Setting update mode environment variable
    update_modes = []
    if utils.get_arguments()["update-environment"]:
        update_modes.append("environment")
    if utils.get_arguments()["update-repositories"]:
        update_modes.append("repositories")

    os.environ["CONDA_GIT_UPDATE"] = ""
    for mode in update_modes:
        os.environ["CONDA_GIT_UPDATE"] += mode + os.pathsep

    # Execute install
    args = [
        "python", os.path.join(os.path.dirname(__file__), "environment.py")
    ]

    args.extend(sys.argv[1:])

    subprocess.call(args)

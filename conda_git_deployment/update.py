import os
import subprocess

import utils


def main():

    # install git
    if not utils.check_executable("git"):
        subprocess.call(["conda", "install", "-c", "anaconda", "git", "-y"])

    # update conda-git-deployment
    print "conda-git-deployment"
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    subprocess.call(["git", "pull"], cwd=path)


if __name__ == "__main__":

    main()

    # execute install
    path = os.path.join(os.path.dirname(__file__), "install.py")
    subprocess.call(["python", path])

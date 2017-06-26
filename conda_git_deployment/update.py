import os
import subprocess
import sys
import tempfile
import shutil

import utils


def main():

    # Install git if its not available
    if not utils.check_executable("git"):
        subprocess.call(["conda", "install", "-c", "anaconda", "git", "-y"])

    # Update conda-git-deployment
    print "conda-git-deployment"
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    repo_url = "https://github.com/tokejepsen/conda-git-deployment.git"
    if ".git" not in os.listdir(path):
        try:
            print "Making conda-git-deployment into git repository."

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
            print "Making conda-git-deployment into git repository failed."
            shutil.rmtree(tempdir)

    subprocess.call(["git", "pull"], cwd=path)


if __name__ == "__main__":

    if (utils.get_arguments()["update-environment"] or
       utils.get_arguments()["update-repositories"]):
        main()

    # Execute install
    args = [
        "python", os.path.join(os.path.dirname(__file__), "environment.py")
    ]

    args.extend(sys.argv[1:])

    subprocess.call(args)

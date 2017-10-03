import os
import subprocess
import sys
import tempfile
import shutil

import utils


def update():

    # Update conda-git-deployment
    print "conda-git-deployment"
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    subprocess.call(["git", "pull"], cwd=path)


def initialise_git():

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


def purge_directories(root):

    if not os.path.exists(root):
        return

    errors = []
    for directory in os.listdir(root):
        path = os.path.join(root, directory)
        if not os.path.isdir(path):
            continue

        try:
            shutil.rmtree(path)
        except Exception as e:
            errors.append(e)

    if errors:
        if not utils.check_module("colorama"):
            subprocess.call(
                ["conda", "install", "-c", "anaconda", "colorama", "-y"]
            )
        from colorama import init, Fore, Style

        init(convert=True)

        print(Fore.RED + "Erros while purging trash:")
        for error in errors:
            print(Fore.RED + str(error))
        print(Style.RESET_ALL)


if __name__ == "__main__":

    # Install git if its not available
    if not utils.check_executable("git"):
        subprocess.call(["conda", "install", "-c", "anaconda", "git", "-y"])

    # Git initialise
    initialise_git()

    # Git update
    if (utils.get_arguments()["update-environment"] or
       utils.get_arguments()["update-repositories"]):
        update()

    # Purge unused files
    print "Purging trash..."
    path = os.path.abspath(
        os.path.join(sys.executable, "..", "pkgs", ".trash")
    )
    purge_directories(path)

    print "Purging extracted packages..."
    path = os.path.abspath(
        os.path.join(sys.executable, "..", "pkgs")
    )
    purge_directories(path)

    # Execute install
    args = [
        "python", os.path.join(os.path.dirname(__file__), "environment.py")
    ]

    args.extend(sys.argv[1:])

    subprocess.call(args)

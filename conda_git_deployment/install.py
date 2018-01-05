import os
import sys
import subprocess
import tempfile
import platform
from difflib import SequenceMatcher
import zipfile

import utils


def main():

    if not utils.check_executable("git"):
        subprocess.call(
            ["conda", "install", "-c", "anaconda", "git", "-y"]
        )

    # Export environment
    if (utils.get_arguments()["export"] or
       utils.get_arguments()["export-without-commit"]):
        environment_string = utils.get_environment_string()
        environment_data = utils.read_yaml(environment_string)

        repositories_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "repositories",
                environment_data["name"]
            )
        )

        # Get commit hash and name from repositories on disk.
        disk_repos = {}
        for repo in os.listdir(repositories_path):
            path = os.path.join(repositories_path, repo)
            if not os.path.exists(os.path.join(path, ".git")):
                continue

            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=path
            ).rsplit()[0]

            disk_repos[repo] = commit_hash

        # Construct new git dependencies.
        git_data = {"git": []}
        for item in environment_data["dependencies"]:
            if "git" in item:
                for repo in item["git"]:

                    # Get url from enviroment file.
                    url = ""
                    if isinstance(repo, str):
                        url = repo
                    if isinstance(repo, dict):
                        url = repo.keys()[0]

                    # Skip any repositories that aren't cloned yet.
                    name = url.split("/")[-1].replace(".git", "").split("@")[0]
                    if name not in disk_repos.keys():
                        continue

                    # Construct commit url if requested.
                    commit_url = url.split("@")[0]
                    if not utils.get_arguments()["export-without-commit"]:
                        commit_url += "@" + disk_repos[name]

                    if isinstance(repo, str):
                        git_data["git"].append(commit_url)

                    if isinstance(repo, dict):
                        git_data["git"].append({commit_url: repo[url]})

        # Replace git dependencies
        for item in environment_data["dependencies"]:
            if "git" in item:
                environment_data["dependencies"].remove(item)

        environment_data["dependencies"].append(git_data)

        # Lock down conda and pip dependencies
        locked_environment = utils.read_yaml(
            subprocess.check_output(["conda", "env", "export"], cwd=path)
        )

        dependencies = {}
        for dependency in environment_data["dependencies"]:
            if isinstance(dependency, str):
                dependencies[dependency.split("=")[0]] = ""
            if isinstance(dependency, dict):
                if "pip" not in dependency:
                    continue
                for pip_dependency in dependency["pip"]:
                    dependencies[pip_dependency.split("=")[0]] = ""

        for dependency in locked_environment["dependencies"]:
            if isinstance(dependency, str):
                name = dependency.split("=")[0]
                if name in dependencies:
                    dependencies[name] = dependency
            if isinstance(dependency, dict):
                if "pip" not in dependency:
                    continue
                for pip_dependency in dependency["pip"]:
                    name = pip_dependency.split("=")[0]
                    if name in dependencies:
                        dependencies[name] = pip_dependency

        for dependency in environment_data["dependencies"]:
            index = environment_data["dependencies"].index(dependency)
            if isinstance(dependency, str):
                version = dependencies[dependency.split("=")[0]]
                if version:
                    environment_data["dependencies"][index] = version
            if isinstance(dependency, dict):
                if "pip" not in dependency:
                    continue
                for pip_dependency in dependency["pip"]:
                    version = dependencies[pip_dependency.split("=")[0]]
                    if version:
                        pip_dict = environment_data["dependencies"][index]
                        pip_index = pip_dict["pip"].index(pip_dependency)
                        pip_dict["pip"][pip_index] = version

        # Write environment file
        utils.write_yaml(
            environment_data, os.path.join(os.getcwd(), "environment.yml")
        )

        # Export deployment
        print("Building deployment...")
        zip_file = zipfile.ZipFile("deployment.zip", "w", zipfile.ZIP_DEFLATED)

        exclude_dirs = [
            os.path.abspath(os.path.join(__file__, "..", "..", "installers")),
            os.path.abspath(
                os.path.join(__file__, "..", "..", "repositories")
            ),
        ]

        exclude_files = [
            os.path.abspath(
                os.path.join(__file__, "..", "..", "deployment.zip")
            ),
            os.path.abspath(
                os.path.join(__file__, "..", "..", "environment.yml")
            )
        ]

        path = os.path.abspath(os.path.join(__file__, "..", ".."))
        files_to_zip = []
        for root, dirs, files in os.walk(path, topdown=True):
            # Filter directories
            valid_dirs = []
            for d in dirs:
                if os.path.join(root, d) not in exclude_dirs:
                    valid_dirs.append(d)
            dirs[:] = valid_dirs

            for f in files:
                # Filter files
                if os.path.join(root, f) in exclude_files:
                    continue
                files_to_zip.append(os.path.join(root, f))

        root = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
        for f in files_to_zip:
            zip_file.write(f, os.path.relpath(f, root))

        zip_file.close()

        return

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
    cloned_repositories = False
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
                    cloned_repositories = True

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
    if utils.get_arguments()["update-repositories"] or cloned_repositories:
        for repo in repositories:
            print(repo["name"])

            # Updating origin url
            subprocess.call(
                [
                    "git",
                    "remote",
                    "set-url",
                    "origin",
                    repo["url"].split("@")[0]
                ],
                cwd=repo["path"]
            )

            # Update git repository
            subprocess.call(["git", "checkout", "master"], cwd=repo["path"])
            subprocess.call(["git", "pull"], cwd=repo["path"])

    # Checkout any commits/tags if there are newly cloned repositories or
    # updating the repositories.
    if utils.get_arguments()["update-repositories"] or cloned_repositories:
        for repo in repositories:
            if "@" in repo["url"]:
                tag = repo["url"].split("@")[1]
                if tag:
                    print(repo["name"])
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

            print(environment_repo["name"])
            branch = environment_path.split("/")[-2]
            subprocess.call(
                ["git", "checkout", branch], cwd=environment_repo["path"]
            )

    # Symlink repositories into environments "site-packages"
    symlink_directory = os.path.abspath(
        os.path.join(
            sys.executable, "..", "Lib", "site-packages", "repositories"
        )
    )

    if not os.path.exists(symlink_directory):
        os.makedirs(symlink_directory)

    for repository in repositories:
        path = os.path.join(symlink_directory, repository["name"])

        if os.path.exists(path):
            continue

        utils.symlink_directory(repository["path"], path)

    # Install any setup.py if we are updating
    if (utils.get_arguments()["update-repositories"] or
       utils.get_arguments()["update-environment"]):
        for repo in repositories:
            if "setup.py" not in os.listdir(repo["path"]):
                continue

            subprocess.call(
                ["python", "setup.py", "develop"],
                cwd=os.path.join(symlink_directory, repo["name"])
            )

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
                    print("Executing: " + cmd)
                    subprocess.call(
                        cmd, shell=True, cwd=repo["path"], **options
                    )

    # Execute launch commands.
    for repo in repositories:
        if "commands" in repo.keys():
            for cmd in repo["commands"]["on_launch"]:
                os.environ.update(utils.read_environment())
                cmd = cmd.replace("$REPO_PATH", repo["path"])
                print("Executing: " + cmd)
                subprocess.call(cmd, shell=True, cwd=repo["path"], **options)


if __name__ == "__main__":

    main()

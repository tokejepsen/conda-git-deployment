import os
import sys
import subprocess
from difflib import SequenceMatcher

import utils


def get_repositories_path():

    environment_string = utils.get_environment_string()
    environment_data = utils.read_yaml(environment_string)

    # Clone repositories. Using os.getcwd() because the drive letter needs to
    # be respected on Windows.
    return os.path.abspath(
        os.path.join(
            os.getcwd(), "repositories", environment_data["name"]
        )
    )


def get_repositories_data(repositories_path):
    environment_string = utils.get_environment_string()
    environment_data = utils.read_yaml(environment_string)

    repositories = []
    cloned_repositories = False
    for item in environment_data["dependencies"]:
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

    return repositories, cloned_repositories


def export():
    print "Exporting environment..."
    environment_string = utils.get_environment_string()
    environment_data = utils.read_yaml(environment_string)

    repositories_path = get_repositories_path()

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
        subprocess.check_output(["conda", "env", "export"])
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

    utils.write_yaml(environment_data, "environment.yml")


def main():

    if not utils.check_executable("git"):
        subprocess.call(
            ["conda", "install", "-c", "anaconda", "git", "-y"]
        )

    # Export environment
    if (utils.get_arguments()["export"] or
       utils.get_arguments()["export-without-commit"]):
        export()
        return

    os.remove(utils.get_arguments()["unknown"][0])

    # The activation script will point to a non-existent file, so we need to
    # change where it gets the environment data from.
    os.environ["CONDA_ENVIRONMENT_CWD"] = os.getcwd()
    os.environ["CONDA_ENVIRONMENT_PATH"] = utils.get_arguments()["environment"]

    repositories_path = get_repositories_path()

    # Update repositories.
    repositories, cloned_repositories = get_repositories_data(
        repositories_path
    )
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

    # Checkout any commits/tags
    for repo in repositories:
        if "@" in repo["url"]:
            tag = repo["url"].split("@")[1]
            if tag:
                print(repo["name"])
                subprocess.call(["git", "checkout", tag], cwd=repo["path"])

    # Checkout environment repository
    environment_path = utils.get_arguments()["environment"]
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

    # Clean up any existing environment file
    if os.path.exists(utils.get_environment_path()):
        os.remove(utils.get_environment_path())

    # Setting update mode environment variable
    update_modes = []
    if utils.get_arguments()["update-environment"]:
        update_modes.append("environment")
    if utils.get_arguments()["update-repositories"]:
        update_modes.append("repositories")

    os.environ["CONDA_GIT_UPDATE"] = ""
    for mode in update_modes:
        os.environ["CONDA_GIT_UPDATE"] += mode + os.pathsep

    run_commands()


def merge_environments(source, target):

    results = {}

    for d in [source, target]:
        for key, value in d.iteritems():
            if key in results.keys():
                for path in value.split(os.pathsep):
                    if path not in results[key]:
                        results[key] += os.pathsep + path
            else:
                results[key] = value

    return results


def run_commands():

    import json
    print json.dumps(dict(os.environ), indent=4, sort_keys=True)
    print bool(os.getenv("CONDA_SKIP_COMMANDS"))
    if bool(os.getenv("CONDA_SKIP_COMMANDS")):
        return

    repositories_path = os.path.abspath(
        os.path.join(
            sys.executable, "..", "Lib", "site-packages", "repositories"
        )
    )

    os.environ["CONDA_ENVIRONMENT_REPOSITORIES"] = repositories_path
    os.environ["CONDA_GIT_REPOSITORY"] = repositories_path

    # Execute environment update commands.
    repositories = get_repositories_data(repositories_path)[0]

    # Ensure subprocess is detached so closing connect will not also
    # close launched applications.
    options = {}

    if not bool(os.getenv("CONDA_ATTACHED")):
        if sys.platform == "win32":
            options["creationflags"] = subprocess.CREATE_NEW_CONSOLE
        else:
            options["preexec_fn"] = os.setsid

    # Add environment site packages to os.environ
    path = os.path.abspath(
        os.path.join(sys.executable, "..", "Lib", "site-packages")
    )
    os.environ["PYTHONPATH"] += os.pathsep + path

    # Add sys.path to environment
    for path in sys.path:
        if path.lower().startswith(repositories_path.lower()):
            os.environ["PYTHONPATH"] += os.pathsep + path
        if path.endswith(".egg"):
            os.environ["PYTHONPATH"] += os.pathsep + path

    # Execute environment update commands
    utils.write_environment({})
    if utils.get_arguments()["update-environment"]:
        for repo in repositories:
            if "commands" in repo.keys():
                for cmd in repo["commands"]["on_environment_update"]:
                    os.environ.update(
                        merge_environments(
                            os.environ, utils.read_environment()
                        )
                    )
                    cmd = cmd.replace("$REPO_PATH", repo["path"])
                    print("Executing: " + cmd)
                    subprocess.call(
                        cmd,
                        shell=True,
                        cwd=repo["path"],
                        **options
                    )

    # Execute launch commands.
    utils.write_environment({})
    for repo in repositories:
        if "commands" in repo.keys():
            for cmd in repo["commands"]["on_launch"]:
                os.environ.update(
                    merge_environments(
                        os.environ, utils.read_environment()
                    )
                )
                cmd = cmd.replace("$REPO_PATH", repo["path"])
                print("Executing: " + cmd)
                subprocess.call(
                    cmd,
                    shell=True,
                    cwd=repo["path"],
                    **options
                )


if __name__ == "__main__":

    main()

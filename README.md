# conda-git-deployment

**NOTE: Linux/OSX is not supported yet.**

## Goal

Simplify deploying git based repositories.

## Responsibilities

In order to accurately mirror an environment with git repositories, this project has to take on some responsibilities;

- Git cloning/updating.
- Environment handling.
- Command execution.

## Dependencies

This package does not have any dependencies on external packages or modules. It downloads all required files. However this means that an internet connection is required.

Once a deployment has been run on various platforms (Windows, Linux and OSX), all dependencies should be downloaded and the entire folder can be shared without an internet connection required.

## Usage

Download the package from https://github.com/tokejepsen/conda-git-deployment/archive/master.zip, and extract.

At the basic level you can use this project to just setup Conda and experiment with the root environment. Just execute the following command:

```
$ cd /path/to/conda-git-deployment
$ startup --environment root
```

This package is about deploying git repositories, so let's try with the example environment:

```
$ cd /path/to/conda-git-deployment
$ startup --environment https://raw.githubusercontent.com/tokejepsen/conda-git-example/master/environment.yml --attached
```

The conda-git-example environment downloads itself and executes the ```environment.py``` file inside the repository with a separate environment specific python executable.

Let's have a look at what is happening.

The environment files follow the standard conda environment files syntax; https://conda.io/docs/using/envs.html#create-environment-file-by-hand, with the added ```git``` element. Here is the conda-git-example environment:

```yaml
name: conda-git-example
dependencies:
- python=2.7
- git:
  - https://github.com/tokejepsen/conda-git-example.git:
    - python $REPO_PATH/environment.py
```

The name of the environment is reflected in the conda environment, but also in the root directory of the repositories an environment contains.  
By default all repositories gets cloned to ```/path/to/conda-git-deployment/repositories/[name of environment]```.

The ```git``` element of the environment is a list of git repository urls, that can contains commands to execute. All commands are executed in the created environment.
In the environment example above, the command; ```python $REPO_PATH/environment.py```, execute the environment python with the repository's ```environment.py``` file. ```$REPO_PATH``` is a special token for getting to the repository's path.

The list of git repositories does not have to contain commands, as the following:

```yaml
name: conda-git-example
dependencies:
- python=2.7
- git:
  - https://github.com/tokejepsen/conda-git-example.git
```

This will just create the environment and clone the conda-git-example repository.

You can also take over the installation process yourself by defining the commands to execute on updating the environment:
```yaml
name: conda-git-example
dependencies:
- python=2.7
- git:
  - https://github.com/tokejepsen/conda-git-example.git:
    - on_environment_update:
      - python -c "print \"Building the repository myself.\""
    - python $REPO_PATH/environment.py
```

### Execution Stages

1. Conda installation.
 - [Miniconda](https://conda.io/miniconda.html) get downloaded and installed.
2. ```conda-git-deployment``` initialized.
 - The ```conda-git-deployment``` directory gets turned into a git reposity.
3. ```conda-git-deployment``` updated.
 - ```conda-git-deployment``` gets updated to the latest version no matter what.
4. Environment creation.
 - A conda environment gets created either from a local or remote environment file.
 - Any ```pip``` commands in the file gets executed on environment creation.
5. Repositories cloning.
 - All repositories in the environment file gets cloned local to the ```conda-git-deployment``` directory.
6. Repositories updating.
 - All repositories get updated to the latest commit.
7. Repositories checkout.
 - All repositories with a commit hash gets checked out to that commit hash.
8. Repositories installation.
 - Any repositories with a ```setup.py``` file gets installed in the development mode.
9. Repositories command execution.
 - All repositories command list gets executed.


### Environment variables

Through the deployment process a number of environment variables are set, to facilitate access across processes.

#### ```PYTHONPATH```

The conda_git_deployment module is added, so it available to import.

All the modules installed during deployment, including any modules installed with ```setup.py``` inside a repository, will be available to import.

#### ```CONDA_ENVIRONMENT_REPOSITORIES```

This is the path to the environments cloned repositories on disk.

#### ```CONDA_GIT_UPDATE```

This is a variable that shows what updating mode, the deployment is in. Available modes are;

Mode | Description
--- | ---
"repositories" | Updating the repositories
"environment" | Updating the environment

The update modes can be combined, in which case they are split by the OS's path separator.

```python
print os.environ["CONDA_GIT_UPDATE"].split(os.sep)
```

**NOTE: If no updating is happening, the environment variable will not be available.**

### Arguments

To facilitate different uses the ```startup``` executables has a number of arguments.

Argument | Description | Example
--- | --- | ---
environment | Environment file to process. | ```startup --environment https://raw.githubusercontent.com/tokejepsen/conda-git-example/master/environment.yml```
attached | Spawn non-detached processes. | ```startup --attached --environment https://raw.githubusercontent.com/tokejepsen/conda-git-example/master/environment.yml```
update-environment | Update and rebuild environment. | ```startup --update-environment --environment https://raw.githubusercontent.com/tokejepsen/conda-git-example/master/environment.yml```
update-repositories | Update and rebuild repositories. | ```startup --update-repositories --environment https://raw.githubusercontent.com/tokejepsen/conda-git-example/master/environment.yml```
export | Exports the environment. | ```startup --export --environment https://raw.githubusercontent.com/tokejepsen/conda-git-example/master/environment.yml```
export-without-commit | Exports the environment, without commit ids. | ```startup --export-without-commit --environment https://raw.githubusercontent.com/tokejepsen/conda-git-example/master/environment.yml```
suppress-environment-update | If there are changes to the environment, this flag will suppress the environment update. | ```startup --suppress-environment-update --environment https://raw.githubusercontent.com/tokejepsen/conda-git-example/master/environment.yml```

## Utilities

**update.bat**

This batch script updates both the environment and the repositories. The same as the following

```startup --update-environment --update-repositories```

**update-environment.bat**

This batch script updates only the environment. The same as the following

```startup --update-environment```

**update-repositories.bat**

This batch script updates only the repositories. The same as the following

```startup --update-repositories```

# conda-git-deployment

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
$ startup --environment https://raw.githubusercontent.com/tokejepsen/conda-git-example/master/environment.yml
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
"" | No updating
"update-repositories" | Updating the repositories
"update-environment" | Updating the environment

The update modes can be combined, in which case they are split by the OS's path separator.

```python
print os.environ["CONDA_GIT_UPDATE"].split(os.sep)
```

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

## Location

Once the environment has been built in a location on disk, if you move the folder to a different location on disk, you will have to rebuild the environment.

***NOTE: UNC paths are not supported currently.***

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

# conda-git-deployment

**Goal**

To simplify deploying git based repositories.

**Dependencies**

This package does not have any dependenies on external packages or modules. It downloads all required files. However this means that an internet connection is required.

Once a deployment has been run on various platforms (Windows, Linux and OSX), all dependencies should be downloaded and the entire folder can be shared without an internet connection required.

**Usage**

Create an environment yaml file in the repository, or modify ```environment.yml.example``` and rename to ```environment.yml```.

The environment file follows this syntax;

```yaml
dependencies:
   - git:
     - "https://github.com/tokejepsen/conda-git-example.git":
        - "python $REPO_PATH/startup.py"
     - "https://github.com/pyblish/pyblish-base.git"
```

You can add git repositories (remote or local), which will be cloned and updated when ever the deployment is started.  
You start the deployment by double-clicking the ```startup.bat``` on Windows, or running the ```startup.bat``` file in a terminal. OSX and Linux will follow later.

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
```

*Window* - You start the deployment by double-clicking the ```startup.bat``` on Windows, or running the ```startup.bat``` file in a terminal.

*Linux* - You start the deployment by executing this in a terminal; ```sh path/to/repository/startup.sh```.

*OSX* - Coming soon.

Using the example above will download the ```https://github.com/tokejepsen/conda-git-example.git``` repository, and execute the ```startup.py``` file inside. ```startup.py``` is dependent on PySide being installed, so it installs PySide with conda and displays a "Hello World" PySide window.

You can add git repositories (remote or local), which will be cloned and updated when ever the deployment is started.

# Tutorial: Install

Use this tutorial to get the Learning Observer running on your machine. It walks you through the exact commands to run and the order to run them in, so you can follow along step by step.

As you set things up, keep in mind that Learning Observer functions as an application platform: the core `learning_observer` package starts the services and loads modules, and each module contributes dashboards, reducers, or other features that run on top of that core.

## Before you begin

Make sure your computer meets these requirements:

1. **Operating system** – A Unix-style system works best. We regularly test on Ubuntu. macOS generally works as well. Windows users should install the project inside [Windows Subsystem for Linux (WSL)](../workshop/wsl-install.md) before continuing.
2. **Python** – Install Python 3.10 or 3.11 (any version newer than 3.9 is expected to work).
3. **Package manager (recommended)** – Have a virtual environment tool ready. We prefer [`virtualenvwrapper`](https://pypi.org/project/virtualenvwrapper/), but you can use `python -m venv`, Conda, or another tool you like.
4. **Optional tools** –
   - [Valkey](https://valkey.io/) or Redis as a key–value store if you plan to run production-style deployments (this tutorial uses on-disk storage instead).
   - Docker 26.1 if you want to experiment with the container-based workflow. The steps below focus on the native installation.

Have two terminal windows or tabs open. We will run the server in one and use the other for helper scripts.

## Step 1 – Download the project

1. Open a terminal and clone the repository:

   ```bash
   git clone https://github.com/ArgLab/writing_observer.git lo_tutorial
   ```

   If you have an SSH key configured with GitHub, you can use:

   ```bash
   git clone git@github.com:ArgLab/writing_observer.git lo_tutorial
   ```

2. Change into the new directory:

   ```bash
   cd lo_tutorial/
   ```

   All commands that follow run from this repository root unless the tutorial notes otherwise.

## Step 2 – Create and activate a Python environment

Choose one of the options below to create an isolated environment for the tutorial.

*With `virtualenvwrapper`:*

```bash
mkvirtualenv lo_env
workon lo_env
```

*With `venv` (built into Python):*

```bash
python -m venv lo_env
source lo_env/bin/activate
```

Verify that the shell prompt shows the environment name before continuing.

```bash
(lo_env) user@pc:~/lo_tutorial$
```

## Step 3 – Install Python dependencies

1. Make sure `pip` itself is up to date (optional but helpful):

   ```bash
   pip install --upgrade pip
   ```

2. Install all project requirements:

   ```bash
   make install
   ```

   This command downloads Python packages and builds local assets. Depending on your network speed, it can take a few minutes.

## Step 4 – Apply the workshop configuration

The project ships with an example configuration tailored for workshops. Copy it into place so the application starts with sensible defaults such as file-based storage and relaxed authentication.

```bash
cp learning_observer/learning_observer/creds.yaml.workshop learning_observer/creds.yaml
```

If you are curious about the changes, compare it with the example file:

```bash
diff -u learning_observer/learning_observer/creds.yaml.example learning_observer/creds.yaml
```

## Step 5 – Start the Learning Observer

1. Launch the development server:

   ```bash
   make run
   ```

2. The first run performs several setup tasks (such as generating role files), so it may exit after downloading dependencies. When the command finishes, run it again:

   ```bash
   make run
   ```

   Repeat until the command reports that the system is ready and stays running.

## Step 6 – Verify everything worked

Once the server is running, open a browser and go to one of the following URLs:

- `http://localhost:8888/`
- `http://0.0.0.0:8888/`
- `http://127.0.0.1:8888/`

You should see the Learning Observer dashboard with a list of courses and analytics modules. Because the workshop configuration disables authentication, you can immediately click around and start experimenting.

## Next steps

- Explore the [cookiecutter module tutorial](cookiecutter-module.md) to scaffold a package from the template.
- Review [system settings concepts](../concepts/system_settings.md) before deploying beyond a simple setup.

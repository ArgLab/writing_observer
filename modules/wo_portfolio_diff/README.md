# Learning Observer Example Module

Welcome to the Learning Observer (LO) example module. This document
will detail everything need to create a module for the LO.

## packaage structure

```bash
module/
  wo_portfolio_diff/
    assets/
      ...
    module.py
    reducers.py
    dash_dashboards.py
    utils.py
  tests/
    test_utils.py
  MANIFEST.in
  setup.cfg
  pyproject.toml
  VERSION
```

### setup.cfg

Notice we include the following items in our `setup.cfg` file.

```cfg
[options.entry_points]
lo_modules =
   wo_portfolio_diff = wo_portfolio_diff.module

[options.package_data]
wo_portfolio_diff = helpers/*
```

The `lo_modules` entry point tells Learning Observer to treat `wo_portfolio_diff.module` as a pluggable application.

The package data section is where we include additional directories we want included in the build.

### pyproject.toml

The `pyproject.toml` file specifies the build system, which in this case is `setuptools`. It works alongside the `setup.cfg` file to provide metadata for the installation process.

### MANIFEST.in

The manifest specifies which files to include during Python packaging. This specifies the additional non-python files we want included. If you do not have additional files needed, this file is unnecessary.

For modules with Dash-made dashboards, this will typically include a relative path to the assets folder.

### VERSION

The VERSION file specifies the version of the package. Each one defaults to `0.1.0`.

### module.py

This file defines everything about the module. See the dedicated section below.

## Defining a module (module.py)

Modules can include a variety items. This will cover each item and its purpose on the system.

### NAME

This one is pretty self explanatory. Give the module a short name to refer to it by.

### EXECUTION_DAG

The execution directed acyclic graph (DAG) is how we interact with the communication protocol.

See `wo_portfolio_diff/module.py:EXECUTION_DAG` for a detailed example.

### REDUCERS

Reducers to define on the system. These are functions that will run over incoming events from students.

See `wo_portfolio_diff/module.py:REDUCERS` for a detailed example.

### DASH_PAGES

Dashboards built using the Dash framework should be defined here.

See `wo_portfolio_diff/module.py:DASH_PAGES` for a detailed example.

### COURSE_DASHBOARDS

The registered course dashboards are provided to the users for navigating around dashboards, such as on their Home screen.

See `wo_portfolio_diff/module.py:COURSE_DASHBOARDS` for a detailed example.

Note that the student counterpart, `STUDENT_DASHBOARDS`, exists.

### THIRD_PARTY

The third party items are downloaded and included when serving items from the module. This is usually used for including extra Javascript or CSS files.

```python
THIRD_PARTY = {
    'name_of_item': {
        'url': 'url_to_third_party_tool',
        'hash': 'hash_of_download_OR_dict_of_versions_and_hashes'
    }
}
```

### STATIC_FILE_GIT_REPOS

We're still figuring this out, but we'd like to support hosting static files from the git repo of the module.
This allows us to have a Merkle-tree style record of which version is deployed in our log files.

A common use case for this is serving static `.html` and `.js` files for your module.

```python
STATIC_FILE_GIT_REPOS = {
    'repo_name': {
        'url': 'url_to_repo',
        'prefix': 'relative/path/to/directory',
        # Branches we serve. This can either be a whitelist (e.g. which ones
        # are available) or a blacklist (e.g. which ones are blocked)
        'whitelist': ['master']
    }
}
```

### EXTRA_VIEWS

These are extra views to publish to the user. Currently, we only support `.json` files.

```python
EXTRA_VIEWS = [{
    'name': 'Name of view',
    'suburl': 'view-suburl',
    'static_json': python_dictionary_to_return
}]
```

## Creating a reducer (reducers.py)

Reducers are ran over incoming student events. They can be defined using a decorator in the `learning_observer.stream_analytics` module.

Each reducer should take the incoming `event` and the previous `internal_state` as parameters and return 2 new state objects.

## Creating dashboards with Dash (dash_dashboard.py)

Dash pages consist of a layout and callback functions. See `dash_dashboard.py` for a more detailed overview.

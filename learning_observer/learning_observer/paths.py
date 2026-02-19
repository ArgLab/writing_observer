'''
Path hierarchy
==============

Helper utility to help manage paths. We'd like to abstract out path
configurations so that the tool can work in:

1. Deployed settings
2. pip installs
3. Development mode

... etc.

This abstracts out finding files and directories. Eventually, we'd
like to be able to search for packages looking at:

- Relative directories (e.g. when developing)
- Static directories (e.g. /etc/, /var/log/, etc.)
- Config file
- pkg_resources
- Command-line parameters

It makes sense to put this logic one place.

Should this be merges with settings.py? Let's see how complex this gets.
'''

import errno
import os
import os.path
import sys


BASE_PATH = os.path.abspath(os.path.dirname(__file__))
PYTHON_EXECUTABLE = sys.executable

# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportError("Please use fully-qualified imports")
    sys.exit(-1)


def base_path(filename=None):
    '''
    Should NOT be used, except by filesystem_state. Use one of the helpers below.
    '''
    if filename is None:
        return BASE_PATH
    return os.path.join(BASE_PATH, filename)


def config_file():
    '''
    Main configuration file
    '''
    pathname = os.path.join(os.path.dirname(base_path()), 'creds.yaml')
    # TODO: This is cut-and-paste from settings.py.
    #
    # It should be one place.
    #
    # The move to pmss moved loading settings into the import
    # statement of settings.py, which is probably a mistake, as in
    # some cases, we want to import files without triggering all
    # this machinery, or use alternative settings. A simple import
    # should not lead to this exception in the future.
    #
    # But here we are, and until we're out of here, this is temporary
    # code to let us know what's failing.
    if not os.path.isfile(pathname):
        print(
            "Configuration file not found: {config_file}\n"
            "\n"
            "Copy the example file into:\n"
            "{config_file}\n\n"
            "And then continue setup\n"
            "The command is probably:\n"
            "cp {sourcedir}/creds.yaml.example {dest}\n\n"
            "The file will then need to be customized for your install".format(
                sourcedir=os.path.dirname(os.path.abspath(__file__)),
                dest=pathname,
                config_file=pathname
            )
        )
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), pathname)

    return pathname


DATA_PATH_OVERRIDE = None


def override_data_path(new_path):
    '''
    We'd like to be able to serve data files from alternative
    locations, especially for testing
    '''
    global DATA_PATH_OVERRIDE
    if not new_path.startswith("/"):
        DATA_PATH_OVERRIDE = base_path(new_path)
    else:
        DATA_PATH_OVERRIDE = new_path


def data(filename=None):
    '''
    File from the static data directory. No parameters: data directory.
    '''
    pathname = base_path('static_data')
    if DATA_PATH_OVERRIDE is not None:
        pathname = DATA_PATH_OVERRIDE
    if filename is not None:
        pathname = os.path.join(pathname, filename)
    return pathname


GIT_REPO_ARCHIVE = {}


def repo(reponame=None):
    '''
    We keep downloaded `git` repos from modules in the static data
    directory. This returns the base path of a `git` repo.

    `git` repos may also be stored other places.
    '''
    if reponame in GIT_REPO_ARCHIVE:
        return GIT_REPO_ARCHIVE[reponame]['PATH']
    pathname = data("repos")
    if reponame is not None:
        pathname = os.path.join(pathname, reponame)
    return pathname


def repo_debug_working_hack(reponame):
    '''
    For debugging, we want to allow serving from the git working dir.

    Just not like this.... We should do the merge in settings.py or
    module_loader, or somewhere else.

    Right now, we allow us to override whether a repo can be served
    from the working dir in the settings file. This is set by
    settings.py, which needs to be loaded after paths.py.

    `True` and `False` are overrides. `None` is the default if not
    set.
    '''
    if reponame in GIT_REPO_ARCHIVE and 'DEBUG_WORKING' in GIT_REPO_ARCHIVE[reponame]:
        return GIT_REPO_ARCHIVE[reponame]['DEBUG_WORKING']
    return None


def register_repo(reponame, path, debug_working=None):
    '''
    Let the system know the location of a repo on the local drive

    `debug_working` is a HACK. The setting is fine, but this does
    not belong in paths.py
    '''
    GIT_REPO_ARCHIVE[reponame] = {
        "PATH": path,
        "DEBUG_WORKING": debug_working
    }


def logs(filename=None):
    '''
    Log file. No parameters: log directory.
    '''
    pathname = base_path('logs')
    if filename is not None:
        pathname = os.path.join(pathname, filename)
    return pathname


def static(filename=None):
    '''
    This is where we store and serve our own static files
    from. Ideally, our web server should serve these for us, but for
    development and small-scale deploys, it's convenient to be able to
    do it ourselves too.
    '''
    pathname = base_path('static')
    if filename is not None:
        pathname = os.path.join(pathname, filename)
    return pathname


def third_party(filename=None):
    '''
    This is where we download 3rd party Javascript, CSS, and similar
    files to (e.g., D3, Bulma, etc.)
    '''
    pathname = static('3rd_party')
    if filename is not None:
        pathname = os.path.join(pathname, filename)
    return pathname


def dash_assets(filename=None):
    '''
    We are standardizing on `dash` for serving dashboards.

    Perhaps, though, extensions should have data directories, and
    this should be made into one for dash?
    '''
    pathname = data('dash_assets')
    if filename is not None:
        pathname = os.path.join(pathname, filename)
    return pathname

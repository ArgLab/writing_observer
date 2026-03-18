'''
This is at the edge of dev-ops and operations. We would like to:
- Confirm that the system is ready to run the Learning Observer.
- Create directories for log files, etc.
- Validate the teacher list file.
- Validate the configuration file exists.
- Download any missing 3rd party files.
- Confirm their integrity.
- Create any directories that don't exist.
'''

from distutils.log import debug
import hashlib
import os
import os.path
import requests
import shutil
import sys
import uuid

import learning_observer.paths as paths
import learning_observer.settings as settings


STARTUP_CHECKS = []
INIT_FUNCTIONS = []
STARTUP_RAN = False


class StartupCheck(Exception):
    '''
    Exception to be raised when a startup check fails.
    '''
    pass


def register_startup_check(check):
    '''
    Allow modules to register additional checks beyond those defined here. This
    function takes a function that takes no arguments and returns nothing which
    should run after settings are configured, but before the server starts.
    '''
    if STARTUP_RAN:
        raise StartupCheck(
            "Cannot register additional checks after startup checks have been run."
        )
    STARTUP_CHECKS.append(check)
    return check


def register_init_function(init):
    '''
    Allow modules to initialize modules after settings are loaded and startup checks have
    run. This function takes a function that takes no arguments and returns nothing which
    should run before the server starts.
    '''
    if STARTUP_RAN:
        raise StartupCheck(
            "Cannot register additional checks after startup checks have been run."
        )
    INIT_FUNCTIONS.append(init)
    return init


# These are directories we'd like created on startup. At the moment,
# they're for different types of log files.
DIRECTORIES = {
    'logs': {'path': paths.logs()},
    'startup logs': {'path': paths.logs('startup')},
    'AJAX logs': {'path': paths.logs('ajax')},
    '3rd party': {'path': paths.third_party()},
    'dash assets': {'path': paths.dash_assets()}
}


@register_startup_check
def make_blank_dirs():
    '''
    Create any directories that don't exist for e.g. log files and
    similar.
    '''
    for d in DIRECTORIES:
        dirpath = DIRECTORIES[d]['path']
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
            print("Made {dirname} directory in {dirpath}".format(
                dirname=d,
                dirpath=dirpath
            ))


@register_startup_check
def validate_config_file():
    '''
    Validate the configuration file exists. If not, explain how to
    create a configuration file based on the example file.
    '''
    if not os.path.exists(paths.config_file()):
        raise StartupCheck(
            "No configuration file found.\n"
            "Copy creds.yaml.sample into the top-level directory:\n"
            "cp creds.yaml.sample ../creds.yaml\n"
            "Fill in the missing fields."
        )


@register_startup_check
def download_3rd_party_static():
    '''
    Download any missing third-party files, and confirm their integrity.
    We download only if the file doesn't exist, but confirm integrity
    in both cases.
    '''
    # We do this import inside to prevent circular imports
    import learning_observer.module_loader as module_loader
    libs = module_loader.third_party()

    def format_hash(hash_string):
        return hash_string[:61] + '\n' + hash_string[61:]

    file_integrity_errors = []

    for name in libs:
        url = libs[name]['urls'][0]
        sha = libs[name]['hash']

        if sha is None:
            error = "No SHA hash set in module for {name}. It should probably be:\n\t{hash}".format(
                name=filename,
                hash=format_hash(shahash)
            )
            raise StartupCheck(error)

        # In most cases, there's just one hash.
        #
        # We support a list or a dictionary if we want multiple
        # versions to all work. The keys in the dictionary are just
        # documentation for now.
        if isinstance(sha, list):
            hashes = sha
        elif isinstance(sha, dict):
            hashes = sha.values()
        else:
            hashes = [sha]

        filename = paths.third_party(name)

        # For subdirectories, make them
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if not os.path.exists(filename):
            # TODO: For larger downloads, we might want to set
            # stream=True and use iter_content instead
            response = requests.get(url)
            if response.status_code == 200:
                with open(filename, 'wb') as file:
                    file.write(response.content)
                    print("Downloaded {name}".format(name=name))
            else:
                print("Failed to download file")

            print("Downloaded {name}".format(name=name))
        shahash = hashlib.sha3_512(open(filename, "rb").read()).hexdigest()
        if shahash not in hashes:
            file_integrity_errors.append({
                "file": name,
                "local_file": filename,
                "expected_sha": sha,
                "actual_sha": shahash,
                "top_line": shahash[:61],
                "bottom_line": shahash[61:],
                "url": url,
                "dashboards": ", ".join(libs[name]['users'])
            })

    if file_integrity_errors:
        header = \
            "We download 3rd party libraries from the Internet. This error means that ones of\n" \
            "or more of these files changed. This may indicate:\n" \
            "* A man-in-the-middle attack or that a CDN has been compromised\n" \
            "* That one of the files had something like a security fix backported, a bug fixed\n" \
            "* That a file was not version-locked, and a new version of a library is available (common in dev)\n"\
            "In either case, please verify file integrity and function (a changed file CAN introduce a bug. If\n"\
            "unsure, please consult with a security expert.\n\n" \
            "Issues:\n\n"
        indent = ' ' * 28
        change = \
            '{file}'\
            'URL: {url}'\
            'File: {local_file}\n' \
            'Expected: {expected_sha}\n' \
            'Got: {actual_sha}\n' \
            'If this is correct, please add these lines:\n' \
            + indent + '"[new version name]": "{top_line}"\n' \
            + indent + '"{bottom_line}"\n' \
            'to the module.py for {dashboards}'
        issues_formatted = "\n====\n".join([change.format(**fie) for fie in file_integrity_errors])
        raise StartupCheck(f"{header}{issues_formatted}")


def preimport():
    '''
    This will import all of the files which use the register_init_function
    or register_startup_check decorators.
    '''
    path = os.path.dirname(os.path.realpath(__file__))
    # Walk the directory tree
    for root, dirs, files in os.walk(path):
        # For each file, if it's a .py file, import it
        for f in files:
            # Only handle Python files
            if not f.endswith(".py"):
                continue
            if f.startswith("__"):
                continue
            if f.startswith("."):
                continue
            if "#" in f:
                continue

            # Skip directories which aren't part of the system
            SKIP = ["static_data", "prototypes"]
            if any(s in root for s in SKIP):
                continue

            # Skip files which don't use the decorator
            DECORATORS = ["register_init_function", "register_startup_check"]
            with open(os.path.join(root, f)) as fp:
                code = fp.read()
                if not any(d in code for d in DECORATORS):
                    continue

            # Strip the .py extension
            f = f[:-3]
            # Import the file
            relpath = os.path.relpath(root, path).replace(os.sep, ".")
            module_name = ".".join(["learning_observer", relpath, f])
            while ".." in module_name:
                module_name = module_name.replace("..", ".")

            try:
                print(f"Importing {module_name}")
                __import__(module_name)
            except ImportError as e:
                print("Error importing {f}".format(f=f))
                print(e)


def startup_checks_and_init():
    '''
    Run a series of checks to ensure that the system is ready to run
    the Learning Observer and create any directories that don't exist.

    We should support asynchronous functions here, but that's a to do. Probably,
    we'd introspect to see whether return values are promises, or have a
    register_sync and a register_async.

    This function should be called at the beginning of the server.

    In the future, we'd like to have something where we can register with a
    priority. The split between checks and intialization felt right, but
    refactoring code, it's wrong. We just have things that need to run at
    startup, and dependencies.
    '''
    preimport()
    exceptions = []
    for check in STARTUP_CHECKS:
        try:
            check()
        except StartupCheck as e:
            exceptions.append(e)
    if exceptions:
        print("Could not start the Learning Observer")
        for e in exceptions:
            print("-------------------")
            print(e)
            if len(e.args) > 0:
                print(e.args[0])
        sys.exit(1)

    for init in INIT_FUNCTIONS:
        init()
    STARTUP_RAN = True


@register_startup_check
def check_aio_session_settings():
    if 'aio' not in settings.settings or \
       'session_secret' not in settings.settings['aio'] or \
       isinstance(settings.settings['aio']['session_secret'], dict) or \
       'session_max_age' not in settings.settings['aio']:
        raise StartupCheck(
            "Settings file needs an `aio` section with a `session_secret`\n"
            "subsection containing a secret string. This is used for\n"
            "security, and should be set once for each deploy of the platform\n"
            "(e.g. if you're running 10 servers, they should all have the\n"
            "same secret)\n\n"
            "Please set an AIO session secret in creds.yaml\n\n"
            "Please pick a good session secret. You only need to set it once, and\n"
            "the security of the platform relies on a strong, unique password there\n\n"
            "This sessions also needs a session_max_age, which sets the number of seconds\n"
            "of idle time after which a user needs to log back in. 4320 should set\n"
            "this to 12 hours.\n\n"
            "This should be a long string of random characters. If you can't think\n"
            "of one, here's one:\n\n"
            "aio:\n"
            "    session_secret: {secret}\n"
            "    session_max_age: 4320".format(
                secret=str(uuid.uuid5(uuid.uuid1(), str(uuid.uuid4())))
            )
        )

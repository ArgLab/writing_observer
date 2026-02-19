'''
This allows us to capture what state we start the server in, for
replicability. We'd like to work from SHA hashes eventually.

We'll probably want something like:

FILESTRING = """{filename}:
\thash:{hash}
\tst_mode:{st_mode}
\tst_size:{st_size}
\tst_atime:{st_atime}
\tst_mtime:{st_mtime}
\tst_ctime:{st_ctime}
"""
'''
import aiohttp
import datetime
import hashlib
import os
import platform
import socket
import subprocess

import learning_observer.paths as paths


extensions = [
    ".py",
    ".js",
    ".html",
    ".md"
]


def filesystem_state():
    '''
    Make a snapshot of the file system. Return a json object. Best
    usage is to combine with `yaml.dump`, or `json.dump` with a
    specific indent. This is helpful for knowing which version was running.

    Snapshot contains list of Python, HTML, JSON, and Markdown files,
    together with their SHA hashes and modified times. It also
    contains a `git` hash of the current commit.

    This ought to be enough to confirm which version of the tool is
    running, and if we are running from a `git` commit (as we ought to
    in production) or if changes were made since git commited.
    '''
    file_info = {}
    # We need have dirs, even if we don't use it.
    # pylint: disable=W0612
    for root, dirs, files in os.walk(paths.base_path()):
        for name in files:
            for extension in extensions:
                # Check if the file has an appropriate extension, and
                # is not a temporary file or backup.
                if name.endswith(extension) and \
                   "#" not in name and \
                   "~" not in name and \
                   not name.startswith("."):
                    filename = os.path.join(root, name)
                    stat = os.stat(filename)
                    file_info[filename] = {
                        "hash": hashlib.sha3_512(open(filename, "rb").read()).hexdigest(),
                        "st_mode": stat.st_mode,
                        "st_size": stat.st_size,
                        "st_atime": stat.st_atime,
                        "st_mtime": stat.st_mtime,
                        "st_ctime": stat.st_ctime
                    }
    try:
        file_info['::git-head::'] = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        print("Learning Observer Startup Warning: Not in a git repo")
        print("We will not log the system state.")
        file_info['::git-head::'] = "Not a git repo"
    file_info['::pid::'] = os.getpid()
    file_info['::hostname::'] = socket.gethostname()
    file_info['::platform::'] = platform.version()
    file_info['::python::'] = platform.python_version()
    file_info['::timestamp::'] = datetime.datetime.utcnow().isoformat()
    return file_info


async def filesystem_state_handler(request):
    return aiohttp.web.json_response(filesystem_state())


if __name__ == '__main__':
    # We normally do JSON, but we'll do YAML here, just to test in a different context
    #
    # By convention:
    # * We always output JSON in logs/snapshots (which are read by machines)
    # * We always input YAML in configuration files (which are written by humans)
    import yaml
    print(yaml.dump(filesystem_state()))

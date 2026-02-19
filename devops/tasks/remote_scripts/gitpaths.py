import os.path
import os


WORKING_REPO_PATH='/home/ubuntu/'
BARE_REPO_PATH='/home/ubuntu/baregit/'


def gitpath_to_name(packagepath):
    '''
    Convert a git path to the name of the repo. For example:

    `https://github.com/ArgLab/writing_observer.git` ==> `writing_observer`
    '''
    package = os.path.split(packagepath)[1]
    if package.endswith(".git"):
        return package[:-4]
    else:
        return package


def working_repopath(repo=None):
    '''
    Switch to the path where *working* `git` repo is located. E.g. one
    with a working tree, if it exists.
    '''
    if repo is None:
        os.chdir(WORKING_REPO_PATH)
        return WORKING_REPO_PATH

    path = os.path.join(WORKING_REPO_PATH, repo)
    if os.path.exists(path):
        os.chdir(path)
        return path
    return False


def bare_repopath(repo=None):
    '''
    Switch to the path where *bare* `git` repo is located. E.g. one
    without a working tree, for pushing and pulling.
    '''
    # If we don't have a path for bare repos, create it.
    if(os.system("mkdir -p "+BARE_REPO_PATH)):
        print("Error creating or accessing bare repository directory")
        sys.exit(-1)

    if repo is None:
        os.chdir(BARE_REPO_PATH)
        return BARE_REPO_PATH

    path = os.path.join(BARE_REPO_PATH, repo)
    if os.path.exists(path):
        os.chdir(path)
        return path
    return False

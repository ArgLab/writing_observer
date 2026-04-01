'''This is a small library to allow us to browse git repos.

Next steps:

* It's a little bit over-conservative in terms of sanitizing parameters
  to git. We should be more precise so we allow more filenames and branch
  names.
* We should really browse the git repo directly, without subprocess. I
  mean, really?
* Perhaps add more git commands?
'''

import enum
import os.path
import string
import subprocess
import sys

import pathvalidate


# Special tag used to browse files in the working directory.  This is
# helpful during **DEVELOPMENT**. This may be dangerous in production,
# since working directories sometimes have random files sitting
# around. We use an enum so that users explicitly need to ask to use
# this feature.

WORKING_DIR = enum.Enum("Special Branches", "Working").Working


class FileExists(Exception):
    '''
    For now, raised when cloning a repo to a location which exists.
    '''


def sanitize(filename):
    '''
    Confirm that a filename is valid for using in a shell command to
    pull a file out of git.

    We'll be overly-conservative. We don't want security exploits. At
    some point, this should be made more narrow, but since we're calling
    into shell code in this version, we're super-careful

    '''
    valid_characters = "-_/." + string.ascii_letters + string.digits
    newname = "".join(c for c in filename if c in valid_characters)
    newname = pathvalidate.sanitize_filepath(
        newname,
        platform='Linux', normalize=True
    )
    if newname.startswith("/"):
        raise ValueError("Suspicious operation: String starts with /")
    if newname.startswith("-"):
        raise ValueError("Suspicious operation: String starts with -")
    if ".." in newname:
        raise ValueError("Suspicious operation: String contains ..")
    if newname != filename:
        raise ValueError("Suspicious operation: Sanitized string != original")
    return newname


class GitRepo:
    '''
    Class for managing a git repo. We could make this functional, but
    OO is helpful in case we ever want to e.g. use remote git repos. In
    those cases, we may want to e.g. maintain open ssh connections and
    whatnot. It can also help with caching.
    '''
    def __init__(self, gitdir, bare=False):
        '''
        We store where the repo is, and return an object we can
        use to browse it.
        '''
        self.bare = bare
        self.workingdir = None
        # We should probably store the working dir too, for
        # non-bare directories. We'll add that once we need
        # it.
        if not gitdir.endswith("/.git"):
            self.gitdir = os.path.join(gitdir, ".git")
        else:
            self.gitdir = gitdir
        self.workingdir = self.gitdir[:-4]

    def clone(self, url, mirror=False):
        '''
        Clone the repo. Hopefully raise an exception if it already exists.
        '''
        if os.path.exists(self.gitdir):
            raise FileExists()
        options = ""
        if mirror:
            options += "--mirror"
        command = "git clone {options} {url} {path}".format(
            options=options,
            url=url,
            path=self.gitdir
        )
        # TODO: Test error handling.
        # *Should* raise a subprocess.CalledProcessError on failure.
        return subprocess.check_output(command, shell=True).decode('utf-8')

    def branches(self):
        '''
        Return a list of all local branches in the repo
        '''
        command = "git --git-dir={gitdir} branch".format(
            gitdir=self.gitdir
        )
        try:
            branch_list = subprocess.check_output(
                command, shell=True
            ).decode('utf-8').split('\n')
        except subprocess.CalledProcessError:
            # This is a bit redundant, since most of this is in the exception,
            # but it's helpful for quickly fixing config issues.
            print("Failed to git branch. Command:")
            print(command)
            print("in gitaccess.py")
            raise
        branch_list = [b.replace('*', '').strip() for b in branch_list]
        branch_list = [b for b in branch_list if b != '']
        return branch_list

    def show(self, branch, filename):
        '''
        Return the contents of a file in the repo

        Note that this is not UTF8, and needs to be decoded.
        '''
        if branch != WORKING_DIR:
            sanitized_branch = sanitize(branch)
        sanitized_filename = sanitize(filename)
        if branch in self.branches():
            data = subprocess.check_output(
                "git --git-dir={gitdir} show {branch}:{filename}".format(
                    gitdir=self.gitdir,
                    branch=sanitized_branch,
                    filename=sanitized_filename
                ), shell=True
            )
        elif branch == WORKING_DIR:
            data = open(
                os.path.join(self.workingdir, sanitized_filename),
                "rb"
            ).read()
        else:
            raise ValueError("No such branch")
        return data

    def rev_hash(self, branch):
        '''
        Return the git hash of a branch.
        '''
        if branch == WORKING_DIR:
            data = "[NO_HASH_WORKING_TREE]"
        else:
            sanitized_branch = sanitize(branch)
            data = subprocess.check_output(
                "git --git-dir={gitdir} rev-parse {branch}".format(
                    gitdir=self.gitdir,
                    branch=sanitized_branch
                ),
                shell=True
            ).decode('utf-8').strip()
            if not all(c in string.hexdigits for c in data):
                raise ValueError("Not a valid branch / hash")

        return data.strip()


# Simple test case. Show README.md from a repo specified on the command line.
if __name__ == "__main__":
    repo = GitRepo(sys.argv[1])
    branches = repo.branches()
    print(branches)
    print(repo.show(branches[-1], 'README.md'))
    print(repo.show(WORKING_DIR, 'README.md'))
    print(repo.rev_hash(branches[-1]))

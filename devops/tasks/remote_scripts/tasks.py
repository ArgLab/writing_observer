'''
This is a remote script for random `git` operations (e.g. running
on machines in the Learning Observer flock).

This is a bit awkward, but we maintain:

- Public `git` repositories in `/home/ubuntu/`
- Private `git` repositories in `/home/ubuntu/baregit` cloned into
  `/home/ubuntu`

The reason for this design is:

- Pushing a nonpublic repo to a remote server is a bit awkward. Versions
  of `git` in current distros do *not* support `push`ing into a non-bare
  repo (although this functionaly was added to bleeding edge git). If 
  we're pushing, we want to push into a bare repo
- For use (e.g. for 

We would like to do this (relatively) statelessly, so that if a repo
exists, we can do an update. If it's up-to-date, we can do nothing. If
it's not there, we create it.

As of this writing, this is not fully tested. We're going to test more
fully by finishing the side from where we're orchestrating.

Note that these scripts are designed to be as flexible as possible in terms
of how a path is specified. E.g.: 

  inv init https://gitserver.example.com/a/foo.git
  inv init /temp/foo
  inv init foo

Will all do the same thing. They will go into the bare repo path, and crete
an empty repository called `foo` if one doesn't already exist, ready for
pushing.

In the future, we should have a desired version and perhaps give warnings if
the wrong one is used.
'''

import os
import os.path

import sys

from invoke import task


# We would like to use these on the remote machine, but also on the local
# machine.
try:
    from gitpaths import bare_repopath, working_repopath, gitpath_to_name
except:
    from orchlib.gitpaths import bare_repopath, working_repopath, gitpath_to_name


@task
def branch(c, repo, branch):
    '''
    Switch to a branch in a repo.
    '''
    repo = gitpath_to_name(repo)
    print("Going to to: ", working_repopath(repo))
    command = "git checkout "+branch
    print(command)
    os.system(command)


@task
def init(c, repo):
    '''
    Create a new bare repo, if one does not exist already.

    Otherwise, continue on silently.

    This is for force pushes of remote repos.
    '''
    repo = gitpath_to_name(repo)
    path = bare_repopath(repo)
    if not path:
        bare_repopath()
        command = "git --bare init "+repo
        print(command)
        os.system(command)
    print(bare_repopath(repo))


@task
def cloneupdate(c, fullrepo):
    '''
    Clone a remote repo.
    '''
    repo = gitpath_to_name(fullrepo)
    barepath = bare_repopath(repo)

    working_repopath()
    if not working_repopath(repo):
        print("Cloning...")
        command = "git clone "+fullrepo
        print(command)
        os.system(command)
        working_repopath(repo)

    print("Updating all branches")
    os.system("git fetch --all")
    os.system("git pull")

@task
def cloneupdatelocal(c, repo):
    repo = gitpath_to_name(repo)
    cloneupdate(c, bare_repopath(repo))


@task
def pull(c, repo):
    '''
    Update a repo to the latest version.
    '''
    path = working_repopath(repo)
    command = "git pull --all"
    print(command)
    os.system(command)
    return path

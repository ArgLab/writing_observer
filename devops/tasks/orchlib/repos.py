import os

import orchlib.config

import remote_scripts.gitpaths


# Working command: GIT_SSH_COMMAND="ssh -i KEY.pem" git --git-dir=/tmp/foo/.git push -f --mirror ssh://ubuntu@SOME_SERVER/home/ubuntu/baregit/foo


# This command will forcefully push a local repo to a remote server, including all branches
GIT_PUSH ='''
GIT_SSH_COMMAND="ssh -i {key} -o 'StrictHostKeyChecking no'" git
    --git-dir={localrepo}/.git
    push -f
    --mirror
    ssh://ubuntu@{mn}.{domain}/home/ubuntu/baregit/{reponame}
'''.strip().replace('\n', '')


def force_push(machine, localrepo):
    print("LOCAL REPO: ", localrepo)
    command = GIT_PUSH.format(
        mn=machine,
        domain=orchlib.config.creds['domain'],
        key=orchlib.config.creds['key_filename'],
        localrepo=localrepo,
        reponame=remote_scripts.gitpaths.gitpath_to_name(localrepo)
    )
    print(command)
    os.system(command)


def remote_invoke(group, command):
    remote_command = "cd writing_observer/devops/tasks/remote_scripts; inv {command}".format(command=command)
    print(remote_command)
    group.run(remote_command)


def update(group, machine_name):
    # In most cases, these would correspond to static sites, or
    # Learning Observer modules
    print("Grabbing public git packages")
    for package in orchlib.config.config_lines(machine_name, "gitclone"):
        remote_invoke(group, "cloneupdate {package}".format(package=package))
    print("Pushing private git packages")

    # We can only push to bare repos. 
    for package in orchlib.config.config_lines(machine_name, "gitpush"):
        print("Configuring: ", package)
        remote_invoke(group, "init {package}".format(package=package))
        print("Force pushing: ", package)
        force_push(machine_name, package)
        remote_invoke(group, "cloneupdatelocal {package}".format(package=package))

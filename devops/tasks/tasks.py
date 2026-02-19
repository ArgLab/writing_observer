import atexit
import csv
import datetime
import itertools
import os
import shlex
import sys

from invoke import task

import fabric.exceptions

import orchlib.aws
import orchlib.config
import orchlib.fabric_flock
import orchlib.templates
import orchlib.ubuntu
import orchlib.repos
from orchlib.logger import system

import remote_scripts.gitpaths


@task
def list(c):
    '''
    Give a human-friendly listing of all provisioned machines
    '''
    for instance in orchlib.aws.list_instances():
        print("{:21} {:21} {:16} {}".format(
            instance['InstanceId'],
            instance['Tags']['Name'],
            instance['PublicIpAddress'],
            instance['Tags'].get("use", "")
        ))


@task
def provision(c, machine_name):
    '''
    Set up a baseline image with all the packages needed for
    Learning Observer. Note that this will **not** configure
    the machine.
    '''
    print("Provisioning...")
    machine_info = orchlib.aws.create_instance(machine_name)
    print("Updating...")
    ip = machine_info.public_ip_address
    print("DNS....")
    orchlib.aws.register_dns(machine_name, orchlib.config.creds['domain'], ip)
    print("IP", ip)
    orchlib.ubuntu.update(ip)
    print("Baseline...")
    orchlib.ubuntu.baseline_packages(ip)
    print("Venv...")
    orchlib.ubuntu.python_venv(ip)


@task
def update(c):
    '''
    Update all machines with the latest systems updates and security
    patches
    '''
    addresses = [i['PublicIpAddress'] for i in orchlib.aws.list_instances()]
    # Machines without IPs don't get updates
    addresses = [i for i in addresses if i != "--.--.--.--"]
    print(addresses)
    orchlib.ubuntu.run_script("update")(*addresses)


@task
def create(c, machine_name):
    '''
    Create a machine end-to-end. This is a shortcut for:
    * Provision
    * Configure
    * Certbot
    * Download
    * Reboot
    '''
    print("Provisioning EC2 instance")
    provision(c, machine_name)
    print("Configuring the Learning Observer")
    configure(c, machine_name)
    print("Setting up SSL")
    certbot(c, machine_name)
    print("Saving config")
    downloadconfig(c, machine_name)
    print("Rebooting")
    reboot(c, machine_name)


@task
def terminate(c, machine_name):
    '''
    Shut down a machine.
    '''
    a = input("Are you sure? ")
    if a.strip().lower() not in ['y', 'yes']:
        sys.exit(-1)
    orchlib.aws.terminate_instances(machine_name)


@task
def connect(c, machine_name):
    '''
    `ssh` to a machine
    '''
    command = "ssh -i {key} ubuntu@{machine_name}".format(
        key=orchlib.config.creds['key_filename'],
        machine_name = machine_name+"."+orchlib.config.creds['domain']
    )
    print(command)
    system(command)


@task
def configure(c, machine_name):
    '''
    Configure a machine
    '''
    group = orchlib.aws.name_to_group(machine_name)

    # We start be setting up `git` repos. This will fail if done later,
    # since we need these to install pip packages, etc.
    orchlib.repos.update(group, machine_name)

    # Set up Python packages. We need git repos for this, but we might
    # want to us these in scripts later.
    print("Installing Python packages")
    for package in orchlib.config.config_lines(machine_name, "pip"):
        group.run("source ~/.profile; pip install {package}".format(
            package=package
        ))

    template_config = {
        "nginx_root_options": "",
        "hostname": machine_name,
        "domain": orchlib.config.creds['domain']
    }

    print("Uploading files")
    uploads = [
        l.strip().split(',')
        for l in itertools.chain(
                orchlib.config.config_lines(machine_name, "sync.csv"),
                orchlib.config.config_lines(machine_name, "uploads.csv"),
        )
    ]
    # We should consider switching back to csvreader, so we handle commas in
    # the description
    for [local_file, owner, perms, remote_file, description] in uploads:
        print("Uploading: ", description)
        remote_path = os.path.dirname(remote_file)
        group.run("mkdir -p "+remote_path)
        orchlib.templates.upload(
            group=group,
            machine_name=machine_name,
            filename=local_file,
            remote_filename=remote_file.format(**template_config),
            config=template_config,
            username=owner,
            permissions=perms
        )

    for command in open("config/postuploads").readlines():
        group.run(command.format(**template_config).strip())
    

@task
def downloadconfig(c, machine_name):
    '''
    After setting up certbot, it's helpful to download the nginx config
    file. We also don't want to make changes remotely directly in deploy
    settings, but if we have, we want to capture those changes.
    '''
    template_config = {
        "nginx_root_options": "",
        "hostname": machine_name,
        "domain": orchlib.config.creds['domain']
    }

    group = orchlib.aws.name_to_group(machine_name)
    downloads = [
        l.strip().split(',')
        for l in itertools.chain(
                orchlib.config.config_lines(machine_name, "sync.csv"),
                orchlib.config.config_lines(machine_name, "downloads.csv"),
        )
    ]
    # We should consider switching back to csvreader, so we handle commas in
    # the description
    for [local_file, owner, perms, remote_file, description] in downloads:
        print("Downloading: ", description)
        try:
            orchlib.templates.download(
                group=group,
                machine_name=machine_name,
                filename=local_file,
                remote_filename=remote_file.format(**template_config)
            )
        except fabric.exceptions.GroupException:
            # This usually means the file is not found. In most cases,
            # this happens when we've added a new file to the config,
            # and we're grabbing from an old server.
            #
            # We should handle this more gracefully. How is TBD
            print("Could not download file!")

@task
def certbot(c, machine_name):
    '''
    This sets up SSL. Note that:
    - SSL will generally NOT work until everything else is set up
    - This change nginx config. You don't want to override config
      files later.
    - This is untested :)
    '''
    group = orchlib.aws.name_to_group(machine_name)
    CERT_CMD = "sudo certbot -n --nginx --agree-tos --redirect " \
        "--email {email} --domains {hostname}.{domain}"
    group.run(CERT_CMD.format(
        email=orchlib.config.creds['email'],
        hostname = machine_name,
        domain=orchlib.config.creds['domain']
    ))


@task
def reboot(c, machine_name):
    '''
    Untested: This doesn't seem to work yet....
    '''
    print("Trying to reboot... no promises.")
    orchlib.ubuntu.reboot(machine_name)


@task
def downloadfile(c, machine_name, remote_filename, local_filename):
    '''
    Helper to download a single file.

    This is verbose, and doesn't do wildcards. Perhaps better a helper to
    `scp`? Don't use this in scripts until we've figured this out....
    '''
    group = orchlib.aws.name_to_group(machine_name)
    group.get(
        remote_filename,
        local_filename
    )


@task
def uploadfile(c, machine_name, remote_filename, local_filename):
    '''
    Helper to upload a single file.

    This is verbose, and doesn't do wildcards. Perhaps better a helper to
    `scp`? Don't use this in scripts until we've figured this out....
    '''
    group = orchlib.aws.name_to_group(machine_name)
    group.put(
        remote_filename,
        local_filename
    )


@task
def runcommand(c, machine_name, command):
    '''
    Run a remote command. Don't forget quotes!
    '''
    group = orchlib.aws.name_to_group(machine_name)
    group.run(command)


@task
def hello(c):
    '''
    For testing!

    For example, hooks.
    '''
    print("Hello, world!")


@task
def backup(c, machine_name, target):
    '''
    Grab a backup of a given directory by name
    '''
    targets = {
        'nginx': "/var/log/nginx/",
        'certs': "/etc/letsencrypt/"
    }

    if target not in targets:
        print("Invalid target. Should be one of:")
        print("\n".join(targets))
        sys.exit(-1)

    ts = datetime.datetime.utcnow().isoformat().replace(":", "-")
    filebase = "{ts}-{mn}-{tg}".format(
        ts=ts,
        mn=machine_name,
        tg=target
    )

    command = "tar /tmp/{filebase} {target}".format(
        filebase=filebase,
        target=target
    )

    group = orchlib.aws.name_to_group(machine_name)
    group.get(
        remote_filename,
        local_filename
    )


@task
def commit(c, msg):
    '''
    This should probably not be a task but a utility function. It's
    helpful for debuggin, though.
    '''
    system(
        "cd {gitpath} ; git add -A; git commit -m {msg}".format(
            gitpath=orchlib.config.creds["flock-config"],
            msg=msg
        )
    )


START_TIME = datetime.datetime.utcnow().isoformat()

def committer():
    '''
    On exit, commit changes to repo. This code is not finished.
    '''
    command_options = shlex.quote(" ".join(sys.argv))
    stop_time = datetime.datetime.utcnow().isoformat()
    log = {
        'start_time': START_TIME,
        'stop_time': stop_time,
        'command_options': command_options
    }


atexit.register(committer)

import os
import os.path

import json
import yaml

creds_file = "settings/CREDS.YAML"

if not os.path.exists(creds_file):
    print("No credentials file. I'll need a bit of info from you")
    print("to make one.")
    info = {
        "user": "Your username on the remote machine (probably ubuntu)",
        "key_filename": "Your AWS key filename (something like /home/me/.ssh/aws.pem)",
        "aws_keyname": "Your AWS key id (as AWS knows it; e.g. aws.pem)",
        "aws_subnet_id": "AWS subnet (e.g. subnet-012345abc)",
        "aws_security_group": "AWS security group (e.g. sg-012345abc)",
        "owner": "Your name",
        "email": "Your email",
        "domain": "Domain name (e.g. learning-observer.org)",
        "flock-config": "Path to git repo where we'll store machine config.",
        "deploy-group": "Tag to identify all machines (typically, learning-observer)",
        "ec2_tags": "JSON dictionary of any additional tags you'd like on your machines. If you're not sure, type {}"
    }
    print("I'll need:")
    for key, value in info.items():
        print("* {value}".format(value=value))
    print("Let's get going")
    d = {}
    for key, value in info.items():
        print(value)
        d[key] = input("{key}: ".format(key=key)).strip()
    d['ec2_tags'] = json.loads(d['ec2_tags'])
    if not os.path.exists(d['flock-config']):
        os.system("git init {path}".format(path=d['flock-config']))
        os.mkdir(os.path.join(d['flock-config'], "config"))
    with open("settings/CREDS.YAML", "w") as fp:
        yaml.dump(d, fp)

creds = yaml.safe_load(open(creds_file))

def config_filename(machine_name, file_suffix, create=False):
    '''
    Search for the name of a config file, checking
    * Per-machine config
    * System-wide defaults
    * Defaults for this for the Learning Observer (defined in this repo)

    Absolute paths (e.g. beginning with '/') are returned as-is.
    '''
    if file_suffix.startswith("/"):
        return file_suffix

    paths = [
        # First, we try per-machine configuration
        os.path.join(
            creds["flock-config"], "config", machine_name, file_suffix
        ),
        # Next, we try the per-machine override
        os.path.join(
            creds["flock-config"], "config", machine_name, file_suffix+".base"
        ),
        # Then, system-wide configuration
        os.path.join(
            creds["flock-config"], "config", file_suffix
        ),
        # And finally, as a fallback, default files
        os.path.join(
            "config", file_suffix
        )
    ]

    # For making new versions, always return the per-machine git repo
    # directory
    if create == True:
        return paths[0]

    for fn in paths:
        print(fn)
        if os.path.exists(fn):
            return fn


def config_lines(machine_name, file_suffix):
    '''
    Kind of like a smart `open().readlines()` for reading config files.

    Handle paths, prefixes, missing files (return nothing),
    `strip()`ing lines, comments, etc.
    '''
    fn = config_filename(machine_name, file_suffix)
    # No config file
    if fn is None:
        print("Skipping; no file for: ", file_suffix)
        return
    print("Config file: ", fn)
    for line in open(fn).readlines():
        line = line.strip()
        if len(line) > 0:
            yield line

'''
These are scripts for preparing an Ubuntu 20.04 machine to run the
Learning Observer
'''

import fabric.exceptions

import orchlib.fabric_flock
import orchlib.config


def run_script(scriptfile):
    '''
    Helper which executes a series of commands on set of machines
    '''
    script = open("scripts/{fn}.fab".format(fn=scriptfile)).read()
    def run(*machines):
        group = orchlib.fabric_flock.machine_group(*machines)

        for line in ['hostname'] + script.split("\n"):
            line = line.strip()
            if len(line) > 0 and line[0] != "#":
                print(line)
                group.run(line)
    return run

update = run_script("update")
baseline_packages = run_script("baseline_packages")
python_venv = run_script("python_venv")


def reboot(machine):
    '''
    Run the reboot script. We expect an exception since the remote machine
    reboots while Fabric is connected.
    '''
    try:
        print("Trying to reboot (this doesn't always work")
        run_script("reboot")(machine)
    except fabric.exceptions.GroupException:
        pass

def provision(ip):
    group = fabric.SerialGroup(
        ip,
        user=orchlib.config.creds['user'],
        connect_kwargs={"key_filename": orchlib.config.creds['key_filename']}
    )
    update()
    baseline_packages()
    python_venv()
    reboot()

if __name__=='__main__':
    provision()

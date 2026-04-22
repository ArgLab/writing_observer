'''
These are baseline script to help orchestrate a flock of machines
via ssh. This is a thin wrapper around `fabric`.
'''

import yaml
import fabric

import orchlib.config
import orchlib.logger

def machine_group(*pool):
    # Skip terminated machines.
    # Sadly, also skips recently-created machines....
    pool = [ip for ip in pool if ip!="--.--.--.--"]
    group = fabric.SerialGroup(
        *pool,
        user=orchlib.config.creds['user'],
        connect_kwargs={"key_filename": orchlib.config.creds['key_filename']}
    )

    class GroupWrapper:
        '''
        This is a thin wrapper, designed for logging commands, and in the
        future, perhaps return values.
        '''
        def __init__(self, group):
            self._group = group

        def run(self, command):
            command = "source ~/.profile; " + command
            orchlib.logger.grouplog(
                "run",
                [command],
                {}
            )

            self._group.run(command)

        def get(self, *args, **kwargs):
            orchlib.logger.grouplog(
                "get",
                args,
                kwargs
            )
            self._group.get(*args, **kwargs)

        def put(self, *args, **kwargs):
            orchlib.logger.grouplog(
                "put",
                args,
                kwargs
            )
            self._group.put(*args, **kwargs)

        def sudo(self, *args, **kwargs):
            orchlib.logger.grouplog(
                "sudo",
                args,
                kwargs
            )
            self._group.sudo(*args, **kwargs)

    wrapper = GroupWrapper(group)

    return wrapper


def connection_group(pool = None):
    '''
    Return a Fabric connection group
    '''
    if pool is None:
        pool = machine_pool()

    return fabric.SerialGroup(
        pool,
        user=orchlib.config.creds['user'],
        connect_kwargs={"key_filename": orchlib.config.creds['key_filename']}
    )


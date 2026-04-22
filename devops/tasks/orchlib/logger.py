'''
We'd like to log which actions we take.

This isn't done, but it's a start
'''

import os

log = [
]

def system(command):
    '''
    Run a command on the local system (`os.system`)

    Log the command and return code.
    '''
    rc = os.system(command)
    log.append({
        'event': 'system',
        'command': command,
        'return_code': rc
    })
    return rc

def grouplog(command, args, kwargs):
    log.append({
        'event': 'group',
        'command': command,
        'args': args,
        'kwargs': kwargs
    })


def exitlog():
    '''
    Not done.
    '''
    os.path.join(
        orchlib.config.creds["flock-config"], "logs"
    )

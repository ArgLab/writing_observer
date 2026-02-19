'''
These aren't used much yet, but these are the sorts of exceptions
our system raises, beyond the basic Python ones.
'''


class DeployException(Exception):
    '''
    E.g. Bad config file. Missing paths. Etc.

    Errors at startup should **not** raise this exception, but print a
    meaningful error message. This exception should only be raised at
    run-time.
    '''


class SuspiciousOperation(Exception):
    '''
    E.g.:
    * A user types in a URL by hand with "/../"
    * Someone hand-crafts an invalid AJAX request
    * etc.

    These happen when a platform is running, but they are suspicious.
    '''

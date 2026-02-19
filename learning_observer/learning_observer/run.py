'''
Run.py: Helper for console_scripts entry point
=====

In order to have this work as a command line utility installed with
pip, we need a way to run this which is a function, rather than a
script.
'''
import sys
import os.path


def run():
    '''
    Helper to run from entry point
    '''
    print("Running")
    print(os.path.dirname(__file__))
    sys.path.append(os.path.dirname(__file__))
    print(sys.path)

    # We might refactor this at some point, but our goal
    # is to emulate running `python learning_observer.main`
    # since console script entry points need to call a
    # function rather than run a script.

    # pylint: disable=C0415,W0611
    import learning_observer.main
    print("Imported")

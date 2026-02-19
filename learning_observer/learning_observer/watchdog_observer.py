'''
This is a subsystem designed to restart the system if files changed.

It has two modes:

    - reimport: It will reimport all modules in the local directory.
    - restart: It will hard restart the system

It currently does not work. We need to make this work with asyncio:

https://gist.github.com/mivade/f4cb26c282d421a62e8b9a341c7c65f6

However, we wanted to commit it since it doesn't break anything, and
we wanted everything to be is in sync. It is behind a feature flag,
and disabled by
'''

import asyncio
import importlib
import os
import os.path
import sys
import time
import logging
import traceback
import watchdog

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, LoggingEventHandler

# TODO fix this
LOCAL_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def reimport_child_modules(paths=[LOCAL_PATH]):
    '''
    Reload all modules which are in the given paths.

    This is used when we are running in watchdog mode, and we want to
    restart parts of the server when a file changes.

    This does not do a full restart. See:
    https://docs.python.org/3/library/importlib.html#importlib.reload

    We should probably be doing a full restart, but we wrote this before
    we had a full restart option. Perhaps we should remove this? We'll
    decide once we see how useful both options are.

    Args:
        paths: A list of paths to search for modules.

    Returns:
        A list of modules that were reloaded, a list of modules that
        failed to reload, and a list of modules that we skipped (e.g.
        system modules).

    If no path is specified, it defaults to the base directory of this file.
    '''
    modules = list(sys.modules.values())
    reloaded = []
    failed = []

    for module in modules:
        # Only reload modules that are in the specified paths,
        # and only if they are not system modules.
        #
        # A lot of these checks are probably redundant, but
        # better safe than sorry. There is no ideal way to
        # determine if a module should be reloaded, so this
        # is a bit heuristic.
        if not hasattr(module, '__file__'):
            continue
        if module.__file__ is None:
            continue
        if not module.__file__.endswith('.py'):
            continue
        if not any(module.__file__.startswith(path) for path in paths):
            continue
        if module.__name__.startswith('_'):
            continue
        if module.__name__ in sys.builtin_module_names:
            continue
        if not os.path.exists(module.__file__):
            continue
        if "SourceFileLoader" not in str(module.__loader__):
            continue
        try:
            importlib.reload(module)
            print('reloaded %s' % module.__name__)
            reloaded.append(module)
        except Exception:
            print("Failed to reload %s" % module.__name__)
            traceback.print_exc()
            failed.append(module)
    skipped = [m for m in modules if m not in reloaded and m not in failed]
    return {
        "reloaded": reloaded,
        "failed": failed,
        "skipped": skipped
    }


def restart():
    '''
    Restart the system.
    '''
    os.execl(sys.executable, sys.executable, *sys.argv)


FILETYPES_TO_WATCH = ['yaml', 'py', 'js']


class RestartHandler(FileSystemEventHandler):
    '''
    Soft restart the server when a file changes.

    We could even just re-import the one file instead of everything?
    '''
    def __init__(self, shutdown, restart, start):
        self.shutdown = shutdown
        self.restart = restart
        self.start = start

    def on_any_event(self, event):
        '''
        On any change in the file system, restart the server.

        We should be more selective, looking only at Python files, config file,
        and skipping cache files, but for now we'll restart on any change,
        since this is helpful for testing this module.
        '''
        if (event.is_directory or
            event.src_path.split('.')[-1] not in FILETYPES_TO_WATCH or
            event.event_type != 'modified'):
            return None
        print("Reloading server", event)
        asyncio.run(self.handle_restart())

    async def handle_restart(self):
        await self.shutdown()
        await self.restart()


def watchdog(handler=LoggingEventHandler()):
    '''
    Set up watchdog mode. This will (eventually) reimport on file changes.
    '''
    event_handler = handler
    observer = Observer()
    print("Watching for changes in:", LOCAL_PATH)
    observer.schedule(event_handler, LOCAL_PATH, recursive=True)
    observer.start()
    return observer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    observer = watchdog()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()

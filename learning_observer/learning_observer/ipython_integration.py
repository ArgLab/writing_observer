'''
This file defines helpers for connecting to the server
via an ipython kernel.

Use `start()` to launch a new kernel instance.
'''
from aiohttp import web
import asyncio
import dash
import IPython
import ipykernel.kernelapp
import ipykernel.ipkernel
import json
import logging
import os
import sys
import threading
from traitlets.config import Config
import zmq

KERNEL_ID = 'learning_observer_kernel'

# generic log file for seeing ipython output
# TODO this is creating a massive file and we ought to make sure its not causing issue
# on any other systems.
# logging.basicConfig(filename='ZMQ.log', encoding='utf-8', level=logging.DEBUG)


async def start_learning_observer_application_server(runner):
    '''
    This will start the Learning Observer application on port
    9999 (Jupyter defaults to 8888).

    We use a runner since IPython expects to control the event loop,
    so we plug into that one instead of our own.
    '''
    await runner.setup()
    # TODO set this to the correct port
    site = web.TCPSite(runner, 'localhost', 9999)
    await site.start()


def record_iopub_port(connection_file_path):
    '''
    The iopub port is one of the five IPython kernel ZeroMQ
    port. This one has all the inputs and outputs from the server.

    We will subscribe here, and listen on the the conversation between
    the IPython kernel and the Jupyter client (e.g. notebook).
    '''
    # Read the connection file to get the iopub_port
    connection_info = json.load(open(connection_file_path))
    return connection_info['iopub_port']


def start(kernel_only=False, connection_file=None, iopub_port=None, run_lo_app=False, lo_app=None):
    '''Kernels can start in several ways:

    1. A user starts up a kernel by running learning observer with `--ipython-kernel` OR
    2. A user starts up an interactive shell by running learning observer with `--ipython-console` OR
    3. A Jupyter client (lab/notebook) starts a kernel

    All 3 are methods are supported; however, we have not figured out
    how to handle logging interactions with #2.

    #2 should be used for debugging purposes. In the future, we want
    to log interactions here for open science purposes.

    When the Jupyter client starts, it passes in a connection file to
    tell the system how to connect. We pass the connection file through
    the `--ipython-kernel-connection-file` parameter. We inspect this
    file to get the `iopub_port`, and subscribe to ZMQ to be able to
    eavesdrop on the conversation. We log messages published on this port.

    Roadblocks:
    - To initiate the kernel properly, you must be run `jupyter` from
      the `/learning_observer` directory.  The same location that we
      normally start the server with `python learning_observer`. The
     `passwd.lo` file is read in based on your current working
      directory.  Other files may also be read in this way. We just
      haven't found and fixed them all yet.
    '''

    class LOKernel(ipykernel.ipkernel.IPythonKernel):
        '''Intercept the kernel to fix any issues with
        in the startup configuration and to start the
        learning observer platform alongside.

        We nest this kernel class so we can start and stop the Learning
        Observer application. The kernel classes are passed into an IPython
        kernel launcher via the `kernel_class` parameter. This prevents
        us from passing arguments, such as the Learning Observer application,
        directly to the kernel.
        '''
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # When dash first loads, it initializes `jupyter_dash`. However,
            # at that point, we have not loaded the IPython module yet. This
            # re-initalizes it now that the IPython module is loaded.
            dash.jupyter_dash.__init__()
            if run_lo_app:
                self.lo_runner = web.AppRunner(lo_app)

        def start(self):
            super().start()
            if run_lo_app:
                asyncio.run_coroutine_threadsafe(start_learning_observer_application_server(self.lo_runner), self.io_loop.asyncio_loop)

        def do_shutdown(self, restart):
            if run_lo_app:
                asyncio.run_coroutine_threadsafe(self.lo_runner.cleanup(), self.io_loop.asyncio_loop)
            return super().do_shutdown(restart)

        def do_execute(self, code, silent,
                       store_history=True, user_expressions=None, allow_stdin=False, *, cell_id=None):
            '''This method handles execution of code cells.
            If there is code to be run with all cells, it should be placed here.
            '''
            return super().do_execute(code, silent, store_history, user_expressions, allow_stdin,
                                      cell_id=cell_id)

    # Start the listener in a separate thread
    # HACK fix this - should this just be a setting?
    iopub = 12345 if iopub_port is None else iopub_port
    if connection_file:
        iopub = record_iopub_port(connection_file)
    keep_monitoring_iopub = True
    thread = threading.Thread(target=monitor_iopub, args=(iopub, lambda: keep_monitoring_iopub))
    thread.start()

    # TODO:
    # I would prefer to be able to select which things are launched as flags rather
    # than exclusive.
    #
    # e.g. --server_running=false --kernel --loconsole --notebook
    #
    # Would run the kernel, a console, and a notebook, but no application server
    #
    # As the number of services grows, this is more maintainable, I think.
    #
    # With pmss, we might also define classes for reasonable defaults.

    # The IPython kernels automatically read in sys.argv. To avoid any conflicts
    # with the kernel, we backup the sys.argv and reset them.
    sys_argv_backup = sys.argv
    sys.argv = sys.argv[:1]
    if kernel_only and connection_file:
        sys.argv.extend(['-f', connection_file])
        print('launching app')
        ipykernel.kernelapp.launch_new_instance(kernel_class=LOKernel)
    elif kernel_only:
        c = Config()
        c.IPKernelApp.iopub_port = iopub
        IPython.embed_kernel(config=c, kernel_class=LOKernel)
    else:
        # TODO figure out how to log when using `.embed()`. The `embed`
        # funciton uses a different structure compared to serving an
        # entire kernel. We are unable to monitor the iopub port, because
        # it doesn't exist in this context.
        IPython.embed()
    keep_monitoring_iopub = False


def load_kernel_spec():
    '''Load the `learning_observer_kernel`. This will create the
    kernel is one does not already exist.

    TODO copy in logo files
    '''
    current_script_path = os.path.abspath(__file__)  # At some point, perhaps move into / use paths.py?
    current_directory = os.path.dirname(current_script_path)
    kernel_spec = {
        'argv': [sys.executable, current_directory, '--ipython-kernel', '--ipython-kernel-connection-file', '{connection_file}'],
        'display_name': 'Learning Observer Kernel',
        'language': 'python',
        'name': KERNEL_ID
    }

    dirname = os.path.join(sys.prefix, 'share', 'jupyter', 'kernels', KERNEL_ID)
    kernel_file = os.path.join(dirname, 'kernel.json')
    # check if we should even make it
    if os.path.isfile(kernel_file):
        print('Kernel found!\nUsing the following kernel spec:')
        print(json.dumps(json.load(open(kernel_file)), indent=2))
        return
    print('Kernel NOT found!\nCreating a default kernel spec:')
    print(json.dumps(kernel_spec, indent=2))
    os.mkdir(dirname)
    json.dump(kernel_spec, open(kernel_file, 'w'), sort_keys=True)
    # We can also store logos in the same directory
    # under `logo-64x64.png` or `logo-32x32.png`


def monitor_iopub(port, stop=None):
    '''
    Setup listener for the IO Pub ZMQ socket to listen for and log
    messages about which code to run and results.

    Incoming messages are a list with the following items:

    ```python
    inc_msg = [
        b'kernel.<id>.<msg_type>',  # ZMQ routing prefix
        b'<IDS|MSG>',               # Delimeter key (always the same)
        b'some-cryptographic-str',  # HMAC string for authentication
        b'{"msg_id": "", ...}'      # message contents
    ]
    ```

    Jupyter recommends using `jupyter_client.session.Session` for
    consuming messages sent back and forth. However, passing in a
    session object only works when in a Jupyter notebook or lab.
    This does not work when serving the kernel and connecting via
    `jupyter console --existing kernel-<kernel_id>.json`
    '''
    stop = stop if stop else lambda: False
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f'tcp://localhost:{port}')
    topic_filter = b''
    subscriber.setsockopt(zmq.SUBSCRIBE, topic_filter)

    # message types we want to record
    logged_msg_types = ['execute_input', 'execute_result']
    try:
        while not stop():
            message = subscriber.recv_multipart()
            # TODO only log the types of messages we want to see
            # there are 2 different ways to fetch the message type
            # msg_type = message[0].decode().split('.')[-1]
            # msg_type = json.loads(message[3].decode())
            # if msg_type.get('msg_type', None) in logged_msg_types:
            logging.debug(f"Received message: {message}")
            # TODO: Figure out where to log, what to log, etc.
    except zmq.ZMQError as e:
        logging.debug(f"Subscriber terminated due to error: {e}")
    finally:
        subscriber.close()
        context.term()

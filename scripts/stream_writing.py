'''
Stream fake writing data

Usage:
    stream_writing.py [--url=url] [--streams=n]
                      [--ici=sec,s,s]
                      [--users=user_id,uid,uid]
                      [--source=filename,fn,fn]
                      [--gdids=googledoc_id,gdi,gdi]
                      [--text-length=5]
                      [--fake-name]
                      [--gpt3=type]

Options:
    --url=url                URL to connect [default: http://localhost:8888/wsapi/in/]
    --streams=N              How many students typing in parallel? [default: 1]
    --users=user_id,uid,uid  Supply the user ID
    --ici=secs,secs          Mean intercharacter interval [default: 0.1]
    --gdids=gdi,gdi,gdi      Google document IDs of spoofed documents
    --source=filename        Stream text instead of lorem ipsum
    --text-length=n          Number of paragraphs of lorem ipsum [default: 5]
    --fake-name              Use fake names (instead of test-user)
    --gpt3=type              Use GPT-3 generated data ('story' or 'argument')

Overview:
    Stream fake keystroke data to a server, emulating Google Docs
    extension log events.
'''

import aiohttp
import asyncio
import docopt
import json
import loremipsum
import names
import random
import sys
import time


ARGS = docopt.docopt(__doc__)
print(ARGS)

STREAMS = int(ARGS["--streams"])


def increment_port(url):
    '''
    http://localhost:8888/wsapi/in/ ==> http://localhost:8889/wsapi/in/

    Not very general; hackish.
    '''
    # Split the URL into the protocol, domain, and port
    protocol, blank, domain, *rest = url.split("/")

    # Split the domain into its parts
    parts = domain.split(":")

    # Get the current port
    current_port = int(parts[-1])

    # Increment the port by 1
    new_port = current_port + 1

    # Build the new URL
    new_url = f"{protocol}//{':'.join(parts[:-1])}:{new_port}/{'/'.join(rest)}"

    return new_url


def argument_list(argument, default):
    '''
    Parse a list argument, with defaults. Allow one global setting, or per-stream
    settings. IF `STREAMS` is 3:

    None       ==> default()
    "file.txt" ==> ["file.txt", "file.txt", "file.txt"]
    "a,b,c"    ==> ["a", "b", "c"]
    "a,b"      ==> exit
    '''
    list_string = ARGS[argument]
    if list_string is None:
        list_string = default
    if callable(list_string):
        list_string = list_string()
    if list_string is None:
        return list_string
    if "," in list_string:
        list_string = list_string.split(",")
    if isinstance(list_string, str):
        list_string = [list_string] * STREAMS
    if len(list_string) != STREAMS:
        print(f"Failure: {list_string}\nfrom {argument} should make {STREAMS} items")
        sys.exit(-1)
    return list_string

# TODO what is `source_files` supposed to be?
# when running this script for the workshop, we should either
#  1) move gpt3 texts out of writing observer (dependency hell) OR
#  2) avoid using `--gpt3` parameter and use loremipsum instead
source_files = None

if ARGS["--gpt3"] is not None:
    import writing_observer.sample_essays
    TEXT = writing_observer.sample_essays.GPT3_TEXTS[ARGS["--gpt3"]]
    STREAMS = len(TEXT)
elif source_files is None:
    TEXT = ["\n".join(loremipsum.get_paragraphs(int(ARGS.get("--text-length", 5)))) for i in range(STREAMS)]
else:
    TEXT = [open(filename).read() for filename in source_files]

ICI = argument_list(
    '--ici',
    "0.1"
)

DOC_IDS = argument_list(
    "--gdids",
    lambda: [f"fake-google-doc-id-{i}" for i in range(STREAMS)]
)

source_files = argument_list(
    '--source',
    None
)

if ARGS['--users'] is not None:
    USERS = argument_list('--users', None)
elif ARGS['--fake-name']:
    USERS = [names.get_first_name() for i in range(STREAMS)]
else:
    USERS = ["test-user-{n}".format(n=i) for i in range(STREAMS)]

assert len(TEXT) == STREAMS, "len(filenames) != STREAMS."
assert len(ICI) == STREAMS, "len(ICIs) != STREAMS."
assert len(USERS) == STREAMS, "len(users) != STREAMS."
assert len(DOC_IDS) == STREAMS, "len(document IDs) != STREAMS."

def current_millis():
    return round(time.time() * 1000)


def insert(index, text, doc_id):
    '''
    Generate a minimal 'insert' event, of the type our Google Docs extension
    might send, but with irrelevant stuff stripped away. This is just for
    testing.
    '''
    return {
        "bundles": [{'commands': [{"ibi": index, "s": text, "ty": "is"}]}],
        "event": "google_docs_save",
        "source": "org.mitros.writing_analytics",
        "doc_id": doc_id,
        "origin": "stream_test_script",
        "timestamp": current_millis()
    }


def identify(user):
    '''
    Send a token identifying user.

    TBD: How we want to manage this. We're still figuring out auth/auth.
    This might just be scaffolding code for now, or we might do something
    along these lines.
    '''
    return [
        {
            "event": "test_framework_fake_identity",
            "source": "org.mitros.writing_analytics",
            "user_id": user,
            "origin": "stream_test_script"
        }, {
            "event": "metadata_finished",
            "source": "org.mitros.writing_analytics",
            "origin": "stream_test_script"
        }
    ]


async def stream_document(text, ici, user, doc_id):
    '''
    Send a document to the server.
    '''
    retries_remaining = 5
    done = False
    url = ARGS["--url"]
    while not done:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as web_socket:
                    commands = identify(user)
                    for command in commands:
                        await web_socket.send_str(json.dumps(command))
                    for char, index in zip(text, range(len(text))):
                        command = insert(index + 1, char, doc_id)
                        await web_socket.send_str(json.dumps(command))
                        # We probably want something that doesn't go as big and which isn't as close to zero as often. Perhaps weibull with k=1.5?
                        await asyncio.sleep(random.expovariate(lambd=1/float(ici)))
            done = True
        except aiohttp.client_exceptions.ClientConnectorError:
            print("Failed to connect on " + url)
            retries_remaining = retries_remaining - 1
            if retries_remaining == 0:
                print("Failed to connect. Tried ports up to "+url)
                done = True
            url = increment_port(url)
            print("Trying to connect on " + url)


async def run():
    '''
    Create a task to send the document to the server, and wait
    on it to finish. In the future, we'll create several tasks.
    '''
    streamers = [
        asyncio.create_task(stream_document(text, ici, user, doc_id))
        for (text, ici, user, doc_id) in zip(TEXT, ICI, USERS, DOC_IDS)
    ]
    print(streamers)
    for streamer in streamers:
        await streamer
    print(streamers)

try:
    asyncio.run(run())
except aiohttp.client_exceptions.ServerDisconnectedError:
    print("Could not connect to server")
    sys.exit(-1)

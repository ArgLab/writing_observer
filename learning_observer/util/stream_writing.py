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

import asyncio
import json
import sys

import aiohttp
import docopt

import loremipsum
import names

ARGS = docopt.docopt(__doc__)
print(ARGS)

STREAMS = int(ARGS["--streams"])


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
        print(
            f"Failure: {list_string}\nfrom {argument} should make {STREAMS} items")
        sys.exit(-1)
    return list_string


source_files = argument_list(
    '--source',
    None
)

if ARGS["--gpt3"] is not None:
    import writing_observer.sample_essays
    TEXT = writing_observer.sample_essays.GPT3_TEXTS[ARGS["--gpt3"]]
    text = TEXT[0]
    TEXT = [text for _ in range(STREAMS)]
    # STREAMS = len(TEXT)
elif source_files is None:
    TEXT = ["\n".join(loremipsum.get_paragraphs(
        int(ARGS.get("--text-length", 5)))) for i in range(STREAMS)]
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
        "origin": "stream_test_script"
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
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ARGS["--url"]) as web_socket:
            commands = identify(user)
            for command in commands:
                try:
                    await web_socket.send_str(json.dumps(command))
                except ConnectionResetError as e:
                    print("CONNECTION RESET:", command, e)
            for char, index in zip(text, range(len(text))):
                command = insert(index + 1, char, doc_id)
                try:
                    await web_socket.send_str(json.dumps(command))
                except ConnectionResetError as e:
                    print("CONNECTION RESET:", command, e)
                await asyncio.sleep(float(ici))


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

try:
    asyncio.run(run())
except aiohttp.client_exceptions.ServerDisconnectedError:
    print("Could not connect to server")
    sys.exit(-1)

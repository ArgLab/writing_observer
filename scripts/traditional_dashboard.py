'''
This is a test script for a web socket interaction with the
original dashboard.

We do need a better command line interface, but this is okay for
debugging for now.
'''

import argparse

import aiohttp
import asyncio

parser = argparse.ArgumentParser(
    description=__doc__.strip()
)
parser.add_argument(
    '--single', action='store_true',
    help="Print just a single message, then disconnect"
)

parser.add_argument(
    '--url', default='http://localhost:8889/wsapi/dashboard?module=writing_observer&course=12345',
    help="We connect to this URL and grab data."
)


args = parser.parse_args()


async def main():
    async with aiohttp.ClientSession() as session:
        print("Connecting to", args.url)
        async with session.ws_connect(
                args.url, timeout=0.5) as ws:
            async for msg in ws:
                print(msg.type)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print("Message")
                    print(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("Error")
                    print(msg)
                    break
                if args.single:
                    return True
    return True

asyncio.run(main())

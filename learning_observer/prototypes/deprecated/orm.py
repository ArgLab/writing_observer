'''
THIS FILE IS NOT CURRENTLY USED. WE ARE PROTOTYPING.

Abstraction to access database '''
import asyncio
import functools

import json
import yaml

import asyncpg

sql_statements = yaml.safe_load(open("init.sql"))

conn = None

stored_procedures = {}


async def initialize(reset=False):
    global conn
    print("Connecting to database...")
    # Connect to the database
    conn = await asyncpg.connect()
    if reset:
        await conn.execute(sql_statements['reset'])

    # Set up tables and stored procedures, if they don't exist.
    await conn.execute(sql_statements['init'])

    # Set up stored procedures
    for stored_procedure in sql_statements['stored_procedures']:
        stored_procedures[stored_procedure] = await conn.prepare(
            sql_statements['stored_procedures'][stored_procedure]
        )
    print("Connected...")

asyncio.get_event_loop().run_until_complete(initialize())


# TODO: This should be done with a decorator, rather than cut-and-paste
def fetch_events(username, docstring):
    return stored_procedures['fetch_events'].cursor(username, docstring)


async def insert_event(username, docstring, event):
    rv = await stored_procedures['insert_event'].fetchval(
        username, docstring, event
    )
    return rv


if __name__ == '__main__':
    async def test():
        print(await insert_event("pmitros", "doc", json.dumps({
            "ty": "ts",
            "si": 5,
            "ei": 7,
            "ibi": 2,
            "s": "hel",
            "f": "lo"
        })))
        async with conn.transaction():
            cursor = fetch_events("pmitros", "doc")
            async for record in cursor:
                print(record)

    asyncio.get_event_loop().run_until_complete(test())

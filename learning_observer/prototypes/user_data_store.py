'''
Abstraction to access database

We need to store a few types of data:

1) An archival store of process data usable for:
   - Posthoc analysis
   - Error recovery
   - Debugging
We expect to potentially receive multiple events per
second per student, so this needs to be able to handle
moderately high volume, high-velocity data. The JSON
format has a lot of redundancy, be design, and compresses
well.

2) Working memory:
   - Storing state as we stream process events
   - This does not have to be reliable IF we have clean
     mechanisms for recovering from the archival store
   - We may have the same user connected to multiple machines
     (e.g. when editing the same document on two computers),
     so we probably cannot rely on async+in-memory. But we can
     rely on high-speed in-memory like redis or memcached.
   - We likely do need at least snapshots of some kind in
     non-volatile memory, so we don't have to replay everythin
     when we restart.

There are open questions as to what granularity state should live
at (e.g. per-student, per-teacher, pre-resource, etc.), and
appropriate abstractions.

3) Typical operational information:

- Users table, with logins
- Probably some list of documents we're operating on
- Some way to map students to classes, so we know who ought to
  receive data for which student.

This naturally fits into a traditional SQL database, like postgresql
or sqlite.

By design, we want to support at least two modes of operation:

1) Small-scale (e.g. development / debugging), with no external
   dependencies. Working on this project should not require spinning
   up an army of cloud machines, servers, and microservices. Here, we
   can e.g. store "large" process data in sqlite, or query static files
   on disk.

2) Scalable (e.g. deployment), where we can swap out local stores for
   larger-scale stores requiring either serious dev-ops or serious
   cloud $$$.

We'd like to be able to go between the two smoothly (e.g. run all but one
service locally).

Python asynchronous database support is limited. A few options:

https://github.com/python-gino/gino
https://www.encode.io/databases/ (and https://github.com/encode/orm)

As well as database-specific options such as:

https://pypi.org/project/aiosqlite/
https://github.com/aio-libs/aiopg

We decided to try databases due to support for both sqlite and postgresql.
'''
import asyncio
import functools

import json
import yaml

import asyncpg
from databases import Database
import sqlalchemy


async def initialize(reset=False):
    pass


async def set_resource_state(username, resource):
    pass


async def get_resource_state(username, resource):
    pass


async def fetch_events(username, resource):
    '''
    Grab all the events for a particular user / resource

    `resource` is typically `googledocs://docstring`
    '''
    pass


async def insert_event(username, resource, event):
    '''
    Store an event in the database
    '''
    pass


async def get_class(username, class_id=None):
    '''
    Return all the students in a teacher's class.

    Teachers can have multiple classes.
    '''
    pass


async def get_recipients(username):
    '''
    Return all the teachers who should be notified of events for user
    `username`
    '''
    pass


# database = Database('sqlite:///example.db')
# await database.connect()

metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String(length=100)),
    #  Should we have a roles table instead?
    sqlalchemy.Column("is_student", sqlalchemy.Boolean()),
    sqlalchemy.Column("is_teacher", sqlalchemy.Boolean()),

)
schools = sqlalchemy.Table(
    "schools",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(length=100)),
)

classes = sqlalchemy.Table(
    "classes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(length=100)),
)

class_students = sqlalchemy.Table(
    "class_student",
    metadata,
    sqlalchemy.Column("student_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("class_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("class.id")),
)


# engine = sqlalchemy.create_engine(str(database.url))
# metadata.create_all(engine)

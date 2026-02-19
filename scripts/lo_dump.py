'''
This is a short script to load data from redis.

It exports Learning Observer data in a human / Python-friendly
format. This is nice if you'd like to download data and modify it,
e.g.:

* For test cases
* For a demo
* Etc.

It is **not** intended for production use. Performance won't be
there. It does a full table scan. It's not ACID. Etc. If you'd like
similar functionality in production, `redis` has built-in persistance:

https://redis.io/topics/persistence

To do: We should make this script abstract:
* Use LO's KVS abstraction, rather than redis directly
* As a correlary to the above, use the config file to authenticated
  if redis is e.g. non-local
* Take semantic arguments (e.g. course, users, etc.) rather than a
  query string

Until at least the last one (so API is fixed), we should not build
dependencies around this script. A one-off hack is fine in
development, but nothing committed to the repo which calls this with a
query string.
'''

import argparse
import json
import sys

import redis

parser = argparse.ArgumentParser(
    description=__doc__.strip(),
    formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument(
    '--query-string', default='*',
    help="Query string for which keys we ought to receive from redis"
)
parser.add_argument(
    '--out', type=argparse.FileType('x', encoding='UTF-8'),
    help="Output filename"
)

args = parser.parse_args()

if args.out is None:
    out = sys.stdout
else:
    out = args.out

r = redis.Redis()
keys = r.keys(args.query_string)

# For now, we alternate keys and data per line
for key in keys:
    out.write(key.decode('utf-8'))
    out.write('\n')
    # We do a load-and-dump to avoid new lines, in case of data
    # corruption or similar. It's really not necessary.
    out.write(json.dumps(json.loads(r.get(key))))
    out.write('\n')

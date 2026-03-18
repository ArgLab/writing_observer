'''
This is a short script to write data to redis.

It reads data from `lo_load`. See `lo_load` documentation for details.

It is **not** intended for production use, or even for use within
archival scripts. Data formats, command line interfaces, etc. may and
probably will change.
'''

import argparse

import redis

parser = argparse.ArgumentParser(
    description=__doc__.strip(),
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument(
    '--in', type=argparse.FileType('r', encoding='UTF-8'),
    dest="filename",
    help="Input filename"
)

args = parser.parse_args()

if args.filename is None:
    parser.print_usage()

r = redis.Redis()

odd = True

# For now, we alternate keys and data per line
for line in args.filename:
    if odd:
        odd = False
        key = line.strip()
    else:
        odd = True
        value = line.strip()
        r.set(key, value)

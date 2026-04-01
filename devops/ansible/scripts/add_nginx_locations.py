"""
This script adds the locations for our web API to nginx. It adds
them after the default location.
"""

import sys
import shutil
import datetime

lines = open("/etc/nginx/sites-enabled/default", "r").readlines()

# If we've already added these, do nothing.
for line in lines:
    if "webapi" in line:
        print("Already configured!")
        sys.exit(-1)

# We will accumulate the new file into this variable
output = ""

# We step through the file until we find the first 'location' line, and
# keep cycling until we find a single "}" ending that section.
#
# At that point, we add the new set of location

location_found = False
added = False
for line in lines:
    output += line
    if line.strip().startswith("location"):
        print("Found")
        location_found = True
    if location_found and line.strip() == "}" and not added:
        output += open("../files/nginx-locations").read()
        added = True


backup_file = "/etc/nginx/sites-enabled-default-" + \
              datetime.datetime.utcnow().isoformat()
shutil.move("/etc/nginx/sites-enabled/default", backup_file)

with open("/etc/nginx/sites-enabled/default", "w") as fp:
    fp.write(output)

print(output)

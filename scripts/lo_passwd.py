#!/usr/bin/python3
'''
Add user to a password file.
We shouldn't be reinventing wheels. But we couldn't find a good one.

As a format issue, we explicitly don't want extranous fields in the file. If
the user doesn't provide an optional field, we don't want to add it to the
file. We provide defaults on read rather than on write. This keeps the file
smaller, cleaner, and easier to read.

We should think through which fields we want. Right now, this is ad-hoc. In
particular:

- Name format (with i18n issues)
- Picture / avatar format (filename? URL?)

Most systems do this wrong. Chinese names have last name first, and
some cultures have more than first/middle/last names. We don't want to
have a Eurocentric format.

We should also break this out into a library, so that `user_fields`, etc. are
consistent across the project.
'''

import argparse
import datetime
import getpass
import os.path
import sys

import bcrypt
import yaml


# Our default user data structure
# We'll populate this with the user's data from the arguments
# and inputs
user_fields = [
    'username',
    'password',
    'email',
    'name',
    'family_name',
    'picture',
    'notes',
    'role'
    # 'authorized',  <-- These will be set automatically
    # 'created_at',
    # 'updated_at'
]

# We need these two fields -- the rest are optional
# We'll prompt for them if they're not provided
required_fields = [
    'username',
    'password'
]

# These fields, we won't echo
secure_fields = ['password']


def read_password_yaml(filename):
    '''
    Read the password file.

    If the file doesn't exist, create it. If it does exist,
    but is missing the required fields, create those fields.

    Args:
        filename (str): The filename to read.

    Returns:
        dict: The password file.
    '''
    data = {}
    if os.path.exists(args.filename):
        with open(filename, 'r') as f:
            data = yaml.safe_load(f)

    if data is None:
        data = {}

    if 'users' not in data:
        data['users'] = {}

    return data


def write_password_yaml(filename, data):
    '''
    Write the password file.

    Args:
        filename (str): The filename to write.
        data (dict): The data to write.
    '''
    with open(filename, 'w') as f:
        yaml.dump(data, f)


def update_password_yaml(password_dict, new_user):
    '''
    Update the password dictionary.

    Args:
        password_dict (dict): The password file.
        new_user (dict): The new user to add or update.

    Returns:
        dict: The updated password file.

    Note that the password_dict is modified in place.
    '''
    username = new_user['username']
    if username not in password_dict['users']:
        password_dict['users'][username] = {}
    password_dict['users'][username].update(new_user)

    now = datetime.datetime.now().isoformat()
    if 'created_at' not in password_dict['users'][username]:
        password_dict['users'][username]['created_at'] = now
    password_dict['users'][username]['updated_at'] = now

    return password_dict


def prompt_for_user_data():
    '''
    Parse arguments, and prompt for missing fields.

    Returns:
        dict: The user's data.
    '''
    user_data = {}

    for field in user_fields:
        if field in args.__dict__ and args.__dict__[field] is not None:
            user_data[field] = args.__dict__[field]
        elif field in secure_fields:
            user_data[field] = getpass.getpass(f'{field}: ')
        elif field in required_fields:
            user_data[field] = input(f"{field} (required): ")
        elif not args.no_prompt:
            response = input(f"{field} (optional): ")
            if response != '':
                user_data[field] = response
        if field in required_fields and user_data[field] == '':
            print(f"{field} is required.")
            sys.exit(1)
        if field == 'password':
            hashpw = bcrypt.hashpw(
                user_data[field].encode('utf-8'),
                bcrypt.gensalt()
            )
            # This is a work-around for version issues in bcrypt.
            # It sometimes returns strings, and sometimes bytes.
            if isinstance(hashpw, bytes):
                hashpw = hashpw.decode('utf-8')
            user_data[field] = hashpw

    return user_data


# Grab the arguments
parser = argparse.ArgumentParser(
    description=__doc__.strip(),
    formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument(
    '--filename', required=True
)

parser.add_argument(
    '--no-prompt', action='store_true'
)

for field in user_fields:
    parser.add_argument("--" + field)

args = parser.parse_args()

password_dict = read_password_yaml(args.filename)
user_data = prompt_for_user_data()
password_dict = update_password_yaml(password_dict, user_data)
print(password_dict['users'][user_data['username']])
write_password_yaml(args.filename, password_dict)

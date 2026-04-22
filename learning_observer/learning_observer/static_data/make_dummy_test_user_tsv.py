import random

import names

import tsvx

user_id_template = "tsu-ts-test-user-{i}"
w = tsvx.writer(open("class_lists/test_users.tsvx", "w"))
w.title = "Test users"
w.description = "Test user file to go with stream_writing.py"
w.headers = ["user_id", "name", "full_name", "email", "phone"]
w.types = [str, str, str, str, str]

w.write_headers()
for i in range(25):
    name = names.get_first_name()
    w.write(
        user_id_template.format(i=i),
        name,
        "{fn} {ln}".format(fn=name, ln=names.get_last_name()),
        "{name}@school.district.us".format(name=name),
        "({pre})-{mid}-{post}".format(
            pre=random.randint(200, 999),
            mid=random.randint(200, 999),
            post=random.randint(1000, 9999))
    )

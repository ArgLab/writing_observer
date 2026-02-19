'''
This creates a roster with all students in Redis
'''

import learning_observer.kvs

from learning_observer.log_event import debug_log


async def all_students():
    '''
    This crawls the keys of the KVS, and creates a list of all
    student IDs in the KVS.
    '''
    keys = await learning_observer.kvs.KVS.keys()
    internal_keys = [k for k in keys if k.startswith("Internal:")]
    split_keys = [k.split(":") for k in internal_keys]
    valid_keys = [k for k in split_keys if len(k) > 2]
    user_ids = sorted(set([k[2] for k in valid_keys]))
    debug_log(user_ids)
    return user_ids


async def all_students_course_list():
    return [
        {
            "id": "12345678901",
            "name": "All Students",
            "descriptionHeading": "For easy small-scale deploys",
            "alternateLink": "https://www.ets.org/",
            "teacherGroupEmail": "",
            "courseGroupEmail": "",
            "teacherFolder": {
                "id": "",
                "title": "All Students",
                "alternateLink": ""
            },
            "calendarId": "NA"
        }
    ]


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(all_students_roster())

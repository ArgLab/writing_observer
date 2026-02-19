'''
This will program populate redis with dummy writing data for one
course. It should be run from the same directory as creds.yaml. This
is primarily intended for development use.
'''

import asyncio

import learning_observer.constants
import learning_observer.google
import learning_observer.settings
import learning_observer.offline
import learning_observer.rosters
import learning_observer.kvs

import writing_observer.writing_analysis
from learning_observer.stream_analytics.fields import KeyField, KeyStateType, EventField

import writing_observer.sample_essays


async def select_course():
    """
    This is an asynchronous function that allows the user to select a
    course from a list of courses. The function prints each course's name
    along with its index, and prompts the user to select a course by
    entering the index number. The function returns the ID of the selected
    course.
    """
    courses = await learning_observer.rosters.courselist(learning_observer.offline.request)

    for course, i in zip(courses, range(len(courses))):
        print(f"{i}: {course['name']}")

    course_index = int(input("Please select a course: "))
    return courses[course_index]['id']


async def print_roster(course):
    """
    This is an asynchronous function that takes a course as an
    argument and prints its roster of students. It returns the
    roster too.
    """
    roster = await learning_observer.rosters.courseroster(learning_observer.offline.request, course)
    print("\nStudents\n========")
    for student in roster:
        print(student['profile']['name']['full_name'])
    return roster


async def select_text_type():
    """
    This is an asynchronous function that allows the user to select a
    text type from a list of available text types from the
    `sample_essays` module. These include GPT3-generate text, lorem
    ipsum, etc.
    """
    available_text_types = writing_observer.sample_essays.TextTypes.__members__
    tt_list = list(available_text_types)

    print("\nText types\n=====\n")
    for text_type, idx in zip(tt_list, range(len(tt_list))):
        print(f"{idx}: {text_type}")

    idx = int(input("Please pick a text type: "))
    text_type = available_text_types[tt_list[int(idx)]]
    print(f"Text type: {text_type}")
    return text_type


async def set_text(kvs, student_id, text, docid):
    '''
    Set a text for the student in redis.
    '''
    document_id = f"test-doc-{docid}"
    for kst in [KeyStateType.INTERNAL, KeyStateType.EXTERNAL]:
        last_document_key = learning_observer.stream_analytics.helpers.make_key(
            writing_observer.writing_analysis.last_document,
            {
                KeyField.STUDENT: student_id,
            },
            kst
        )
        document_key = learning_observer.stream_analytics.helpers.make_key(
            writing_observer.writing_analysis.reconstruct,
            {
                KeyField.STUDENT: student_id,
                EventField('doc_id'): document_id
            },
            kst
        )
        await kvs.set(last_document_key, {"document_id": document_id})
        await kvs.set(document_key, {"text": text})
    print("LDK", last_document_key)
    print("DK", document_key)


async def main():
    learning_observer.offline.init()
    kvs = learning_observer.kvs.KVS()
    course = await select_course()
    roster = await print_roster(course)
    text_type = await select_text_type()

    texts = writing_observer.sample_essays.sample_texts(
        text_type=text_type,
        count=len(roster)
    )

    for student, text, idx in zip(roster, texts, range(len(roster))):
        print(student)
        await set_text(kvs, student[learning_observer.constants.USER_ID], text, idx)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

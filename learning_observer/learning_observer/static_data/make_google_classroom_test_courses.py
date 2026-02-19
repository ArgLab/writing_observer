import json
import random
import names


def make_courses():
    random.seed(0)
    courses = [
        {
            "name": "Biology 1A",
            "descriptionHeading": "7th grade biology, period 1",
        },
        {
            "name": "Biology 1B",
            "descriptionHeading": "7th grade biology, period 2",
        },
        {
            "name": "Biology 2A",
            "descriptionHeading": "8th grade biology, period 4",
        },
        {
            "name": "Biology 1B",
            "descriptionHeading": "8th grade biology, period 7",
        }
    ]
    for course in courses:
        course["id"] = str(random.randint(10**10, 10**11))
        course["ownerId"] = str(random.randint(10**19, 10**20))
        course["creationTime"] = "2019-{M}-{D}T{h}:{m}:{s}.000Z".format(
            M=random.randint(1, 12),
            D=random.randint(1, 30),
            h=random.randint(1, 24),
            m=random.randint(10, 59),
            s=random.randint(10, 59),
        )
        course["updateTime"] = "2020-{M}-{D}T{h}:{m}:{s}.000Z".format(
            M=random.randint(1, 12),
            D=random.randint(1, 30),
            h=random.randint(1, 24),
            m=random.randint(10, 59),
            s=random.randint(10, 59),
        )
        course["enrollmentCode"] = "".join([chr(random.randint(97, 123)) for i in range(7)])
        course["courseState"] = "ACTIVE"
        course["alternateLink"] = "https://classroom.google.com/c/ABCD1234"
        course["teacherGroupEmail"] = "foo@localhost"
        course["teacherFolder"] = {
            "id": "A" * 72,
            "title": course["name"],
            "alternateLink": "https://drive.google.com/drive/folders/" + "A" * 72
        }
        course["guardiansEnabled"] = False
        course["calendarId"] = "ABCD1234@group.calendar.google.com"
    return {'courses': courses}


def make_roster(course_id, N):
    students = []
    for i in range(N):
        student_id = str(random.randint(10**20, 10**21))
        fn = names.get_first_name()
        ln = names.get_last_name()
        student = {
            'course_id': course_id,
            'user_id': student_id,
            'profile': {
                'id': student_id,
                'name': {'given_name': fn, 'family_name': ln, 'full_name': '{fn} {ln}'.format(fn=fn, ln=ln)}
            }
        }
        students.append(student)
    return {'students': students}


with open("courses.json", "w") as fp:
    fp.write(json.dumps(make_courses(), indent=3))

with open("students.json", "w") as fp:
    fp.write(json.dumps(make_roster(course_id="41016982062", N=20), indent=3))

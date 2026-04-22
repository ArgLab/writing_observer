import pytest

import writing_observer.nlp_indicators


def synthesize_student(id, course_id=None):
    """
    Create a fake student under a given course_id
    """
    if course_id is None:
        course_id = '1234567890'
    first = f'student-{id}'
    family = 'last'
    student = {
        "course_id": course_id,
        "user_id": id,
        "profile": {
            "id": id,
            "name": {
                "given_name": first,
                "family_name": family,
                "full_name": f'{first} {family}'
            },
            "email_address": f"{first}@example.com",
            "photo_url": "https://lh3.googleusercontent.com/photo.jpg"
        }
    }
    return student


@pytest.fixture(scope='session')
def fetch_students():
    students = [synthesize_student(i) for i in range(10)]
    return students


@pytest.fixture(scope='session')
def fetch_nlp_options():
    return writing_observer.nlp_indicators.INDICATOR_JSONS

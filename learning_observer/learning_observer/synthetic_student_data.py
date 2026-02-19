'''
Note that current loremipsum in `pip` is not Python 3
compatible. If you are getting b'' in your text, the
patch is at:

`https://github.com/monkeython/loremipsum/issues/10`
'''

import random

import numpy
import numpy.random

import loremipsum
import names

import learning_observer.util as util


def synthetic_student_data(student_id):
    '''
    Create fake student data for mock-up UX for one student
    '''
    name = names.get_first_name()
    essay = "\n".join(loremipsum.get_paragraphs(5))
    return {
        'id': student_id,
        'name': name,
        'email': "{name}@school.district.us".format(name=name),
        'address': "1 Main St",
        'phone': "({pre})-{mid}-{post}".format(
            pre=random.randint(200, 999),
            mid=random.randint(200, 999),
            post=random.randint(1000, 9999)),
        'avatar': "avatar-{number}".format(number=random.randint(0, 14)),
        'ici': random.uniform(100, 1000),
        'essay_length': len(essay),
        'essay': essay,
        'writing_time': random.uniform(5, 60),
        'text_complexity': random.uniform(3, 9),
        'google_doc': "https://docs.google.com/document/d/1YbtJGn7ida2IYNgwCFk3SjhsZ0ztpG5bMzA3WNbVNhU/edit",
        'time_idle': numpy.random.gamma(0.5, scale=5),
        'outline': [{"section": "Problem " + str(i + 1),
                     "length": random.randint(1, 300)} for i in range(5)],
        'revisions': {}
    }


def synthetic_data(student_count=20):
    '''
    Generate paginated mock student data for `student_count` students.
    '''
    data = [
        synthetic_student_data(i)
        for i in range(student_count)
    ]
    return util.paginate(data, 4)


if __name__ == '__main__':
    print(synthetic_data())

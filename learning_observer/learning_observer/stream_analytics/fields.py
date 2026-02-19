'''
We would like to be able to aggregate data across many axes; for example,
we might want to aggregate data across teachers, across schools, etc.

We do this by having a list of fields we'd like to aggregate over. For example,
if we wanted to aggregate data by problem by student (e.g. to see how much time
each student spent on a problem), we'd have a list like this:

`student, problem`

This would allow us to make a key which, in pseudo-code, would look like this:

`student="Bob", problem="Pythagorean Triples"`

At that point, the reduced would reduce over that problem, student pair (and every
other such pair).

These are called fields. The concept is taken from XBlocks.

https://edx.readthedocs.io/projects/xblock-tutorial/en/latest/concepts/fields.html
'''

import enum
import functools


@functools.total_ordering
class EventField:
    '''
    This is a field type used for extracting a particular element from an event.
    '''
    def __init__(self, event):
        if not event.replace(".", "").replace("-", "").replace("_", "").isalnum():
            # Suspicious operation. We'd like a better exception.
            # This happens when either:
            # * There is a bug in our code
            # * Someone tries a SQL injection or similar attack
            #
            # We use repr to prevent things like newlines from being
            # included in the text verbatim.
            raise AttributeError(
                "Events should be alphanumeric, dashes, and underscores:"
                "{}".format(event=repr(event))
            )
        self.event = event
        self.name = "EventField." + self.event

    def __hash__(self):
        return hash(self.event)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<{name}>".format(name=self.name)

    def __eq__(self, other):
        if not isinstance(other, EventField):
            return False

        return self.event == other.event

    def __lt__(self, other):
        if not isinstance(other, EventField):
            raise TypeError("< not supported between instances of 'EventField' and other types")

        return self.event < other.event


KeyStateType = enum.Enum("KeyStateType", "INTERNAL EXTERNAL")

# This is a set of fields which we use to index reducers. For example,
# if we'd like to know how many students accessed a specific Google
# Doc, we might create a RESOURCE key (which would receive events for
# all students accessing that resource). If we'd like to keep track of
# a students' work in a particular Google Doc, we'd create a
# STUDENT/RESOURCE key.
#
# At some point, this shouldn't be hardcoded
#
# We'd also like a better way to think of the hierarchy of assignments than ITEM/ASSIGNMENT
KeyFields = [
    "STUDENT",      # A single student
    "CLASS",        # A group of students. Typically, one class roster in Google Classroom
    "RESOURCE",     # E.g. One Google Doc
    # "ASSIGNMENT"  # E.g. A collection of Google Docs (e.g. notes, outline, draft)
    # TODO we are not 100% sold on the TEACHER / STUDENT split.
    "TEACHER"       #
    #  ...          # ... and so on.
]

KeyField = enum.Enum("KeyField", " ".join(KeyFields))


class Scope(frozenset):
    '''
    A scope is a set of KeyFields and EventFields.
    '''
    pass


class ScopeFieldError(Exception):
    '''
    Exception used if we e.g. try to add an incorrect type to a scope, have
    a mismatched key to a scope, etc. Perhaps this might be a few exceptions
    in the future.
    '''
    pass

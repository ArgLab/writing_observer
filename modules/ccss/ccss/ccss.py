'''
This is a simple interface to navigate Common Core State Standards.
'''

from pkg_resources import resource_filename
import json

ELA = 'ELA-Literacy'
MATH = 'Math'


class Standard:
    def __init__(self, standard_str):
        self.standard_str = standard_str.replace("Math.Content", "Math")
        parts = self.standard_str.split('.')
        self.subject = parts[1]
        if self.subject == ELA:
            self.subdomain = parts[2]
            self.grade = parts[3]
            self.id = ".".join(parts[4:])
        elif self.subject == MATH:
            self.subdomain = parts[3]
            self.grade = parts[2]
            self.id = ".".join(parts[4:])
        else:
            raise AttributeError("Unknown subject")

    def __str__(self):
        return self.standard_str


class Standards(dict):
    def query(self, func):
        return Standards(
            {
                key: value
                for key, value in self.items()
                if func(Standard(key))
            }
        )

    def math(self):
        # Return a new Standards object with just math items
        return self.query(lambda key: key.subject == MATH)

    def ela(self):
        # Return a new Standards object with just ELA items
        return self.query(lambda key: key.subject == ELA)

    def subdomain(self, subdomains):
        # Handle lists or individual values
        if not isinstance(subdomains, list):
            subdomains = [subdomains]
        # Return a new Standards object with specified subdomain items
        return self.query(lambda key: key.subdomain in subdomains)

    def id(self, ids):
        # Handle lists or individual values
        if not isinstance(ids, list):
            ids = [ids]
        # Return a new Standards object with specified id items
        return self.query(lambda key: key.id in ids)

    def grade(self, grade_levels):
        # Handle lists or individual values
        if not isinstance(grade_levels, list):
            grade_levels = [grade_levels]

        # Handle integers
        grade_levels = list(map(str, grade_levels))
        return self.query(lambda key: key.grade in grade_levels)

    def subdomains(self):
        all_subdomains = {Standard(key).subdomain for key in self}
        return sorted(all_subdomains)

    def ids(self):
        all_ids = {Standard(key).id for key in self}
        return sorted(all_ids)

    def grades(self):
        all_grades = {Standard(key).grade for key in self}
        return sorted(all_grades)


json_file_path = resource_filename(__name__, 'ccss.json')

standards = Standards(json.load(open(json_file_path)))

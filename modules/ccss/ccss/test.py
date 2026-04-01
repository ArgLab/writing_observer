'''
For now, this just runs all the code paths and checks return
types. We should do something more robust later.
'''

import unittest

import ccss


class TestStandards(unittest.TestCase):
    def test_math(self):
        math_standards = ccss.standards.math()
        self.assertIsInstance(math_standards, ccss.Standards)

    def test_ela(self):
        ela_standards = ccss.standards.ela()
        self.assertIsInstance(ela_standards, ccss.Standards)

    def test_subdomain_with_list(self):
        sub_standards = ccss.standards.subdomain(['Math'])
        self.assertIsInstance(sub_standards, ccss.Standards)

    def test_subdomain_with_str(self):
        sub_standards = ccss.standards.subdomain('Math')
        self.assertIsInstance(sub_standards, ccss.Standards)

    def test_id_with_list(self):
        sub_standards = ccss.standards.id(['1', '2'])
        self.assertIsInstance(sub_standards, ccss.Standards)

    def test_id_with_str(self):
        sub_standards = ccss.standards.id('1')
        self.assertIsInstance(sub_standards, ccss.Standards)

    def test_grade_with_list(self):
        sub_standards = ccss.standards.grade(['1', '2'])
        self.assertIsInstance(sub_standards, ccss.Standards)

    def test_grade_with_str(self):
        sub_standards = ccss.standards.grade('1')
        self.assertIsInstance(sub_standards, ccss.Standards)

    def test_grade_with_int(self):
        sub_standards = ccss.standards.grade(1)
        self.assertIsInstance(sub_standards, ccss.Standards)


if __name__ == '__main__':
    unittest.main()

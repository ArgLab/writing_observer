'''
Rather minimalistic install script. To install, run `python
setup.py develop` or just install via requirements.txt
'''

from setuptools import setup, find_packages

setup(
    name="wo_common_student_errors",
    package_data={
        'wo_common_student_errors': ['assets/*'],
    }
)

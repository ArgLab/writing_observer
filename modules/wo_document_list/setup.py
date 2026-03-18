'''
Rather minimalistic install script. To install, run `python
setup.py develop` or just install via requirements.txt
'''

from setuptools import setup

setup(
    name="wo_document_list",
    package_data={
        'wo_document_list': ['assets/*'],
    }
)

'''
Rather minimalistic install script. To install, run `python
setup.py develop` or just install via requirements.txt
'''

from setuptools import setup, find_packages

setup(
    name="wo_highlight_dashboard",
    package_data={
        'wo_highlight_dashboard': ['assets/*'],
    }
)

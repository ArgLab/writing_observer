import json
import os
from setuptools import setup
from setuptools.command.develop import develop as _develop
import subprocess
import sys

with open('package.json') as f:
    package = json.load(f)

package_name = package["name"].replace(" ", "_").replace("-", "_")
new_path = '/'.join(sys.executable.split('/')[:-1])
current_path = os.environ['PATH']
modified_env = {'PATH': f'{new_path}{os.pathsep}{current_path}'}

package_path = os.path.abspath(os.path.dirname(__file__))

class ReactSetup(_develop):
    '''
    LO_dash_react_components relies on Dash to be installed.
    To ensure Dash (and any other downstream dependencies) are resolved first,
    we install LODRC after the install_requires
    '''
    def run(self):
        _develop.run(self)
        subprocess.run(['npm', 'install', package_path], env=modified_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['npm', 'run', '--prefix', package_path, 'build'], env=modified_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


setup(
    name=package_name,
    version=package["version"],
    author=package['author'],
    packages=[package_name],
    include_package_data=True,
    license=package['license'],
    description=package.get('description', package_name),
    install_requires=[s.strip() for s in open(os.path.join(package_path, 'requirements.txt')).readlines() if len(s) > 1],
    classifiers=[
        'Framework :: Dash',
    ],
    cmdclass={
        'develop': ReactSetup
    }
)

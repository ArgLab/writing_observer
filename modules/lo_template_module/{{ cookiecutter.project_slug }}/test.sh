#!/bin/bash
# modules/{{ cookiecutter.project_slug }}/test.sh
echo "================================================="
echo "Running tests for {{ cookiecutter.project_name }}"
echo "================================================="

# Modify the commands below to fit your testing needs
echo "Running traditional pytests"
pytest tests/
echo "Running doctests"
pytest --doctest-modules

#!/bin/bash
# modules/wo_portfolio_diff/test.sh
echo "================================================="
echo "Running tests for Writing Observer Portfolio Diff"
echo "================================================="

# Modify the commands below to fit your testing needs
echo "Running traditional pytests"
pytest tests/
echo "Running doctests"
pytest --doctest-modules

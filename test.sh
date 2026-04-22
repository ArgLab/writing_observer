#!/bin/bash
# test.sh
# This script iterates over the passed in `PACKAGES`,
# change directory to that path, and execute the `test.sh`
# file.
set -e  # Exit immediately if a command exits with a non-zero status

# Parse arguments
PACKAGES=("$@")

# Check for no arguments
if [ ${#PACKAGES[@]} -eq 0 ]; then
    echo "Error: No packages specified."
    echo "Usage:"
    echo "$0 /path/to/package_a path/to/package_b ..."
    echo "or"
    echo "make test PKG=/path/to/package_a"
    exit 1
fi

echo "Running tests for: ${PACKAGES[*]}"

# Run tests for each package
for package in "${PACKAGES[@]}"; do
    ABS_PACKAGE_PATH="$(cd "$(dirname "$package")" && pwd)/$(basename "$package")/"
    PACKAGE_TEST_SCRIPT="$ABS_PACKAGE_PATH/test.sh"

    # Debug directory
    if [ -d "$ABS_PACKAGE_PATH" ]; then
        echo "Directory exists: $ABS_PACKAGE_PATH"
    else
        echo "Warning: Directory does not exist: $ABS_PACKAGE_PATH, skipping."
        continue
    fi

    # Check if the file exists
    if [ -f "$PACKAGE_TEST_SCRIPT" ]; then
        echo "Running $PACKAGE_TEST_SCRIPT..."
        (cd "$ABS_PACKAGE_PATH" && ./test.sh)
    else
        echo "Warning: No test.sh found in $package, skipping."
    fi
done

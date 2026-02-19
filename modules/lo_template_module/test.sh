# This is a small script which builds and installs a test of this template.
#
# It is helpful for development.
#
# Be careful to run it from this directory.

current_directory=$(pwd)
if [ ! -f "$current_directory/test.sh" ] || [ ! -f "$current_directory/test_module.json" ]; then
    echo "test.sh should be run from the directory where it (and test_module.json) are located (e.g. modules/lo_template_module)"
    exit 1
fi

cd ..
rm -Rf test_template_module
cookiecutter lo_template_module/ --replay-file lo_template_module/test_module.json
cd test_template_module
pip install -e .

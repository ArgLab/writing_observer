# TODO rename these packages to something else
PACKAGES ?= wo

help:
	@echo "Available commands:"
	@echo ""
	@echo "  run                          Run the learning_observer Python application."
	@echo "	 install-pre-commit-hook      Install the pre-commit git hook."
	@echo "  install                      Install the learning_observer package in development mode."
	@echo "  install-dev                  Install dev dependencies (requires additional setup)."
	@echo "  install-packages             Install specific packages: [${PACKAGES}]."
	@echo "  test                         Run tests for the specified package (PKG=<package>)."
	@echo "  linting-setup                Setup linting tools and dependencies."
	@echo "  linting-python               Lint Python files using pycodestyle and pylint."
	@echo "  linting-node                 Lint Node files (JS, CSS, and unused CSS detection)."
	@echo "  linting                      Perform all linting tasks (Python and Node)."
	@echo "  build-wo-chrome-extension    Build the writing-process extension."
	@echo "  build-python-distribution    Build a distribution for the specified package (PKG=<package>)."
	@echo ""
	@echo "Note: All commands are executed in the current shell environment."
	@echo "      Ensure your virtual environment is activated if desired, as installs and actions"
	@echo "      will occur in the environment where the 'make' command is run."
	@echo ""
	@echo "Use 'make <command>' to execute a command. For example: make run"

run:
	# If you haven't done so yet, run: make install
	# we need to make sure we are on the virtual env when we do this
	cd learning_observer && python learning_observer

# Install commands
install-pre-commit-hook:
	# Adding pre-commit.sh to Git hooks
	cp scripts/hooks/pre-commit.sh .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

install: install-pre-commit-hook
	# The following only works with specified packages
	# we need to install learning_observer in dev mode to
	# more easily pass in specific files we need, such as creds
	pip install --no-cache-dir -e learning_observer/

	# Installing Learning Oberser (LO) Dash React Components
	# TODO properly fetch the current version of lodrc.
	# We have a symbolic link between `lodrc-current` and the most
	# recent version. We would like to directly fetch `lodrc-current`,
	# however, the fetch only returns the name of the file it's
	# linked to. We do an additional fetch for the linked file.
	@LODRC_CURRENT=$$(curl -s https://raw.githubusercontent.com/ETS-Next-Gen/lo_assets/main/lo_dash_react_components/lo_dash_react_components-current.tar.gz); \
	pip install https://raw.githubusercontent.com/ETS-Next-Gen/lo_assets/main/lo_dash_react_components/$${LODRC_CURRENT}

install-dev:
	# TODO create a dev requirements file
	pip install --no-cache-dir -e learning_observer/[${PACKAGES}]
	. ${HOME}/.nvm/nvm.sh && nvm use && pip install -v -e modules/lo_dash_react_components/

install-packages:
	pip install -e learning_observer/[${PACKAGES}]

# Testing commands
test:
	@if [ -z "$(PKG)" ]; then echo "No module specified, please try again with \"make test PKG=path/to/module\""; exit 1; fi
	./test.sh $(PKG)

# Linting commands
linting-python:
	# Linting Python modules
	pip install pycodestyle pylint
	pycodestyle --ignore=E501,W503 $$(git ls-files 'learning_observer/*.py' 'modules/*.py')
	pylint -d W0613,W0511,C0301,R0913,too-few-public-methods $$(git ls-files 'learning_observer/*.py' 'modules/*.py')

linting-node:
	npm install
	# TODO each of these have lots of errors and block
	# the next item from running
	# Starting to lint Node modules
	# Linting Javascript
	npm run lint:js
	# Linting CSS
	npm run lint:css
	# Finding any unused CSS files
	npm run find-unused-css

linting: linting-setup linting-python linting-node
	# Finished linting

# Build commands
build-wo-chrome-extension:
	# Installing LO Event
	cd modules/lo_event && npm install & npm link lo_event
	# Building extension
	cd extension/writing-process && npm install && npm run build

build-python-distribution:
	# Building distribution for package
	pip install build
	# Switching to package directory
	cd $(PKG) && python -m build

# TODO we may want to have a separate command for uploading to testpypi
upload-python-package-to-pypi: build-python-distribution
	pip install twine
	# TODO we currently only upload to testpypi
	# TODO we need to include `TWINE_USERNAME=__token__`
	# and `TWINE_PASSWORD={ourTwineToken}` to authenticate
	#
	# TODO We have not fully tested the following commands.
	# Try out the following steps and fix any bugs so the
	# Makefile can do it automatically.
	# cd $(PKG) && twine upload -r testpypi dist/*

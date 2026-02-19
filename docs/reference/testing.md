# Testing

Testing is an essential part of software development to ensure the reliability and stability of your code. In the Learning Observer project, we currently support Python testing, using the pytest framework. This document provides an overview of how the testing framework is used in the project.

## Preparing a Module for Testing

The following workflow is a **HACK** while we work toward better testing infrastructure.
Each module should define a `test.sh` at the root of the module's directory. This script should define how to run the tests for the module.

### How Testing Ought to be

We want to have a finite set of testing infrastructure. The types of tests we ought to support are

- Client / dashboard tests
  - Basic: we're not getting 500 errors on any pages (which can be semi-automatic from routes)
  - Advanced: things work as expected.
- Python unit tests
- Server-side integration tests
- Data pipeline tests
  - The very explicit models, like reducers, are designed to support this
  - Also, query language, etc.
  - This is related to replicability, which is important in science and in debugging in ways we discussed

We should have an opinionated, recommended way to do things, included in the example template package.

## Running Tests

The Makefile offers a `test` command which calls an overall `test.sh` script. This script takes the passed in module paths and runs each of their respective `test.sh` scripts. To run via the Makefile, use

```bash
make test PKG=path/to/module
# OR to test multiple packages at once
make test PKG="modules/writing_observer learning_observer"
```

## GitHub Actions for Automated Testing

To automate testing in your project, you can use GitHub Actions. This allows you to run tests automatically when you push changes to your repository. The provided GitHub Action YAML file will iterate over the defined modules and

1. Check for any changes within that module. If no changes are found, proceed to next module in list.
1. Install Learning Observer - `make install`
1. Install the module itself - `pip install path/to/module`
1. Run tests - `make test PKG=path/to/module`

To add an additional module to this testing pipeline, add its path to the list of packages under the matrix strategy in `.github/workflows/test.yml`, like so:

```yml
  strategy:
    matrix:
      package: ['learning_observer/', 'modules/writing_observer/', 'path/to/new/module/']
```

## Python Testing

We use the [pytest framework](https://docs.pytest.org/) for Python testing. Pytest is a popular testing framework that simplifies writing and running test cases. It provides powerful features, such as fixtures, parametrized tests, and plugins, to help you test your code efficiently and effectively.

### Setting Up the Testing Environment

Before writing and running tests, it's essential to set up the testing environment correctly. Here is a step-by-step guide on how to set up the testing environment:

1. Install Python dependencies required for the project. You can find these dependencies in the `requirements.txt` file in the project's root directory.
2. Install the Python packages for the modules you will be testing. In the Learning Observer project, this includes the `writing_observer`, `lo_dash_react_components`^, and `wo_highlight_dashboard` modules.

^ This requires node v16 to installed as it needs to build the components during install

### Writing Test Cases

To write test cases for your Python code, follow these guidelines:

1. Create a `tests` directory in the module you want to test, if it doesn't already exist.
2. For each file or functionality you want to test, create a separate test file with a name in the format `test_<filename>.py` or `test_<functionality>.py`.
3. Inside each test file, write test functions that test specific aspects of your code. Start each test function's name with `test_` to ensure that pytest can discover and run the test.

### Running PyTests

Once you have written your test cases, you can run them using the pytest command:

```bash
pytest <module_directory>
```

For example, to run tests for the `wo_highlight_dashboard` module, you would run:

```bash
pytest modules/wo_highlight_dashboard/
```

## Other testing

Not yet implemented.

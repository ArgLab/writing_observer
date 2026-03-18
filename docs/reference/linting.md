# Linting

This documentation provides an overview of the linting configurations and tools used in the project. Linting is an essential step in the development process, helping to ensure code consistency and quality by detecting potential errors and enforcing stylistic conventions.

## Linting the code

### Python

To lint any Python code, run:

`pycodestyle --ignore=E501,W503 $(git ls-files 'learning_observer/*.py' 'modules/*.py')`

### CSS and JS

In the `package.json` file, we define several npm scripts to run the linting tasks:

- `npm run lint:css`: Runs `stylelint` on all CSS and SCSS files.
- `npm run lint:js`: Runs `eslint` on all JavaScript files.
- `npm run lint`: Runs both `lint:css` and `lint:js`.
- `npm run find-unused-css`: Runs the custom script to find unused CSS.

## GitHub Action

We use a GitHub Action to handle the linting process for our codebase. This action is triggered on every push to the repository. It consists of two jobs: `lint-python` and `lint-node`.

### Linting Python Code

The `lint-python` job is responsible for linting Python code in the project. It uses `pycodestyle` to check for style issues in the Python code. The configuration for this job is as follows:

- Runs on the latest version of Ubuntu with Python versions 3.9 and 3.10.
- Runs `pycodestyle` to analyze Python files, ignoring specific error codes
  - E501: Line too long
  - W503: line break before binary operator (not enforced by PEP8)

### Linting CSS and JavaScript Code

The `lint-node` job is responsible for linting CSS and JavaScript code in the project. It uses `stylelint` for CSS and `eslint` for JavaScript. The configuration for this job is as follows:

- Runs on the latest version of Ubuntu with Node version 16.x.
- Finds unused CSS using a custom script (`list-unused-css.js`).
- Lints CSS and JavaScript code using the configured `stylelint` and `eslint`.

These commands ignore the following globs:

- `**/node_modules/**`
- `**/deps/**`
- `**/build/**`
- `**/3rd_party/**`
- `extension/`

These paths are auto-generated or auto-downloaded by various steps in the build process. Additionally, we ignore `extension` until we update it to have a better build process.

#### Stylelint Configuration

We use `stylelint` to lint our CSS code, with the following configuration:

- Ignores specific directories (listed above).
- Extends the `stylelint-config-standard` configuration.
- Uses the `postcss-scss` custom syntax for SCSS.
- Enables the `stylelint-scss` plugin to lint SCSS.

#### ESLint Configuration

We use `eslint` to lint our JavaScript code. This follows a standard configuration.

# Versioning

## Tracking Versions

Each module should include a `VERSION` file to specify the module's current version. This version is referenced in the module's setup configuration. Typically, this is done in the `setup.cfg` file as follows:

```cfg
# setup.cfg
[metadata]
name = Module name
version = file:VERSION
```

## Version Format

The version format is split into 2 pieces, the semantic version and the local version string separated by a `+`. The semantic version is primarily used for uploading to PyPI and resolving dependency conflicts. The local version string contains additional metadata about when the code was last modified and the commit it came from. The versions should follow the following format:

```sh
major.minor.patch+%Y.%m.%dT%H.%M.%S.%3NZ.abc123.branch.name
```

A example version string might look like this:

```sh
0.1.0+2024.12.16T16.42.38.637Z.abc123.branch.name
```

## Bumping Versions

The local version strings that contain metadata are automatically managed using a Git pre-commit hook. Before each commit is made, the appropriate `VERSION` is updated to reflect the current time and commit.

Bumping the semantic version is done manually.

## Setting Up the Pre-Commit Hook

To enable automatic version bumping, use the `install-pre-commit-hook` command provided in the `Makefile`. This command handles copying the pre-commit hook script into the appropriate location and making it executable. Run the following command:

```bash
make install-pre-commit-hook
```

With this setup, every commit will automatically update the version for you.

## Notes

- Ensure that `setup.cfg` properly references the `VERSION` file to avoid version mismatches.
- Avoid manually editing the `VERSION` file; rely on the pre-commit hook for consistency.

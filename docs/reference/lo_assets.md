# lo_assets Built Package Reference

This document explains how Learning Observer consumes built packages from [`ArgLab/lo_assets`](https://github.com/ArgLab/lo_assets), why this exists, and current operational caveats.

## Why `lo_assets` exists

Some frontend-related packages require an `npm` build step before they are usable. That build tooling is not always available on deployment servers, so we publish prebuilt artifacts to `lo_assets` and fetch them during setup/startup.

In `lo_assets`, each package typically has its own directory containing:

- versioned archives (for example, `package-name-v1.2.3.tar.gz`)
- a `package-name-current.tar.gz` pointer file (a plain-text file containing the current archive filename)

## Where this repository is referenced in Learning Observer

### 1) Python package install path (`Makefile`)

The top-level `Makefile` installs `lo_dash_react_components` by:

1. downloading `lo_dash_react_components-current.tar.gz` from `lo_assets`
2. reading the returned filename
3. installing that resolved tarball with `pip`

This is implemented in the `install` target and is currently specialized to LODRC.

### 2) Runtime frontend asset fetch (`remote_assets.py`)

`learning_observer.remote_assets.fetch_module_assets()` supports a generic pointer-file workflow for prebuilt frontend bundles (for example exported Next.js apps):

1. read a `*-current.tar.gz` pointer file from `lo_assets`
2. resolve it to a concrete archive name
3. download and extract the archive into a target module directory

This logic is used for modules that ship prebuilt frontend assets outside of the main repo.

## Package-specific notes

### LODRC (`lo_dash_react_components`)

- This is a Python package, so downloading and reinstalling is an acceptable update path.
- Current behavior is handled by the top-level `Makefile` install process.

### Portfolio Diff (`wo_portfolio_diff`)

- This is a Next.js-derived frontend bundle copied into `modules/wo_portfolio_diff/wo_portfolio_diff`.
- Current fetch logic can pull the bundle when assets are missing.
- Current behavior does **not** automatically refresh when a newer remote bundle exists and local assets are already present.

## Operational caveats

- Whenever a new package version is published in `lo_assets`, the `*-current.tar.gz` pointer file should also be updated to point to that new archive.
- Most consuming code paths intentionally resolve the `current` pointer rather than pinning a hard-coded version.
- In some cases, users may need to remove local assets and re-run setup/startup steps to force retrieval of the latest bundle.

## Future improvement (TODO)

A generic Learning Observer startup check should:

1. track the resolved remote archive version in a local state file
2. compare local version vs. current `*-current.tar.gz` pointer target
3. auto-refresh assets when the remote current version changes

This would eliminate manual remove-and-refetch workflows and make behavior consistent across modules.

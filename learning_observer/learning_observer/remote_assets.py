"""
learning_observer.remote_assets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utilities for downloading and installing prebuilt frontend asset bundles
(e.g. exported Next.js apps) that are hosted in a GitHub repository.

Intended use: LO module ``__init__.py`` files call :func:`fetch_module_assets`
from their startup checks to ensure their bundled frontend is present.

Typical repository layout assumed by the pointer-file convention::

    lo_assets/
      my_module/
        my_module-current.tar.gz   ← plain-text file containing the tarball name
        my_module-v1.2.3.tar.gz    ← the actual tarball
"""

import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request

# ---------------------------------------------------------------------------
# Default repository coordinates
# ---------------------------------------------------------------------------

_LO_ASSETS_REPO = 'ArgLab/lo_assets'
_LO_ASSETS_REF = 'main'


# ---------------------------------------------------------------------------
# Interactive / non-interactive prompts
# ---------------------------------------------------------------------------

def confirm(prompt, default_noninteractive):
    """
    Ask a yes/no question and return a boolean.

    Resolution order:
      1. *default_noninteractive* when stdin is not a TTY.
      2. An interactive prompt otherwise.

    Example usage in a module startup check::

        should_fetch = confirm(
            prompt='Download missing assets? (y/n) ',
            default_noninteractive=False,
        )
    """
    if not sys.stdin.isatty():
        return default_noninteractive

    return input(prompt).strip().lower() in {'y', 'yes'}


# ---------------------------------------------------------------------------
# Low-level network helpers
# ---------------------------------------------------------------------------

def read_url(url):
    """
    Fetch *url* and return its contents as a stripped string.
    """
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8').strip()


def download_file(url, destination):
    """
    Stream *url* to *destination*, avoiding loading the full response into
    memory.
    """
    with urllib.request.urlopen(url) as response, open(destination, 'wb') as output_file:
        shutil.copyfileobj(response, output_file)


# ---------------------------------------------------------------------------
# Archive helpers
# ---------------------------------------------------------------------------

def find_nextjs_root(extracted_dir):
    """
    Walk *extracted_dir* and return the shallowest path that looks like an
    exported Next.js app (contains both ``index.html`` and a ``_next/``
    directory).

    Raises ``ValueError`` if no such directory is found.
    """
    candidates = []
    for root, _, files in os.walk(extracted_dir):
        if 'index.html' in files and os.path.isdir(os.path.join(root, '_next')):
            candidates.append(root)

    if not candidates:
        raise ValueError(
            "Could not find an exported Next.js app inside the archive "
            "(expected index.html and _next/ in the same directory)."
        )

    return min(candidates, key=len)


def extract_assets_tarball(tar_path, target_dir):
    """
    Extract the Next.js app bundle at *tar_path* into *target_dir*.

    The archive may contain arbitrary wrapper directories; only the shallowest
    directory that looks like an exported Next.js app is copied to
    *target_dir*.  Any pre-existing *target_dir* is removed first.

    Raises ``ValueError`` (from :func:`find_nextjs_root`) if the archive does
    not contain a recognisable Next.js export.
    """
    with tempfile.TemporaryDirectory() as temp_extract_dir:
        with tarfile.open(tar_path, mode='r:gz') as archive:
            archive.extractall(temp_extract_dir)

        source_root = find_nextjs_root(temp_extract_dir)

        if os.path.isdir(target_dir):
            shutil.rmtree(target_dir)
        shutil.copytree(source_root, target_dir)


# ---------------------------------------------------------------------------
# High-level fetch interface
# ---------------------------------------------------------------------------

def fetch_module_assets(
    target_dir,
    pointer_file,
    assets_url=None,
    assets_repo=_LO_ASSETS_REPO,
    assets_ref=_LO_ASSETS_REF,
):
    """
    Download and install a prebuilt Next.js asset bundle for an LO module.

    Parameters
    ----------
    target_dir:
        Local directory where the extracted app should be placed.
    pointer_file:
        Path within *assets_repo* to a plain-text file whose content is the
        filename of the current tarball, e.g.
        ``'wo_portfolio_diff/wo_portfolio_diff-current.tar.gz'``.
        The tarball is assumed to live in the same directory as this file.
    assets_url:
        If supplied, skip pointer-file resolution and download this URL
        directly.  Useful for pinning a specific release or local testing.
    assets_repo:
        ``owner/repo`` slug on GitHub.  Defaults to the canonical LO assets
        repository.
    assets_ref:
        Branch, tag, or commit SHA to resolve *pointer_file* against.
        Defaults to ``'main'``.

    Raises
    ------
    urllib.error.URLError
        Network error while resolving the pointer file or downloading.
    ValueError
        The downloaded archive does not contain a recognisable Next.js export.
    OSError
        File-system error while writing or extracting the archive.
    tarfile.TarError
        The downloaded file is not a valid gzipped tar archive.
    """
    if assets_url is None:
        pointer_url = (
            f'https://raw.githubusercontent.com/{assets_repo}/{assets_ref}'
            f'/{pointer_file}'
        )
        resolved_name = read_url(pointer_url)
        pointer_dir = pointer_file.rsplit('/', 1)[0]
        assets_url = (
            f'https://raw.githubusercontent.com/{assets_repo}/{assets_ref}'
            f'/{pointer_dir}/{resolved_name}'
        )

    with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
        archive_path = tmp.name

    try:
        download_file(assets_url, archive_path)
        extract_assets_tarball(archive_path, target_dir)
    finally:
        os.unlink(archive_path)

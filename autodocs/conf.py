import os
import pathlib
import re
import shutil
import sphinx.util
import sys
import unicodedata
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Learning Observer'
copyright = '2020-2025, Bradley Erickson'
author = 'Bradley Erickson'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
sys.path.insert(0, os.path.abspath('../'))

extensions = [
    'autodoc2',
    'myst_parser',
]

autodoc2_packages = [
    '../learning_observer/learning_observer',
    '../modules/writing_observer/writing_observer'
]

autodoc2_output_dir = 'apidocs'
autodoc2_member_order = 'bysource'

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
    '.txt': 'markdown'
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

LOGGER = sphinx.util.logging.getLogger(__name__)


_MARKDOWN_IMAGE_PATTERN = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
_RST_IMAGE_PATTERNS = [
    re.compile(r'\.\.\s+image::\s+([^\s]+)'),
    re.compile(r'\.\.\s+figure::\s+([^\s]+)'),
]


def _extract_local_assets(text):
    """Return relative asset paths referenced in the provided README text."""

    asset_paths = set()
    for match in _MARKDOWN_IMAGE_PATTERN.findall(text):
        asset_paths.add(match)
    for pattern in _RST_IMAGE_PATTERNS:
        asset_paths.update(pattern.findall(text))

    filtered_assets = set()
    for raw_path in asset_paths:
        candidate = raw_path.strip()
        if not candidate:
            continue
        # Remove optional titles ("path "optional title"") and URL fragments
        candidate = candidate.split()[0]
        candidate = candidate.split('#', maxsplit=1)[0]
        candidate = candidate.split('?', maxsplit=1)[0]

        if candidate.startswith(('http://', 'https://', 'data:')):
            continue
        if candidate.startswith('#'):
            continue

        filtered_assets.add(candidate)

    return sorted(filtered_assets)


def _copy_module_assets(readme_path, destination_dir):
    """Copy image assets referenced by ``readme_path`` into ``destination_dir``."""

    module_dir = readme_path.parent.resolve()
    readme_text = readme_path.read_text(encoding='utf-8')
    asset_paths = _extract_local_assets(readme_text)
    for asset in asset_paths:
        relative_posix_path = pathlib.PurePosixPath(asset)
        if relative_posix_path.is_absolute():
            LOGGER.warning(
                "Skipping absolute image path %s referenced in %s", asset, readme_path
            )
            continue

        normalized_relative_path = pathlib.Path(*relative_posix_path.parts)
        source_path = (module_dir / normalized_relative_path).resolve(strict=False)

        try:
            source_path.relative_to(module_dir)
        except ValueError:
            LOGGER.warning(
                "Skipping image outside module directory: %s referenced in %s",
                asset,
                readme_path,
            )
            continue

        if not source_path.exists():
            LOGGER.warning(
                "Referenced image %s in %s was not found", asset, readme_path
            )
            continue

        destination_path = destination_dir / normalized_relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)


def _extract_readme_title(readme_path: pathlib.Path) -> str:
    """Return the first Markdown heading in ``readme_path``.

    Defaults to the parent directory name if no heading can be found.
    """

    try:
        for line in readme_path.read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if stripped.startswith('#'):
                title = stripped.lstrip('#').strip()
                if title:
                    return title
    except OSError as exc:  # pragma: no cover - filesystem error propagation
        LOGGER.warning("unable to read %s: %s", readme_path, exc)

    return readme_path.parent.name


def _slugify(text: str) -> str:
    """Convert ``text`` to a lowercase filename-safe slug."""

    normalized = unicodedata.normalize('NFKD', text)
    without_diacritics = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    slug = re.sub(r'[^a-z0-9]+', '-', without_diacritics.casefold()).strip('-')
    return slug or 'module'


def _copy_module_readmes(app):
    """Populate ``module_readmes`` with module README files and assets."""

    docs_root = pathlib.Path(__file__).parent.resolve()
    modules_root = docs_root.parent / 'modules'
    destination_root = docs_root / 'module_readmes'

    if not modules_root.exists():
        LOGGER.warning("modules directory %s was not found", modules_root)
        return

    if destination_root.exists():
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)

    readme_info = []
    for readme_path in modules_root.glob('*/README.md'):
        title = _extract_readme_title(readme_path)
        readme_info.append((title, readme_path))

    readme_info.sort(key=lambda item: item[0].casefold())

    for title, readme_path in readme_info:
        module_name = readme_path.parent.name
        slug = _slugify(title)
        module_destination = destination_root / f'{slug}--{module_name}'
        module_destination.mkdir(parents=True, exist_ok=True)
        destination_path = module_destination / "README.md"
        shutil.copy2(readme_path, destination_path)
        _copy_module_assets(readme_path, module_destination)


def setup(app):
    app.connect('builder-inited', _copy_module_readmes)

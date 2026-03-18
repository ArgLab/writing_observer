'''
Writing Observer Portfolio Diff

A writing observer module that shows the difference between the works of a student
'''

import json
import os
import re
import sys
import tarfile
import urllib.error

import learning_observer.prestartup
import learning_observer.settings
import learning_observer.remote_assets
from learning_observer.log_event import debug_log


NAME = 'Writing Observer - Portfolio Diff'

COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/wo_portfolio_diff/portfolio_diff/",
    "icon": {
        "type": "fas",
        "icon": "fa-play-circle"
    }
}]

NEXTJS_PAGES = [
    {'path': 'portfolio_diff/'}
]

_POINTER_FILE = 'portfolio_diff/portfolio_diff-current.tar.gz'


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _portfolio_diff_dir():
    return os.path.join(os.path.dirname(__file__), 'portfolio_diff')


def _runtime_config_path():
    return os.path.join(_portfolio_diff_dir(), 'runtime-config.js')


def _portfolio_diff_assets_present():
    portfolio_diff_dir = _portfolio_diff_dir()
    return (
        os.path.isdir(portfolio_diff_dir)
        and os.path.isfile(os.path.join(portfolio_diff_dir, 'index.html'))
        and os.path.isdir(os.path.join(portfolio_diff_dir, '_next'))
    )


# ---------------------------------------------------------------------------
# Asset fetching
# ---------------------------------------------------------------------------

def _fetch_portfolio_diff_assets():
    learning_observer.remote_assets.fetch_module_assets(
        target_dir=_portfolio_diff_dir(),
        pointer_file=_POINTER_FILE,
    )


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

def _prompt_to_fetch_assets():
    return learning_observer.remote_assets.confirm(
        prompt=(
            'Portfolio diff assets were not found. '
            'Download prebuilt assets from the LO assets repository now? (y/n) '
        ),
        default_noninteractive=False,
    )


def _prompt_to_write_runtime_config():
    return learning_observer.remote_assets.confirm(
        prompt=(
            'Would you like to write runtime-config.js '
            f'using current LO hostname/protocol settings `{_ws_origin_from_settings()}`?  (y/n) '
        ),
        default_noninteractive=True,
    )


# ---------------------------------------------------------------------------
# Runtime config
# ---------------------------------------------------------------------------

def _ws_origin_from_settings():
    protocol = learning_observer.settings.pmss_settings.protocol()
    hostname = learning_observer.settings.pmss_settings.hostname()
    ws_protocol = 'wss' if protocol == 'https' else 'ws'
    return f'{ws_protocol}://{hostname}'


def _runtime_config_contents(ws_origin):
    # json.dumps produces a properly-quoted JS string literal.
    return (
        'window.__PORTFOLIO_DIFF_CONFIG = {\n'
        f'  NEXT_PUBLIC_LO_WS_ORIGIN: {json.dumps(ws_origin)}\n'
        '};\n'
    )


def _write_runtime_config_from_settings():
    runtime_config_path = _runtime_config_path()
    os.makedirs(os.path.dirname(runtime_config_path), exist_ok=True)
    ws_origin = _ws_origin_from_settings()

    with open(runtime_config_path, 'w', encoding='utf-8') as f:
        f.write(_runtime_config_contents(ws_origin))

    debug_log(
        'Wrote wo_portfolio_diff runtime-config.js with '
        f'NEXT_PUBLIC_LO_WS_ORIGIN={ws_origin}.'
    )


# ---------------------------------------------------------------------------
# Startup checks
# ---------------------------------------------------------------------------

@learning_observer.prestartup.register_startup_check
def check_portfolio_diff_assets_exist():
    if _portfolio_diff_assets_present():
        return

    if _prompt_to_fetch_assets():
        try:
            _fetch_portfolio_diff_assets()
        except (urllib.error.URLError, OSError, tarfile.TarError, ValueError) as error:
            raise learning_observer.prestartup.StartupCheck(
                f"Could not automatically fetch wo_portfolio_diff assets. Details: {error}"
            ) from error

        if _prompt_to_write_runtime_config():
            try:
                _write_runtime_config_from_settings()
            except (OSError, AttributeError) as error:
                raise learning_observer.prestartup.StartupCheck(
                    f"Could not write wo_portfolio_diff runtime-config.js. Details: {error}"
                ) from error

        if _portfolio_diff_assets_present():
            debug_log('Downloaded and installed missing wo_portfolio_diff assets.')
            return

    raise learning_observer.prestartup.StartupCheck(
        "Could not find bundled portfolio diff assets at "
        f"`{_portfolio_diff_dir()}`.\n"
        "This dashboard expects a built frontend in "
        "`wo_portfolio_diff/portfolio_diff/`.\n"
        "Answer `y` to the interactive prompt on startup to fetch assets."
    )


@learning_observer.prestartup.register_startup_check
def check_runtime_config_server_override():
    runtime_config_path = _runtime_config_path()
    if not os.path.isfile(runtime_config_path):
        return

    with open(runtime_config_path, encoding='utf-8') as f:
        contents = f.read()

    if re.search(r'NEXT_PUBLIC_LO_WS_ORIGIN\s*:\s*null\b', contents):
        debug_log(
            "WARNING:: portfolio diff runtime-config.js sets "
            "NEXT_PUBLIC_LO_WS_ORIGIN to null. "
            "Set this value if you want the dashboard to point to a specific server."
        )

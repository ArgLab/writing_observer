'''
Writing Observer Portfolio Diff

A writing observer module that shows the difference between the works of a student
'''

import os
import re

import learning_observer.prestartup
from learning_observer.log_event import debug_log


# Name for the module
NAME = 'Writing Observer - Portfolio Diff'


'''
The Course Dashboards are used to populate the modules
on the home screen.

Note the icon uses Font Awesome v5
'''
COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/wo_portfolio_diff/portfolio_diff/",
    "icon": {
        "type": "fas",
        "icon": "fa-play-circle"
    }
}]

'''
Built NextJS pages we want to serve.
'''
NEXTJS_PAGES = [
    {'path': 'portfolio_diff/'}
]

def _portfolio_diff_dir():
    return os.path.join(os.path.dirname(__file__), 'portfolio_diff')


@learning_observer.prestartup.register_startup_check
def check_portfolio_diff_assets_exist():
    portfolio_diff_dir = _portfolio_diff_dir()
    if not os.path.isdir(portfolio_diff_dir):
        raise learning_observer.prestartup.StartupCheck(
            "Could not find bundled portfolio diff assets at "
            f"`{portfolio_diff_dir}`.\n"
            "This dashboard expects a built frontend in "
            "`wo_portfolio_diff/portfolio_diff/`.\n"
            "Rebuild and copy the frontend output into this module before starting."
        )


@learning_observer.prestartup.register_startup_check
def check_runtime_config_server_override():
    runtime_config_path = os.path.join(_portfolio_diff_dir(), 'runtime-config.js')
    if not os.path.isfile(runtime_config_path):
        return

    with open(runtime_config_path, encoding='utf-8') as runtime_config_file:
        runtime_config_contents = runtime_config_file.read()

    if re.search(r'NEXT_PUBLIC_LO_WS_ORIGIN\s*:\s*null\b', runtime_config_contents):
        debug_log(
            "WARNING:: portfolio diff runtime-config.js sets "
            "NEXT_PUBLIC_LO_WS_ORIGIN to null. "
            "Set this value if you want the dashboard to point to a specific server."
        )

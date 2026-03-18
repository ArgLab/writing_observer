'''
System Configuration
====================

This is just a wrapper to load out configuration YAML file from disk.

At some point, it might make sense to make this a thicker wrapper, so
we can have multiple configuration files with includes. As is, we have
credentials in the same place as module configuration, which is not
ideal.
'''

import argparse
import enum
import os.path
import sys

import yaml

import learning_observer.paths

import pmss

pmss_settings = None

# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportError("Please use fully-qualified imports")
    sys.exit(-1)


args = None
parser = None

def str_to_bool(arg):
    if isinstance(arg, bool):
        return arg
    if arg.lower() in ['true', '1']:
        return True
    if arg.lower() in ['false', '0']:
        return False
    raise argparse.ArgumentTypeError('Boolean like value expected.')


def _expand_ruleset_paths(ruleset_paths):
    if not ruleset_paths:
        return [learning_observer.paths.config_file()]

    expanded_paths = []
    for ruleset_path in ruleset_paths:
        if not os.path.exists(ruleset_path):
            raise FileNotFoundError(
                f"PMSS ruleset path not found: {ruleset_path}"
            )
        if os.path.isdir(ruleset_path):
            entries = [
                os.path.join(ruleset_path, entry)
                for entry in sorted(os.listdir(ruleset_path))
            ]
            expanded_paths.extend(
                entry for entry in entries if os.path.isfile(entry)
            )
        else:
            expanded_paths.append(ruleset_path)
    return expanded_paths


def _build_rulesets(ruleset_paths):
    rulesets = []
    for ruleset_path in _expand_ruleset_paths(ruleset_paths):
        if ruleset_path.endswith(('.yaml', '.yml')):
            rulesets.append(pmss.YAMLFileRuleset(filename=ruleset_path))
        elif ruleset_path.endswith('.pmss'):
            rulesets.append(pmss.PMSSFileRuleset(filename=ruleset_path))
        else:
            print(
                f"Skipping PMSS ruleset file {ruleset_path}; "
                "unsupported suffix."
            )
    return rulesets


def init_pmss_settings(ruleset_paths=None):
    global pmss_settings
    if pmss_settings is None:
        pmss_settings = pmss.init(
            prog=__name__,
            description="A system for monitoring",
            epilog="For more information, see PMSS documentation.",
            rulesets=_build_rulesets(ruleset_paths)
        )
    return pmss_settings


def parse_and_validate_arguments():
    '''
    Parse and validate command line arguments; for now, just the
    configuration file location.
    '''
    global args, parser
    # TODO use PMSS instead of argparse to track these settings
    parser = argparse.ArgumentParser(
        description='The Learning Observer',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--config-file',
        help='Specify an alternative configuration file',
        default=learning_observer.paths.config_file())

    parser.add_argument(
        '--pmss-rulesets',
        help='List of PMSS ruleset files or a directory of rulesets.',
        nargs='+',
        default=[learning_observer.paths.config_file()])

    parser.add_argument(
        '--watchdog',
        help='Run in watchdog mode. This will restart on file changes.',
        default=None)

    parser.add_argument(
        '--ipython-console',
        help='Instead of launching a web server, run a debug console.',
        action='store_true')

    parser.add_argument(
        '--ipython-kernel',
        help='Launch an `ipython` kernel',
        default=False, action='store_true')

    parser.add_argument(
        '--ipython-kernel-connection-file',
        help='Connection file passed into ipython-kernel. This is used by Juptyer Clients.',
        type=str)
    # TODO possibly include a --ipython-iopub-port param for monitoring purposes

    parser.add_argument(
        '--run-lo-application',
        help='Launce the Learning Observer application. This can be used with `--ipython-console` and `--ipython-kernel`.',
        default=True, nargs='?', const=True, type=str_to_bool)

    parser.add_argument(
        '--port',
        help='Which port to start the system on. Overrides any port listed in a configuration file.',
        type=int)

    args = parser.parse_args()

    if not os.path.exists(args.config_file):
        raise FileNotFoundError(
            "Configuration file not found: {config_file}\n"
            "\n"
            "Copy the example file into:\n"
            "{config_file}\n"
            "And then continue setup\n"
            "The command is probably:\n"
            "cp {sourcedir}/creds.yaml.example {dest}".format(
                sourcedir=os.path.dirname(os.path.abspath(__file__)),
                dest=args.config_file,
                config_file=args.config_file
            )
        )
    init_pmss_settings(args.pmss_rulesets)
    return args


# TODO we ought to refactor how this enum is built
# so the values are strings instead of integers
#
# DEV = Development, with full debugging
# DEPLOY = Running on a server, with good performance
# INTERACTIVE = Processing data offline
RUN_MODES = enum.Enum('RUN_MODES', 'DEV DEPLOY INTERACTIVE')
RUN_MODE = None

pmss.parser('run_mode', parent='string', choices=['dev', 'deploy', 'interactive'], transform=None)
pmss.register_field(
    name='run_mode',
    type='run_mode',
    description="Set which mode the server is running in.\n"\
                "`dev` for local development with full debugging\n"\
                "`deploy` for running on a server with better performance\n"\
                "`interactive` for processing data offline",
    required=True
)

settings = None


def load_settings(config):
    '''
    Load the settings file and return a dictionary of settings. Also:
    - Allow a stub data path
    - Select the run mode
    - Set up location of module repositories, if overridden in the config

    This is a wrapper around `yaml.safe_load()` so we can do some validation,
    error handling, and postprocessing.

    :param config: The configuration file to load, or a dictionary of settings
    :return: A dictionary of settings

    We can work from a dictionary rather than config file because we want to
    be able to use pieces of the Learning Observer in scripts and tests, where
    we don't need a full config.
    '''
    global settings

    # Ensure PMSS is initialized for callers that skip CLI parsing.
    # If CLI parsing already ran, the init call is a no-op.
    init_pmss_settings()

    if isinstance(config, str):
        with open(config, 'r') as f:
            settings = yaml.safe_load(f)
    elif isinstance(config, dict):
        settings = config
    else:
        raise AttributeError("Invalid settings file")

    # For testing and similar, we'd like to be able to have alternative data
    # paths
    if 'data_path' in settings:
        learning_observer.paths.override_data_path(settings['data_path'])

    # Development versus deployment. This is helpful for logging, verbose
    # output, etc.
    global RUN_MODE
    settings_run_mode = pmss_settings.run_mode(types=['config'])
    if settings_run_mode == 'dev':
        RUN_MODE = RUN_MODES.DEV
    elif settings_run_mode == 'deploy':
        RUN_MODE = RUN_MODES.DEPLOY
    elif settings_run_mode == 'interactive':
        RUN_MODE = RUN_MODES.INTERACTIVE
    else:
        raise ValueError("Configuration setting for run_mode must be either 'dev', 'deploy', or 'interactive'")

    if 'repos' in settings:
        for repo in settings['repos']:
            # In the future, we might allow dicts if we e.g. want more metadata
            if isinstance(settings['repos'][repo], str):
                learning_observer.paths.register_repo(repo, settings['repos'][repo])
            elif isinstance(settings['repos'][repo], dict):
                # HACK. We should figure out where to stick this. This does not belong in paths
                debug_working = settings['repos'][repo].get("debug_working", None)

                learning_observer.paths.register_repo(
                    repo,
                    settings['repos'][repo]['path'],
                    debug_working=debug_working
                )
            else:
                raise ValueError("settings.repos.{repo} should be a string or a dict. Please fix the settings file.".format(repo=repo))

    return settings


class SettingsException(Exception):
    pass


NOT_INITIALIZED_ERROR = \
    """Attempted to access Learning Observer settings before initializing
    them:
    * If you are writing test code, use `offline.init()` for a minimalist
    in-memory debug settings version.
    * If you are running in the main system, you probably have a bug with
    load / initialization order."""


def initialized():
    '''
    Check if we're initialized. If not, raise an exception
    '''
    if settings is None:
        raise SettingsException(
            NOT_INITIALIZED_ERROR
        )
    return True


# Not all of these are guaranteed to work on every branch of the codebase.
AVAILABLE_FEATURE_FLAGS = [
    'uvloop', 'watchdog', 'auth_headers_page', 'merkle', 'save_google_ajax', 'use_google_ajax',
    'google_routes', 'save_clean_ajax', 'use_clean_ajax',
    'canvas_routes', 'schoology_routes'
]


def feature_flag(flag):
    '''
    Return `None` if the given feature flag is disabled.

    Returns the value of the feature flag if it is enabled.

    Feature flags should look like an object in settings.
    `feature_flags: {uvloop, google_routes: false, watchdog: { foo: bar }}`
    Both `uvloop` and `watchdog` will be enabled, with `watchdog`
    returning additional content. `google_routes` and other
    other flags not listed will be disabled, `return None`.
    '''
    initialized()
    if flag not in AVAILABLE_FEATURE_FLAGS:
        raise ValueError(
            f"Unknown feature flag: {flag} "
            f"Available feature flags: {AVAILABLE_FEATURE_FLAGS}"
        )

    flags = settings.get('feature_flags', {})

    flag_setting = settings.get(
        'feature_flags', {}
    ).get(flag, None)

    # The feature flag is disabled if it is False or omitted
    if flag_setting is False:
        return None

    # Flag is available, but no further settings are included.
    if flag in flags and flag_setting is None:
        return True

    return flag_setting


def module_setting(module_name, setting=None, default=None):
    '''
    Return the settings for a specific module.

    Optionally, can be passed a specific setting.

    Returns `default` if no setting (or `None` if not set)
    '''
    initialized()
    return getattr(pmss_settings, setting)(types=['modules', module_name])

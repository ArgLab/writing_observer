import learning_observer.integrations.canvas
import learning_observer.integrations.google
import learning_observer.integrations.schoology
import learning_observer.prestartup
import learning_observer.settings

INTEGRATIONS = {}


@learning_observer.prestartup.register_startup_check
def verify_lti_feature_flags():
    '''
    Ensure LMS-specific LTI routes are enabled when related providers are configured.
    '''
    auth_settings = learning_observer.settings.settings.get('auth', {})
    lti_providers = auth_settings.get('lti', {})
    if not isinstance(lti_providers, dict):
        return

    configured_provider_names = [str(k).lower() for k in lti_providers.keys()]
    has_canvas_provider = any('canvas' in provider for provider in configured_provider_names)
    has_schoology_provider = any('schoology' in provider for provider in configured_provider_names)

    missing_flags = []
    if has_canvas_provider and not learning_observer.settings.feature_flag('canvas_routes'):
        missing_flags.append("feature_flags.canvas_routes")
    if has_schoology_provider and not learning_observer.settings.feature_flag('schoology_routes'):
        missing_flags.append("feature_flags.schoology_routes")

    if missing_flags:
        providers = []
        if has_canvas_provider:
            providers.append("Canvas")
        if has_schoology_provider:
            providers.append("Schoology")
        provider_text = " and ".join(providers)
        flags_text = "\n".join([f"  - {flag}" for flag in missing_flags])
        raise learning_observer.prestartup.StartupCheck(
            f"{provider_text} LTI provider(s) are configured, but required feature flags are disabled.\n"
            "Please enable the following in creds.yaml:\n"
            f"{flags_text}"
        )


def register_integrations(app):
    '''`routes.py:add_routes` calls this function to add the
    integrated services as routes on the system

    This initializes INTEGRATIONS for other functions to reference
    when making a call to course/rosters/assignments/etc.
    '''
    # TODO the setting checks should be calling into `pmss_settings` instead of `settings`
    if 'google_oauth' in learning_observer.settings.settings['auth']:
        INTEGRATIONS['google'] = learning_observer.integrations.google.register_endpoints(app)

    if 'lti' not in learning_observer.settings.settings['auth']:
        return

    # TODO we ought to check for what type of provider each lti setting needs
    # then only register the needed set of providers
    if any('schoology' in k for k in learning_observer.settings.settings['auth']['lti']):
        INTEGRATIONS['schoology'] = learning_observer.integrations.schoology.register_endpoints(app)

    # TODO we ought to fetch the following information with PMSS
    canvas_providers = [k for k in learning_observer.settings.settings['auth']['lti'].keys() if 'canvas' in k]
    for provider in canvas_providers:
        provider_endpoint_registrar = learning_observer.integrations.canvas.setup_canvas_provider(provider)
        # TODO check that provider doesn't already exist and is trying to be overwritten
        INTEGRATIONS[provider] = provider_endpoint_registrar(app)

import learning_observer.integrations.canvas
import learning_observer.integrations.google
import learning_observer.integrations.schoology
import learning_observer.settings

INTEGRATIONS = {}


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

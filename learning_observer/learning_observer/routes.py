'''
Map URLs to functions which handle them.
'''

import getpass
import os
import secrets
import sys

import aiohttp
import aiohttp.web

import gitserve.aio_gitserve

import aiohttp_wsgi

import learning_observer.admin as admin
import learning_observer.auth
import learning_observer.auth.http_basic
import learning_observer.client_config
import learning_observer.filesystem_state
import learning_observer.impersonate
import learning_observer.incoming_student_event as incoming_student_event
import learning_observer.dashboard
import learning_observer.integrations
import learning_observer.rosters as rosters
import learning_observer.module_loader

import learning_observer.paths as paths
import learning_observer.settings as settings

from learning_observer.log_event import debug_log, startup_state

from learning_observer.utility_handlers import *


def add_routes(app):
    '''
    Massive routine to set up all static routes.

    This should be broken out into routines for each group of routes,
    or handled as a data file, or similar.
    '''
    # Allow debugging of memory leaks.  Helpful, but this is a massive
    # resource hog. Don't accidentally turn this on in prod :)
    if 'tracemalloc' in settings.settings['config'].get("debug", []):
        import tracemalloc
        tracemalloc.start(25)

        def tracemalloc_handler(request):
            '''
            Handler to show tracemalloc stats.
            '''
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            top_hundred = "\n".join((str(t) for t in top_stats[:100]))
            top_stats = snapshot.statistics('traceback')
            top_one = "\n".join((str(t) for t in top_stats[0].traceback.format()))
            return aiohttp.web.Response(text=top_one + "\n\n\n" + top_hundred)

        app.add_routes([
            aiohttp.web.get('/debug/tracemalloc/', tracemalloc_handler),
        ])

    register_dashboard_api(app)
    register_static_routes(app)
    register_incoming_event_views(app)
    register_debug_routes(app)
    learning_observer.integrations.register_integrations(app)

    app.add_routes([
        aiohttp.web.get(
            '/webapi/courselist/',
            rosters.courselist_api),
        aiohttp.web.get(
            '/webapi/course/{course_id}',
            rosters.course_api),
        aiohttp.web.get(
            '/webapi/courseroster/{course_id}',
            rosters.courseroster_api),
        aiohttp.web.get(
            '/webapi/courseassignments/{course_id}',
            rosters.courseassignments_api),
    ])

    register_auth_webapp_views(app)

    # General purpose status page:
    # - List URLs
    # - Show system resources
    # Etc.
    app.add_routes([
        aiohttp.web.get('/admin/status', handler=admin.system_status)
    ])

    # This might look scary, but it's innocous. There are server-side
    # configuration options which the client needs to know about. This
    # gives those. At the very least, we want to be able to toggle the
    # client-side up between running with a real server and a dummy static
    # server, but in the future, we might want to include things like URIs
    # for different services the client can talk to and similar.
    #
    # This URI should **not** be the same as the filename. We have two
    # files, config.json is loaded if no server is running (dummy mode), and
    # this is overridden by the live server.
    app.add_routes([
        aiohttp.web.get(
            '/config.json',
            learning_observer.client_config.client_config_handler
        ),
        aiohttp.web.get(
            '/startup-info',
            learning_observer.auth.admin(json_response_handler(startup_state))
        ),
        aiohttp.web.get(
            '/filesystem-state',
            learning_observer.auth.admin(learning_observer.filesystem_state.filesystem_state_handler)
        )
    ])

    # We'd like to be able to have the root page themeable, for
    # non-ETS deployments. This is a quick-and-dirty way to override
    # the main page.
    root_file = settings.settings.get("theme", {}).get("root_file", "webapp.html")
    app.add_routes([
        aiohttp.web.get('/', static_file_handler(paths.static(root_file))),
    ])

    # E.g. We have an alias of /static/common to /common
    # We place useful things modules can use, such as e.g. our logger
    app.add_routes([
        aiohttp.web.get('/common/{filename}', static_directory_handler(paths.static("common"))),
    ])

    register_extra_views(app)
    register_nextjs_routes(app)

    # Allow AJAX calls.  Right now, the function receives a `request`
    # object. This should be cleaned in some way.
    ajax = learning_observer.module_loader.ajax()
    for module in ajax:
        for call in ajax[module]:
            path = "/ajax/{module}/{call}".format(module=module, call=call)
            debug_log("Adding AJAX path", path)
            app.add_routes([
                aiohttp.web.get(
                    path,
                    lambda x: aiohttp.web.json_response(ajax[module][call](x))
                )
            ])

    # We route the repos last, since we override some of the routes
    # above (esp. 3rd party libraries and media)
    repos = learning_observer.module_loader.static_repos()
    register_repo_routes(app, repos)

    # Allow users to mask themselves as other users
    register_impersonation_routes(app)

    # This is called last since we don't want wsgi routes overriding
    # our normal routes. We may change this design decision if we do
    # want to provide that option in the future, but as we're prototyping
    # and figuring stuff out, this feels safest to put last.
    register_wsgi_routes(app)


def register_debug_routes(app):
    '''
    Handy-dandy information views, useful for debugging and development.
    '''
    if settings.feature_flag("auth_headers_page"):
        app.add_routes([
            aiohttp.web.get(
                '/admin/headers',
                learning_observer.auth.social_sso.show_me_my_auth_headers
            )
        ])


def register_incoming_event_views(app):
    '''
    Register views for incoming events. We have a websocket
    connection for each incoming event. The websocket connection
    is a long-lived connection, and is used to receive events
    from the client.

    We supported AJAX calls before, but we've since moved to
    websockets, and the AJAX may be disabled since it's not
    tested. We'll keep the code around for now, since it's
    useful for debugging and in the future, lower-velocity
    events.
    '''
    # Handle web sockets event requests, incoming and outgoing
    app.add_routes([
        aiohttp.web.get(
            '/wsapi/in/',
            incoming_student_event.incoming_websocket_handler)
    ])


def register_dashboard_api(app):
    '''
    Register the dashboard API views.

    We are moving from per-student and per-course dashboard to a
    more general-purpose API. This is TBD.
    '''
    app.add_routes([
        aiohttp.web.get(
            '/wsapi/dashboard',
            learning_observer.dashboard.websocket_dashboard_view),
        aiohttp.web.get(
            '/wsapi/communication_protocol',
            learning_observer.dashboard.websocket_dashboard_handler
        ),
        aiohttp.web.get(
            '/webapi/course_dashboards',
            ajax_handler_wrapper(learning_observer.module_loader.course_dashboards)),
        aiohttp.web.get(
            '/webapi/student_dashboards',
            ajax_handler_wrapper(learning_observer.module_loader.student_dashboards))
    ])

    app.add_routes([
        aiohttp.web.get(
            '/wsapi/generic_dashboard',
            learning_observer.dashboard.generic_dashboard)
    ])


def register_auth_webapp_views(app):
    '''
    Register the views for the auth module and user info
    '''
    # Generic web-appy things
    app.add_routes([
        aiohttp.web.get(
            '/auth/logout',
            handler=learning_observer.auth.logout_handler),
        aiohttp.web.get(
            '/auth/userinfo',
            handler=learning_observer.auth.user_info_handler)
    ])

    if 'google_oauth' in settings.settings['auth']:
        debug_log("Running with Google authentication")
        app.add_routes([
            aiohttp.web.get(
                '/auth/login/{provider:google}',
                handler=learning_observer.auth.social_handler),
        ])

    # TODO We ought to use pmss here, though at this time it is easier
    # to check if a key exists this way
    if 'lti' in settings.settings['auth']:
        debug_log("Running with LTI authentication")
        # TODO build provider syntax based on available providers
        app.add_routes([
            aiohttp.web.post(
                '/lti/{provider}/login',
                handler=learning_observer.auth.handle_oidc_authorize),
            aiohttp.web.get(
                '/lti/{provider}/login',
                handler=learning_observer.auth.handle_oidc_authorize),
            aiohttp.web.post(
                '/lti/{provider}/launch',
                handler=learning_observer.auth.handle_oidc_launch),
            aiohttp.web.get(
                '/auth/login/lti',
                learning_observer.auth.check_oidc_login)
        ])

    if 'password_file' in settings.settings['auth']:
        debug_log("Running with password authentication")
        if not os.path.exists(settings.settings['auth']['password_file']):
            print("Configured to run with password file,"
                  "but no password file exists")
            print()
            print("Please either:")
            print("* Remove auth/password_file from the settings file")
            print("* Create a file {fn} with lo_passwd.py".format(
                fn=settings.settings['auth']['password_file']
            ))
            print("Typically:")
            print("{python_src} scripts/lo_passwd.py "
                  "--username {username} --password {password} "
                  "--filename learning_observer/{fn}".format(
                      python_src=paths.PYTHON_EXECUTABLE,
                      username=getpass.getuser(),
                      password=secrets.token_urlsafe(16),
                      fn=settings.settings['auth']['password_file']
                  ))
            sys.exit(-1)
        app.add_routes([
            aiohttp.web.post(
                '/auth/login/password',
                learning_observer.auth.password_auth(
                    settings.settings['auth']['password_file'])
            )])

    # If we want to support multiple modes of authentication, including
    # http-basic, we can configure a URL in nginx which will require
    # http basic auth, which is used to log in, and then redirects back
    # home.
    if learning_observer.auth.http_basic.http_auth_page_enabled():
        # If we don't have a password file, we shouldn't have an auth page.
        # At the very least, the user should explicitly set it to `null`
        # if they are planning on using nginx for auth
        debug_log("Enabling http basic auth page")
        auth_file = settings.settings['auth']['http_basic']["password_file"]
        app.add_routes([
            aiohttp.web.get(
                '/auth/login/http-basic',
                learning_observer.auth.http_basic.http_basic_auth(
                    filename=auth_file,
                    response=lambda:aiohttp.web.HTTPFound(location="/")
                )
            )
        ])
    app.add_routes([
        aiohttp.web.get(
            '/auth/default-avatar.svg',
            learning_observer.auth.handlers.serve_user_icon)
    ])


def register_static_routes(app):
    '''
    Register static routes routes for the webapp, especially 3rd party
    libraries.

    This serves static files from the static directories. It overrides the
    paths in repos. Most of these files are downloaded from the internet,
    rather than being kept in the codebase.
    '''
    # Serve static files
    app.add_routes([
        aiohttp.web.get(
            '/favicon.ico',
            static_file_handler(paths.static("favicon.ico"))),
        aiohttp.web.get(
            '/static/{filename}',
            static_directory_handler(paths.static())),
        aiohttp.web.get(
            '/static/modules/{filename}',
            static_directory_handler(paths.static("modules"))),
        # TODO: Make consistent. 3rdparty versus 3rd_party and maybe clean up URLs.
        aiohttp.web.get(
            r'/static/repos/{module:[^{}/]+}/{repo:[^{}/]+}/{branch:[^{}/]+}/3rdparty/{filename:[^{}]+}',
            static_directory_handler(paths.static("3rd_party"))),
        aiohttp.web.get(
            '/static/3rd_party/{filename}',\
            static_directory_handler(paths.static("3rd_party"))),
        aiohttp.web.get(
            '/static/3rd_party/css/{filename}',\
            static_directory_handler(paths.static("3rd_party/css"))),
        aiohttp.web.get(
            '/static/3rd_party/webfonts/{filename}',\
            static_directory_handler(paths.static("3rd_party/webfonts"))),
        aiohttp.web.get(
            '/static/media/{filename}',
            static_directory_handler(paths.static("media"))),
        aiohttp.web.get(
            '/static/media/avatar/{filename}',
            static_directory_handler(paths.static("media/hubspot_persona_images/"))),
    ])


def repo_url(module, repo, branch="master", path="index.html"):
    '''
    Return a URL for a file in a repo.
    '''
    return "/static/repos/{module}/{repo}/{branch}/{path}".format(
        module=module,
        repo=repo,
        branch=branch,
        path=path
    )


def register_repo_routes(app, repos):
    '''
    Register routes for all repos.

    An example repo is:

    {
        'url': 'https://github.com/ETS-Next-Gen/writing_observer.git',  // URL to the repo; downloaded if not already here
        'prefix': 'modules/writing_observer/writing_observer/static',   // Path in repo to serve static files from
        'module': 'wobserver',                                          // Module name to use in the static path

        'whitelist': ['master'],                                        // Optional: List of branches to serve static files from; currently ignored
        'working_tree': True,                                           // Optional: Allow working branches to be served
        'bare': False,                                                  // Optional: Serve from a bare repo
        'path': '/home/ubuntu/writing_observer'                         // Optional: Path to the repo
    }

    Most of the optional parameters should *not* be used in production. They are here
    for testing and development, especially of new dashboard modules. If needed in production,
    paths can also be set in the settings file.
    '''
    for reponame in repos:
        gitrepo = repos[reponame]
        # Check the keys in the repo dictionary are valid
        # We can add more keys in the future. E.g. we might want to have comments
        # and similar human-friendly metadata.
        for key in gitrepo:
            if key not in ['url', 'prefix', 'module', 'whitelist', 'working_tree', 'bare', 'path']:
                raise ValueError("Unknown key in gitrepo: {}".format(key))
        for key in ['url', 'prefix', 'module']:
            if key not in gitrepo:
                raise ValueError("Missing key in gitrepo: {}".format(key))
        # Check the URL is valid
        # We might want to support a broader range of URLs in the future.
        if not gitrepo['url'].startswith('http://') and not gitrepo['url'].startswith('https://') and not gitrepo['url'].startswith('git@'):
            raise ValueError("Invalid URL: {}".format(gitrepo['url']))

        giturl = r'/static/repos/' + gitrepo['module'] + '/' + reponame + '/{branch:[^{}/]+}/{filename:[^{}]+}'

        debug_log(f"Module {reponame} is hosting {gitrepo} at {giturl}")

        # If the working tree is set in the repo, we can serve from the working tree
        # This can be overridden by the settings file, in either direction
        working_tree = gitrepo.get('working_tree', False)
        working_tree_in_settings = paths.repo_debug_working_hack(reponame)  # Ignore the branch; serve from working tree
        if working_tree_in_settings is not None:
            print("Using working tree:", working_tree_in_settings)
            working_tree = working_tree_in_settings

        bare = gitrepo.get("bare", True)
        if working_tree:
            debug_log("Serving from working tree; overriding the bare repo setting")
            debug_log(f"Settings are inconsistent: working_tree: {working_tree} and bare: {bare}")
            bare = False

        print("Bare", bare)
        print("working_tree", working_tree)

        app.add_routes([
            aiohttp.web.get(
                giturl,
                handler=gitserve.aio_gitserve.git_handler_wrapper(
                    paths.repo(reponame),
                    cookie_prefix="SHA_" + reponame,
                    prefix=repos[reponame].get("prefix", None),
                    bare=bare,
                    working_tree_dev=working_tree)
            )
        ])


HTTP_METHOD_MAPPING = {
    'GET': aiohttp.web.get,
    'POST': aiohttp.web.post
}


def register_extra_views(app):
    # Add extra views as json responses
    extra_views = learning_observer.module_loader.extra_views()
    views = []
    for view in extra_views:
        if 'static_json' in view:
            views.append(aiohttp.web.get(
                f'/views/{view["module"]}/{view["suburl"]}/',
                lambda request, data=view['static_json']: aiohttp.web.json_response(data)
            ))
        elif 'method' in view and 'handler' in view:
            views.append(HTTP_METHOD_MAPPING[view['method']](
                f'/views/{view["module"]}/{view["suburl"]}/',
                view['handler']
            ))
        else:
            debug_log(f'The provided view did not register properly: {view}')
    app.add_routes(views)


def create_nextjs_handler(path):
    async def _nextjs_handler(request):
        sub_url = request.match_info.get('tail')
        if sub_url is None:
            return aiohttp.web.FileResponse(os.path.join(path, 'index.html'))
        # TODO will this handle multi-layered sub-urls? /foo/bar
        return aiohttp.web.FileResponse(os.path.join(path, f'{sub_url}.html'))
    return _nextjs_handler


def register_nextjs_routes(app):
    '''Add nextjs pages.

    Nextjs compresses all of the css/js into a static directory.
    We expose both the inital path and the static directory.
    '''
    for page in learning_observer.module_loader.nextjs_pages():
        full_path = os.path.join(page['_BASE_PATH'], page['path'])
        page_path = os.path.join(f"/{page['_COMPONENT']}", page['path'])
        static_path = f'/_next{page_path}_next/static/'
        app.router.add_static(static_path, os.path.join(full_path, '_next', 'static'))
        app.router.add_get(page_path, create_nextjs_handler(full_path))
        # The tail path handles suburls
        tail_path = page_path + '{tail:.*}'
        app.router.add_get(tail_path, create_nextjs_handler(full_path))


def register_wsgi_routes(app):
    '''
    This is primarily for `dash` integration, and is unsupported for
    other uses.
    '''
    for plugin in learning_observer.module_loader.wsgi():
        wsgi_app = plugin['APP']
        # This is a nice design pattern to adopt more broadly
        if callable(wsgi_app):
            wsgi_app = wsgi_app()
        wsgi_url_patterns = plugin.get("URL_PATTERNS", None)

        # We want to support patterns being a string, a list,
        # or a function. This is (relatively untested) code to
        # do that.
        if wsgi_url_patterns is None:
            print("Warning! No WSGI URL patterns. This should")
            print("only be used for prototyping on dev machines")
            wsgi_url_patterns = "/{path_info:.*}"
        if callable(wsgi_url_patterns):
            wsgi_url_patterns = wsgi_url_patterns()
        # We would like to support async, but for now, the whole
        # routing setup isn't async, so that's for later.
        #
        # if inspect.isawaitable(wsgi_url_patterns):
        #    wsgi_url_patterns = await wsgi_url_patterns
        if isinstance(wsgi_url_patterns, str):
            wsgi_url_patterns = [wsgi_url_patterns]

        wsgi_handler = learning_observer.auth.teacher(aiohttp_wsgi.WSGIHandler(wsgi_app.server))
        for pattern in wsgi_url_patterns:
            app.router.add_route("*", pattern, wsgi_handler)


def register_impersonation_routes(app):
    app.add_routes([
        aiohttp.web.get(
            '/start-impersonation/{user_id}',
            learning_observer.impersonate.start_impersonation
        ),
        aiohttp.web.get(
            '/stop-impersonation',
            learning_observer.impersonate.stop_impersonation
        )
    ])

'''
Import analytics modules

This runs _after_ `paths` and `settings`, since `settings` calls
`learning_observer.paths.register_repo`, which we use here.

Ideally, this would be more modular and run without a settings file
too. We'd like to use this from utility scripts.
'''


import collections
import copy
import os.path
import pmss
import sys

import pkg_resources

import gitserve.gitaccess

import learning_observer.paths
import learning_observer.settings

from learning_observer.log_event import debug_log
import learning_observer.communication_protocol.integration
import learning_observer.queries
import learning_observer.stream_analytics.helpers as helpers


pmss.parser('clone_module_git_repos', parent='string', choices=['prompt', 'y', 'n'], transform=None)
pmss.register_field(
    name='clone_module_git_repos',
    type='clone_module_git_repos',
    description='Determine if we should fetch git repos for installed '\
        'modules. If None, prompt user instead.',
    default='prompt'
)

# This is set to true after we've scanned and loaded modules
LOADED = False

COURSE_AGGREGATORS = collections.OrderedDict()
EXECUTION_DAGS = {}
REDUCERS = []
THIRD_PARTY = {}
STATIC_REPOS = {}
STUDENT_DASHBOARDS = []
COURSE_DASHBOARDS = []
EXTRA_VIEWS = []

# Additional calls, primarily for metadata
AJAX = {}

WSGI = []
DASH_PAGES = {}
NEXTJS_PAGES = []


def extra_views():
    '''
    We used to just have dashboards rendered as views as a hack. This
    will use the same API, provide backwards-compatibility, but also
    act as a place for things which aren't dashboards. Modules ought
    to be able to define random views.
    '''
    load_modules()
    return EXTRA_VIEWS


def student_dashboards():
    '''
    URLs of per-student views
    '''
    load_modules()
    return STUDENT_DASHBOARDS


def course_dashboards():
    '''
    URLs of per-course views
    '''
    load_modules()
    return COURSE_DASHBOARDS


def course_aggregators():
    '''
    Return a dictionary of all modules the system can render.
    TODO: Rename to teacher aggregators or similar.
    '''
    load_modules()
    return COURSE_AGGREGATORS


def execution_dags():
    '''
    Return a dictionary of all named queries the system can make.
    '''
    load_modules()
    return EXECUTION_DAGS


def reducers():
    '''
    Return a list of all event processors / reducers. Note that
    we can have multiple reducers for the same event type.
    '''
    load_modules()
    return REDUCERS


def third_party():
    '''
    Return a list of modules to download from 3rd party repos.

    We should eventually:

    - Handle version conflicts more gracefully (e.g. by allowing
      hashes of multiple compatible versions)
    - Support serving static files from e.g. S3 or similar
      services rather than our own server (e.g. by filling in
      references in modules where needed, or through settings in
      config.json)
    - Serving from CDNs (for deploys where we don't mind leaking
      user data; e.g. development)

    ... but not today.

    We don't want these modules committed to our repo due to size.
    '''
    load_modules()
    return THIRD_PARTY


def static_repos():
    '''
    We can serve static files for each module. These are served
    straight from `git`. In the future, we'd like to cache this.

    There's a little bit of complexity and nuance in how we'd
    like to manage branches.

    In deployment / operational settings:

    - We'll want to be careful about WHICH branch and commit we
    serve. We don't want students, teachers, or search engines
    navigating all versions willy nilly.
    - This is primarily a research platform. In research settings,
    we usually DO want to allow users to go to different versions.
    This is helpful for research replicability ("what version did
    Subject 42 see?"), for the social practice of research (e.g.
    show a collaborator a prototype, while using IRB-approved
    versions for coglabs), for experiments (e.g. show different
    versions to different students), etc.

    For now, this is set up around the *research* use-case: Being able
    to run coglabs, small pilots, and similar, used in controlled
    settings, without confidential items in repos.

    Note that since this is all open-source, hosting static files from
    a repo is *typically* *not* a security issue. It can be a usability
    issue, though (e.g. if users find an outdated link via a search
    engine).

    (Of course, YMMV. If you're hosting test items in a repo, then you
    want to be very careful about security)
    '''
    load_modules()
    return STATIC_REPOS


def ajax():
    '''
    Return a dictionary of all AJAX handlers.
    '''
    load_modules()
    return AJAX


def wsgi():
    load_modules()
    return WSGI


def dash_pages():
    load_modules()
    return DASH_PAGES


def nextjs_pages():
    load_modules()
    return NEXTJS_PAGES


def load_modules():
    '''
    Iterate through entry points to:
    - Find all Learning Observer modules installed
    - Load course_aggregators from each module
    - Load reducers from each module

    This is called before we ask for something from modules, but it
    only changes state on startup (for now -- we might revist later
    if we want to be more dynamic).
    '''
    # pylint: disable=W0603
    global LOADED
    if LOADED:
        return

    # Iterate through Learning Observer modules
    for entrypoint in pkg_resources.iter_entry_points("lo_modules"):
        load_module_from_entrypoint(entrypoint)
    LOADED = True


def validate_module(module):
    '''
    Check that a module has the required components.

    We should eventually do more validation here, once we have
    figured out what we want to validate.
    '''
    if not hasattr(module, "NAME"):
        raise ValueError(
            f"Module {module} does not have a NAME attribute "
            "Please give your module a short, human-friendly name "
            "Spaces, etc. are okay"
        )


DEFAULT_STUDENT_SCOPE = helpers.Scope([helpers.KeyField.STUDENT])


def format_function(f):
    '''
    Returns a nice, fully-qualified name for a function
    '''
    return f"{f.__module__}.{f.__name__}"


def add_reducer(reducer, string_id=None):
    '''
    We add a reducer. In actual operation, this should only happen once, on
    module load. We'd like to be able to dynamic load and reload reducers in
    interactive programming, so we offer the option of a `string_id`
    '''
    global REDUCERS
    # TODO this is filtering the reducers on a specific string_id.
    # we ought to look for the matching reducer and replace it if it exists.
    if string_id is not None:
        REDUCERS = [r for r in REDUCERS if r.get("string_id", None) != string_id]
    REDUCERS.append(reducer)
    return REDUCERS


def remove_reducer(reducer_id):
    '''Remove a reducer from the available reducers
    '''
    global REDUCERS
    REDUCERS = [r for r in REDUCERS if r['id'] != reducer_id]


def load_reducers(component_name, module):
    '''
    Load reducers from a module.

    We clean up the reducer by removing any keys that we don't
    and need, adding defaults for any missing keys.
    '''
    # Load any state reducers / event processors
    if hasattr(module, "REDUCERS"):
        debug_log(f"Loading reducers from {component_name}")
        for reducer in module.REDUCERS:
            cleaned_reducer = {
                "context": reducer['context'],
                "function": reducer['function'],  # Primary ID
                "scope": reducer.get('scope', DEFAULT_STUDENT_SCOPE),
                "default": reducer.get('default', {}),
                "module": module,
                "id": f"{module.__name__.replace('.module', '')}.{reducer['function'].__name__}"
            }

            # Here's the deal: Our primary ID is the function itself, and our
            # code should rely on that. It gives us type safety. However, it's
            # convenient to be able to reference these things more easily when
            # developing interactively. This gives a string ID. We might eliminate
            # this later, since it's possible to recompute to the string
            # representation of the function. But it's convenient for now.
            if learning_observer.settings.RUN_MODE == learning_observer.settings.RUN_MODES.INTERACTIVE:
                cleaned_reducer['string_id'] = format_function(reducer['function'])

            debug_log(f"Loading reducer: {cleaned_reducer}")
            REDUCERS.append(cleaned_reducer)
    else:
        debug_log(f"Component {component_name} has no reducers")


def load_course_aggregators(component_name, module):
    '''
    Load course aggregators from a module.

    We clean up the course aggregator by removing any keys that we
    don't need, adding defaults for any missing keys.
    '''
    if hasattr(module, "COURSE_AGGREGATORS"):
        debug_log(f"Loading course aggregators from {component_name}")
        for course_aggregator in module.COURSE_AGGREGATORS:
            aggregator_id = "{module}.{submodule}".format(
                module=component_name,
                submodule=course_aggregator
            )

            cleaned_aggregator = {
                "long_id": aggregator_id,
                "short_id": course_aggregator,
                "module": module
            }
            cleaned_aggregator.update(module.COURSE_AGGREGATORS[course_aggregator])

            COURSE_AGGREGATORS[aggregator_id] = cleaned_aggregator

            debug_log(f"Loaded course aggregator: {cleaned_aggregator}")
    else:
        debug_log(f"Component {component_name} has no course aggregators")


def load_execution_dags(component_name, module):
    '''
    Load execution DAG from a module.
    '''
    if hasattr(module, "EXECUTION_DAG"):
        debug_log(f"Loading execution DAG from {component_name}")
        # set up a nested module to add our queries to
        queries = learning_observer.queries.NestedQuery()
        learning_observer.communication_protocol.integration.add_exports_to_module(module.EXECUTION_DAG, queries)
        # set the nested module to the `learning_observer.queries.component_name` namespace
        setattr(learning_observer.queries, component_name, queries)

        # clean queries
        cleaned_query = {'module': component_name}
        cleaned_query.update(module.EXECUTION_DAG)
        if component_name in EXECUTION_DAGS:
            raise KeyError(f'Execution DAG already exists for {component_name}')
        EXECUTION_DAGS[component_name] = cleaned_query
    else:
        debug_log(f"Component {component_name} has no execution DAG")


def load_ajax(component_name, module):
    '''
    Load AJAX handlers from a module. This is API is TBD.
    '''
    if hasattr(module, "AJAX"):
        debug_log(f"Loading AJAX handlers from {component_name}")
        AJAX[component_name] = module.AJAX
    else:
        debug_log(f"Component {component_name} has no extra AJAX handlers")


def load_dashboards(component_name, module):
    '''
    Load dashboards from a module.

    For now, these are just static URLs to the dashboards. These can
    either be per-student or per-course. We might want to add more
    types later, or somehow organize these better.

    These should have more metadata at some point. Organization of this
    is TBD.
    '''
    dashboards = False
    if hasattr(module, "COURSE_DASHBOARDS"):
        debug_log(f"Loading course dashboards from {component_name}")
        COURSE_DASHBOARDS.extend(module.COURSE_DASHBOARDS)
        dashboards = True

    if hasattr(module, "STUDENT_DASHBOARDS"):
        debug_log(f"Loading student dashboards from {component_name}")
        STUDENT_DASHBOARDS.extend(module.COURSE_DASHBOARDS)
        dashboards = True

    if not dashboards:
        debug_log(f"Component {component_name} has no dashboards")


def load_extra_views(component_name, module):
    '''
    '''
    extras = False
    if hasattr(module, 'EXTRA_VIEWS'):
        debug_log(f'Loading extra views from {component_name}')
        EXTRA_VIEWS.extend([m | {'module': component_name} for m in module.EXTRA_VIEWS])
        extras = True

    if not extras:
        debug_log(f'Component {component_name} has no extra views')


def register_3rd_party(component_name, module):
    '''
    Register 3rd party components the module needs.

    These will be downloaded and installed onto the server,
    and then the module will be able to use them.

    These are verified by SHA hashes.

    There's a lot to think through in terms of absolute paths,
    conflicts, etc. perhaps another time.
    '''
    if hasattr(module, "THIRD_PARTY"):
        debug_log(f"Loading third party components from {component_name}")
        for library_filename in module.THIRD_PARTY:
            # If another module already wants this library, confirm
            # it's under the same hash
            if library_filename in THIRD_PARTY:
                if THIRD_PARTY[library_filename]['hash'] != module.THIRD_PARTY[library_filename]['hash']:
                    raise RuntimeError(
                        "Version Conflict in 3rd party libs\n"
                        "Component {} has a different hash for {} "
                        "than previous component.\n"
                        "{} vs {}".format(
                            component_name,
                            library_filename,
                            THIRD_PARTY[library_filename],
                            module.THIRD_PARTY[library_filename]
                        )
                    )
            else:
                THIRD_PARTY[library_filename] = {
                    'urls': [],
                    'hash': module.THIRD_PARTY[library_filename].get('hash', None),
                    'users': []
                }
            THIRD_PARTY[library_filename]['users'].append(module.NAME)
            THIRD_PARTY[library_filename]['urls'].append(
                module.THIRD_PARTY[library_filename]['url']
            )


def register_git_repos(component_name, module):
    '''
    Register git repositories the module would like to serve
    static files from.

    These can be downloaded and installed onto the server, but we
    prompt the user to confirm before doing so, since we don't
    want to accidentally conflict with devops tools.

    We don't handle multiple components wanting the same repo
    well. We should probably do something about that.
    '''
    if hasattr(module, "STATIC_FILE_GIT_REPOS"):
        debug_log(f"Loading git repositories from {component_name}")
        for repo in module.STATIC_FILE_GIT_REPOS:
            debug_log(f"Validating and registering git repository: {repo}")
            if repo in STATIC_REPOS:
                raise NotImplementedError(
                    f"Multiple modules want to clone {repo}\n"
                    "This isn't bad, but isn't implemented yet.\n"
                    "We want code to either make sure both versions\n"
                    "are the same, or place them in different locations,\n"
                    "or something. Please code that up and make a PR!"
                )
            STATIC_REPOS[repo] = copy.deepcopy(module.STATIC_FILE_GIT_REPOS[repo])
            # TODO: This is a bit awkward.... The URL and key structure won't work well
            # if we use the same repo twice.
            STATIC_REPOS[repo]['module'] = component_name
            if not os.path.exists(learning_observer.paths.repo(repo)):
                print(f"Repo {repo} does not exist.")
                print(f"It is requested by {component_name}")
                print("Should I clone it from {url} to {location}?".format(
                    location=learning_observer.paths.repo(repo),
                    url=module.STATIC_FILE_GIT_REPOS[repo]['url']
                ))
                yesno = learning_observer.settings.pmss_settings.clone_module_git_repos()
                yesno = yesno if yesno != 'prompt' else input("Yes/No> ")
                if yesno.lower().strip() not in ["y", "tak", "yes", "yup", "好", "نعم"]:
                    print("Fine. Get it yourself, and configure the location")
                    print("in the setting file under repos. Run me again once it's")
                    print("there.")
                    sys.exit(-1)
                gitrepo = gitserve.gitaccess.GitRepo(learning_observer.paths.repo(repo))
                print(gitrepo.clone(
                    module.STATIC_FILE_GIT_REPOS[repo]['url'],
                    mirror=module.STATIC_FILE_GIT_REPOS[repo].get("mirror", True)
                ))
                # Paths are top-level for bare repos e.g. `/home/ubuntu/repo` and subdir for
                # working repos e.g. `/home/ubuntu/repo.git` which we need to later manage.
            if not os.path.exists(os.path.join(learning_observer.paths.repo(repo), ".git")):
                STATIC_REPOS[repo]['bare'] = True
    else:
        debug_log(f"Component {component_name} has no git repositories")
    debug_log(STATIC_REPOS)


def register_wsgi_modules(component_name, module):
    '''
    We *don't* support pluggable `wsgi` modules. If you'd like to register
    an unsupported one, this will do it, though!

    `wsgi` is a way of plugging in additional servers. We use it for
    `dash` support, and it made sense to do this generically. It's
    nice for _prototyping_ too. However, it's far too general for
    modules to just plug in this way, and far too easy to screw up. At
    some point, we might:

    * Yank this out
    * Restrict it (e.g. require a URL scheme)
    * Change the API

    It definitely should not stay like this forever.

    This should be called *before* we register `dash` modules, though,
    since this is where we load `dash`.
    '''
    if hasattr(module, "WSGI"):
        for item in module.WSGI:
            item['COMPONENT_NAME'] = component_name
            # item['MODULE'] is for debugging; we should pull out
            # anything we use directly
            item['MODULE'] = module
        WSGI.extend(module.WSGI)


def register_dash_pages(component_name, module):
    '''
    Load the set of `dash` pages. We might want to change to a flat
    list later. We might also want to include URLs once available.
    '''
    if hasattr(module, "DASH_PAGES"):
        for page in module.DASH_PAGES:
            page['_BASE_PATH'] = os.path.dirname(module.__file__)
        DASH_PAGES[component_name] = module.DASH_PAGES


def register_nextjs_pages(component_name, module):
    '''
    Load the set of `nextjs` pages.
    TODO this looks a lot like the above, we ought to abstract it
    '''
    if hasattr(module, 'NEXTJS_PAGES'):
        debug_log(f'Loading nextjs pages from {component_name}')
        for page in module.NEXTJS_PAGES:
            page['_BASE_PATH'] = os.path.dirname(module.__file__)
            page['_COMPONENT'] = component_name
        NEXTJS_PAGES.extend(module.NEXTJS_PAGES)
    else:
        debug_log(f'Component {component_name} has no nextjs pages')


def load_module_from_entrypoint(entrypoint):
    '''
    Load a module from an entrypoint.
    '''
    debug_log(
        f"Loading entrypoint: {entrypoint.name} / {entrypoint.dist.version} / "
        f"{entrypoint.dist.location} / {entrypoint.dist.project_name}")
    module = entrypoint.load()
    module_name = module.__name__
    if not module_name.endswith(".module"):
        raise AttributeError("Module should be defined in a file called module.py")
    component_name = module_name[:-len(".module")]
    validate_module(module)
    debug_log(f"Corresponding to module: {module.__name__} ({module.NAME})")
    load_reducers(component_name, module)
    load_course_aggregators(component_name, module)
    load_execution_dags(component_name, module)
    load_ajax(component_name, module)
    load_dashboards(component_name, module)
    load_extra_views(component_name, module)
    register_3rd_party(component_name, module)
    register_git_repos(component_name, module)
    register_nextjs_pages(component_name, module)
    register_wsgi_modules(component_name, module)
    register_dash_pages(component_name, module)

    return module

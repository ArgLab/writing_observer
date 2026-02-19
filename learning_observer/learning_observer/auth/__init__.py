'''Authorization / authentication subsystem.

Our goal is to keep things simple. We would like a few types of accounts:

- Student (guest)
- Student (authorized)
- Teacher
- System admin
- In the future, researchers

We really don't want this blowing up into massive ACLs and
what-not. There is a broad set of use-cases for Learning Observer,
including:

* Web pages on the internet with no log-ins, and per-session "accounts"
* Small-scale deploys, with config in flat files for individual classes
* Research coglabs and studies
* Large-scale deploys integrated with school subsystems through single
  sign-on

Currently, we're developing the system to handle all of these
use-cases through configuration (e.g. different deploy for each of
these). Eventually, we'd like to handle all of these in one common
deploy, so we can cross-link, aggregate, and understand what's going
on across contexts, but there's a lot of architecture and planning work
to get there.

It's worth noting that there are two types of security:

1) **Students injecting data into the system**. Here, in many
   use-cases, lack of auth is low-stakes. The worst-case outcome in,
   for example, a cog lab, is a DoS attack. Stakes only go up if data
   is used for e.g. decisionmaking. For this reason, student auth/auth
   supports modes which are pretty lax. On the other hand, in many
   contexts, we won't have good data (e.g.  open web pages without
   sign-ins).

2) **Access to student data**. For authenticating teachers and sys
   admins, we want full paranoia.

We do want to be aware of corner-cases (e.g. students wanting access
to their own data).

We haven't figured out all of the data models here.
'''

import sys

# Decorators to confirm requests are authenticated
#
# We might consider breaking these out into AJAXy ones, which return
# an error object, and HTMLy ones, which take users to a log-in page.
# e.g. @admin_ajax @admin_html, or @admin(type=ajax)
from learning_observer.auth.utils import admin
from learning_observer.auth.utils import teacher
from learning_observer.auth.roles import ROLES

# Utility functions
from learning_observer.auth.utils import fernet_key
from learning_observer.auth.utils import google_id_to_user_id
from learning_observer.auth.utils import get_active_user
from learning_observer.auth.events import encode_id

# Utility handlers
from learning_observer.auth.handlers import logout_handler
from learning_observer.auth.handlers import user_info_handler

from learning_observer.auth.handlers import auth_middleware

# Specific authentication schemes
from learning_observer.auth.social_sso import social_handler
from learning_observer.auth.password import password_auth
from learning_observer.auth.lti_sso import handle_oidc_authorize, handle_oidc_launch, check_oidc_login

# Code below does sanity checks on configuration
#
# Importing settings isn't perfect, since this should not depend on learning_observer,
# but it's better than the alternatives
import learning_observer.prestartup
import learning_observer.settings as settings


@learning_observer.prestartup.register_startup_check
def verify_auth_precheck():
    '''
    This is a pre-startup check to make sure that the auth system is configured
    correctly.
    '''
    # We need some auth
    if 'auth' not in settings.settings:
        raise learning_observer.prestartup.StartupCheck(
            "Please configure auth")

    # If we have Google oauth, we need it properly configured.
    # TODO: Confirm everything works with Google Oauth missing
    if 'google_oauth' in settings.settings['auth']:
        if 'web' not in settings.settings['auth']['google_oauth'] or \
           'client_secret' not in settings.settings['auth']['google_oauth']['web'] or \
           'project_id' not in settings.settings['auth']['google_oauth']['web'] or \
           'client_id' not in settings.settings['auth']['google_oauth']['web'] or \
           isinstance(settings.settings['auth']['google_oauth']['web']['client_secret'], dict) or \
           isinstance(settings.settings['auth']['google_oauth']['web']['project_id'], dict) or \
           isinstance(settings.settings['auth']['google_oauth']['web']['client_id'], dict):
            error = \
                "Please configure (or disable) Google oauth\n" + \
                "\n" + \
                "Go to:\n" + \
                "  https://console.developers.google.com/ \n" + \
                "And set up an OAuth client for a web application. Make sure that configuration\n" + \
                "mirrors the one here.\n" + \
                "\n" + \
                "If you are not planning to use Google auth (which is the case for most dev\n" + \
                "settings), please disable Google authentication in creds.yaml by\n" + \
                "removing the google_auth section under auth."
            raise learning_observer.prestartup.StartupCheck("Auth: " + error)

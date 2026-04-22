'''
This file is a bit of a hack.

Here's the deal: We'd like to be able to import from dash apps:

- We'd like those apps to keep working on dash on their end stand-alone. That's
  nice for dev
- We'd like to be able to import those apps, without messing up our dash

We do this by replacing:

    from dash import ...

with:

    from learning_observer.dash_wrapper import ...

Then, if we're called in a stand-alone system, we just proxy on through to
dash. If we're running within the Learning Observer, we replace calls like
`register_page` either with no-ops, or with our own versions.

We check if we're inside LO stupidly. We should figure this out better.
'''

import sys

from dash import *

# So we're going to be a bit stupid. If we **just** import this file,
# the only learning_observer modules will be:
# ['learning_observer', 'learning_observer.dash_wrapper']
#
# If we're running in the main system, it will import learning_observer.main
#
# This way, we can tell which version of register_page to use
lo_modules = [m for m in sys.modules if "learning" in m]

if 'learning_observer.main' in lo_modules:
    def register_page(*args, **kwargs):
        pass

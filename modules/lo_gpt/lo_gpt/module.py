'''
Learning Observer GPT
'''
import learning_observer.downloads as d
import learning_observer.communication_protocol.query as q
from learning_observer.dash_integration import thirdparty_url, static_url
from learning_observer.stream_analytics.helpers import KeyField, Scope

import lo_gpt.gpt

# Name for the module
NAME = 'Learning Observer GPT'

# TODO Create a really simple dashboard for interfacing with the GPT api.
# This should be created in NextJS.
# An input for each api parameter, a submit button, and the json output.

'''
Additional API calls we can define, this one returns the colors of the rainbow
'''
EXTRA_VIEWS = [{
    'name': 'GPT Chat Completion',
    'suburl': 'api/llm',
    'method': 'POST',
    'handler': lo_gpt.gpt.api_chat_completion
}]

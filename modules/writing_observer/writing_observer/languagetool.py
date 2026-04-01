import pmss

import learning_observer.cache
import learning_observer.communication_protocol.integration
import learning_observer.prestartup
import learning_observer.settings

from learning_observer.log_event import debug_log

from awe_languagetool import languagetoolClient

client = None
DEFAULT_PORT = 8081
lt_started = False
# TODO fill this in
STUB_LANGUAGETOOL_OUTPUT = {
    'languagetool_stub': 'This is stub output. It will probably break something until we clean this up.'
}

pmss.register_field(
    name='use_languagetool',
    description='Flag for connecting to and using LT (LanguageTool).  LT is'\
                'used to find language and mechanical errors in text.',
    type=pmss.pmsstypes.TYPES.boolean,
    default=False
)
pmss.register_field(
    name='languagetool_host',
    description='Hostname of the system LanguageTool is running on.',
    type=pmss.pmsstypes.TYPES.hostname,
    default='localhost'
)
pmss.register_field(
    name='languagetool_port',
    description='Port of the system LanguageTool is running on.',
    type=pmss.pmsstypes.TYPES.port,
    default=DEFAULT_PORT
)


@learning_observer.prestartup.register_startup_check
def check_languagetool_running():
    '''
    We want to make sure that the Language Tool service is running on the server
    before starting the rest of the Learning Observer platform.

    TODO create a stub function for language tool to return dummy data when testing.
    See aggregator.py:214 for stubbing in the function
    '''
    if learning_observer.settings.module_setting('writing_observer', 'use_languagetool'):
        host = learning_observer.settings.module_setting('writing_observer', 'languagetool_host')
        port = learning_observer.settings.module_setting('writing_observer', 'languagetool_port')
        # TODO LanguageTool Client also accepts a full server url, we ought to fetch that from pmss

        global client, lt_started
        try:
            client = languagetoolClient.languagetoolClient(port=port, host=host)
            lt_started = True
        except RuntimeError as e:
            raise learning_observer.prestartup.StartupCheck(
                f'Unable to start LanguageTool Client.\n{e}'
            ) from e
    else:
        debug_log('WARNING:: We are not configured to try and use to LanguageTool. '\
            'Set `modules.writing_observer.use_languagetool: true` in `creds.yaml` '\
            'to enable the usage of the LanguageTool client.')


@learning_observer.communication_protocol.integration.publish_function('writing_observer.languagetool')
async def process_texts(texts):
    '''
    This method processes the text through Language Tool and returns
    the output.

    We use a closure to allow the system to initialize the memoization KVS.
    '''
    @learning_observer.cache.async_memoization()
    async def process_text(text):
        return await client.summarizeText(text)

    async for t in texts:
        text = t.get('text', '')
        text_data = await process_text(text) if lt_started else STUB_LANGUAGETOOL_OUTPUT
        text_data['text'] = text
        text_data['provenance'] = t['provenance']
        yield text_data

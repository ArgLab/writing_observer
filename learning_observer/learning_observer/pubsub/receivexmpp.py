'''
This is an xmpp receiver. It was tested with prosidy, although
eJabberd is a better deployment server (prosidy requires less
devops; eJabberd is known to work at extreme scale).

It may be buggy. It needs testing and test cases.

It might make sense to combine the sender and receiver into one
file.

We should also figure out abstractions to make this look like the
other pubsubs. xmpp has the upside that it can scale across
servers in a managed fashion, and the downside that it's a little
hard to hide that complexity.
'''

import asyncio

from lxml import etree

from slixmpp import ClientXMPP


class Message(str):
    '''
    This is a string-like object width additional attributes for:
    * `message_type` (e.g. 'chat')
    * `message_to` -- the destination
    * `message_from` -- the source
    * `message_id` -- conveniently added by prosody (and hopefully
      other servers)

    This lets us operate relatively seamlessly with non-XMPP code and
    preserve (some) abstraction.
    '''
    def __new__(cls, msg):
        xml_tree = etree.fromstring(msg)
        new_object = super().__new__(
            cls,
            etree.tostring(
                xml_tree, encoding='utf8', method='text'
            ).decode('utf8')
        )

        # We do this explicitly to sanitize inputs
        # (Although this is coming from a (relatively) secure source)
        new_object.message_type = xml_tree.attrib['type']
        new_object.message_to = xml_tree.attrib['to']
        new_object.message_id = xml_tree.attrib['id']
        new_object.message_from = xml_tree.attrib['from']

        return s


class ReceiveXMPP(ClientXMPP):
    '''
    An asynchronous XMPP receiver. slixmpp is asynchronous, but not
    with pythonic constructs. This translates from slixmpp-style
    callbacks to more Pythonic async/await/futures.
    '''
    def __init__(self, jid, password, debug_log=lambda x: None):
        '''
        Log into XMPP server on localhost with username `jid`, and
        password `password.` If 'debug_log' is passed, pass log
        messages to that callback.
        '''
        self.debug_log = debug_log
        ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.msg_future = self.new_future()

    def new_future(self):
        '''
        We return a future for a message, and populate it when the
        message comes in.
        '''
        return asyncio.get_event_loop().create_future()

    def session_start(self, event):
        '''
        Some XMPP servers require us to `send_presence` and
        `get_roster` before they'll talk to us.
        '''
        self.send_presence()
        self.get_roster()
        self.debug_log("XMPP receiver started")

    async def receive(self):
        '''
        Returns a future for the next message.

        We make a future, which will be filled in by `message`
        '''
        self.debug_log("Waiting for XMPP message")
        await self.msg_future
        rv = self.msg_future.result()
        self.msg_future = self.new_future()
        return Message(rv)

    async def message(self, msg):
        '''
        Callback called when a message is received.

        When this happens, we fill in our future. We
        don't need to reset the future, since that
        happens next time receive is called.
        '''
        self.debug_log("XMPP message received")
        self.msg_future.set_result(str(msg))
        # For debugging, we sometimes want to send something back
        # if msg['type'] in ('chat', 'normal'):
        #     msg.reply("Thanks for sending\n%(body)s" % msg).send()

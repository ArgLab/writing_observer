'''
We have several models for pub-sub:

1) We can use xmpp, which can run over prosody or eJabberd. These are
wickedly scaleable. We're not necessarily finished (as of the time of
this writing), which is to say they kind of work, but we sometimes
lose messages, and we can't direct them the right places.

2) We have a stubbed-in version. This only supports one user. It's
helpful for development and demos.

3) We're going to play with redis, which seems easier (but less scalable)
than xmpp, but is probably right approach for pilots.

One project which came up which might be relevant:
https://github.com/encode/broadcaster

TODO this module is no longer being used by the LO system.
This should be removed.
'''
import sys

import learning_observer.settings as settings
from learning_observer.log_event import debug_log

try:
    PUBSUB = settings.settings['pubsub']['type']
except KeyError:
    print("Pub-sub configuration missing from configuration file.")
    sys.exit(-1)

if PUBSUB == 'xmpp':
    import learning_observer.pubsub.receivexmpp
    import learning_observer.pubsub.sendxmpp

    async def pubsub_send(channel=None):
        '''
        Connect to an XMPP server, and return an object able to send
        events.
        '''
        sender = learning_observer.pubsub.sendxmpp.SendXMPP(
            settings.settings['xmpp']['source']['jid'],
            settings.settings['xmpp']['source']['password'],
            debug_log,
            mto='sink@localhost'
        )
        sender.connect()
        return sender

    async def pubsub_receive(channel=None):
        '''
        Connect to an XMPP server, and return an object able to receive
        events.
        '''
        receiver = learning_observer.pubsub.receivexmpp.ReceiveXMPP(
            settings.settings['xmpp']['sink']['jid'],
            settings.settings['xmpp']['sink']['password'],
            debug_log
        )
        receiver.connect()
        return receiver
elif PUBSUB == 'stub':
    import learning_observer.pubsub.pubstub

    async def pubsub_send(channel=None):
        '''
        Return an object capable of placing objects in a simple in-memory
        queue.
        '''
        sender = learning_observer.pubsub.pubstub.SendStub()
        return sender

    async def pubsub_receive(channel=None):
        '''
        Return an object capable of awaiting to remove objects from a
        simple in-memory queue.
        '''
        receiver = learning_observer.pubsub.pubstub.ReceiveStub()
        return receiver
elif PUBSUB == 'redis':
    import learning_observer.pubsub.redis_pubsub

    async def pubsub_send(channel=None):
        '''
        Connect to redis, and return an object capable of sending messages
        out over a redis queue / pubsub
        '''
        sender = learning_observer.pubsub.redis_pubsub.RedisSend()
        await sender.connect()
        return sender

    async def pubsub_receive(channel=None):
        '''
        Connect to redis, and return an object capable of receiving messages
        out over a redis queue / pubsub
        '''
        receiver = learning_observer.pubsub.redis_pubsub.RedisReceive()
        await receiver.connect()
        return receiver
else:
    print("Pubsub incorrectly configured")
    print("We support stub, redis, and xmpp")
    print("It's set to:")
    print(PUBSUB)

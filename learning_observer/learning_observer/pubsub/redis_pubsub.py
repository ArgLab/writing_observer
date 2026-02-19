'''
Pubsub for redis

redis is nice for medium-scale. It doesn't seem quite as scalable as
xmpp (at least on paper), but it's easy to develop for, easy to
maintain, and should be nice for pilot tests.

Note that redis does not guarantee delivery. This ought to notify the
receiver to dequeue events, rather than sending events directly.
'''

import asyncio
import asyncio_redis


class RedisSend():
    '''
    Simple async pubsub sender. To use:
    >> sender = RedisSend("channel-1")
    >> sender.connect()
    >> sender.send_event("Hello!")
    '''
    def __init__(self, channel='test_channel', debug_log=lambda x: None):
        '''
        We connect to a redis pubsub channel passed in `channel`. If we
        want detailed logging, we can provide a callback `debug_log` which
        takes a string (and e.g. prints it)

        Note that the verbosity on logging is excessive, even for passing to
        informational loggers, for most uses. It's for debugging.
        '''
        self.s_connection = None
        self.channel = channel
        self.debug_log = debug_log
        self.debug_log("Redis send created")

    async def connect(self):
        '''
        Await a new redis connection. We need this in its own function,
        since Python does do async in magic functions like `__init__`.
        As an alternative, we could have an async factory function.

        In the current implementation, this is optional for the sender
        (which will connect in `send_event` if this is not called),
        but required for the receiver. Implementations change, so we
        recommend calling it.
        '''
        self.s_connection = await asyncio_redis.Connection.create()
        self.debug_log("Redis send connected")

    async def send_event(self, mbody):
        '''
        We send an event. Note that `asyncio-redis` does reconnects if
        a connection is lost, but it'd be good to have better error
        handling here too (that `is None` is not for error handling; just
        so the code works if the user didn't call `connect`).
        '''
        if self.s_connection is None:
            await self.connect()
            self.debug_log("Redis send reconnected")
        n = await self.s_connection.publish(self.channel, mbody)
        self.debug_log("Sent event to " + str(n))


class RedisReceive():
    '''
    Simple async pubsub sender. To use:
    >> receiver = RedisReceive("channel-1")
    >> receiver.connect()
    >> message = await receiver.receive()
    '''
    def __init__(self, channel='test_channel', debug_log=lambda x: None):
        '''
        We connect to a redis pubsub channel passed in `channel`. If we
        want detailed logging, we can provide a callback `debug_log` which
        takes a string (and e.g. prints it)

        Note that the verbosity on logging is excessive, even for passing to
        informational loggers, for most uses. It's for debugging.
        '''
        self.r_connection = None
        self.subscriber = None
        self.channel = channel
        self.debug_log = debug_log
        self.debug_log("Redis receive initialized")

    async def connect(self):
        '''
        We need to establish a connection to begin receiving messages
        on startup (before receive is called).
        '''
        self.r_connection = await asyncio_redis.Connection.create()
        self.subscriber = await self.r_connection.start_subscribe()
        await self.subscriber.subscribe([self.channel])
        self.debug_log("redis receive connected")

    async def receive(self):
        '''
        Unless this is at the start of the program, be sure to call
        `connect` as soon as you want to start capturing messages.
        '''
        if self.r_connection is None:
            self.debug_log("redis receive reconnected")
            await self.connect()
        self.debug_log("awaiting event")
        item = await self.subscriber.next_published()
        self.debug_log("Got event!")
        return item.value


if __name__ == '__main__':
    async def main():
        sender = RedisSend(debug_log=print)
        await sender.connect()
        receiver = RedisReceive(debug_log=print)
        await receiver.connect()
        await sender.send_event("hi")
        await sender.send_event("bye")
        received_msg = await receiver.receive()
        print(received_msg)
        received_msg = await receiver.receive()
        print(received_msg)

    asyncio.run(main())

'''
This is a stubbed-in version of the XMPP send/receive code. It is
helpful for development and debugging.
'''

import collections
import asyncio

# We should eventually have a list of queues: One for each
# subscriber. For now, we only support one subscriber.
queue = collections.defaultdict(asyncio.Queue)


class SendStub():
    '''
    Minimal class for sending events over a channel. Perhaps
    this should be a closure?
    '''
    def __init__(self, channel='dummy'):
        '''
        Create dumb in-memory queue, outgoing channel
        '''
        self.channel = channel

    async def send_event(self, mbody):
        '''
        Place an object in the queue
        '''
        queue[self.channel].put_nowait(mbody)
        return True


class ReceiveStub():
    '''
    Minimal class for receiving events over a channel. Perhaps
    this should be a closure?
    '''
    def __init__(self, channel='dummy'):
        '''
        Create dumb in-memory queue, incoming channel
        '''
        self.channel = channel

    async def receive(self):
        '''
        Wait for an object from the queue
        '''
        return await queue[self.channel].get()


if __name__ == '__main__':
    async def main():
        '''
        Helper function so we can run asynchronously
        '''
        sender = SendStub()
        receiver = ReceiveStub()
        await sender.send_event("hi")
        await sender.send_event("bye")
        response = await receiver.receive()
        print(response)
        response = await receiver.receive()
        print(response)

    asyncio.run(main())

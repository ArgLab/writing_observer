Messaging Technologies
======================

We may need to route a lot of messages. The best protocol is
XMPP. [ejabberd](https://www.ejabberd.im/) is super-scalable, but
requires a lot maintance. [prosody](https://prosody.im/) is
(relatively) quick and easy. 

There are a lot of clients for Python. We did an eval of a few. If I
recall, we tried [xmpppy](https://github.com/xmpppy/xmpppy),
[SleekXMPP](http://sleekxmpp.com/), and eventually settled on
[Slixmpp](https://slixmpp.readthedocs.io/en/latest/).

A step up in simplicty are AWS hosted services like SQS/SNS; those
have proprietary lock-in, and for our use-case, rather high pricing.

Another step up in simplicy are the pub-subs built into redis and
postgresql. These work fine in moderate-size installs, but it's not
clear these would scale to where we hope this system goes.

For development, we support in-memory pubsub.

In the current use-case (classroom dashboards), polling beats
pub-sub. Students generate many events per second, and teachers need
updates perhaps every few hundred milliseconds at most.
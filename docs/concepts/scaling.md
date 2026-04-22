# Scaling Architecture

The goal is for the Learning Observer to be:

* Fully horizontally-scaleable in large-scale settings
* Simple to run in small-scale settings

It is worth noting that some uses of Learning Observer require
long-running processes (e.g. NLP), but the vast majority are small,
simple reducers of the type which would work fine on an 80386
(e.g. event count, time-on-task, or logging scores / submission).

## Basic use case

In the basic use case, there is a single Learning Observer process
running. It is either using redis or, if unavailable, disk/memory as a
storage back-end.

## Horizontally-scalable use-case

LO needs to handle a high volume of incoming data. Fortunately,
reducers are sharded on a key. In the present system, the key is
always a student. However, in the future, we may have per-resource,
per-class, etc. reducers.

A network roundtrip is typically around 30ms, which we would like to
avoid. Therefore, we would like reducers to be able to run keeping
state in-memory (and simply writing the state out to our KVS either
with each event, or periodically e.g. every second). Therefore, we
would like to have a fixed process per key so that reducers can run
without reads.

Our eventual architecture here is:

```
incoming event --> load balancer routing based on key --> process pool
```

Events for the same key (typically, the same student) should always
land on the same process.

Eventually, we will likely want a custom load balancer / router, but
this can likely be accomplished off-the-shelf, for example by
including the key in an HTTP header or in the URL.

**HACK**: At present, if several web sockets hit a server even with a
  common process, they may not share the same in-memory storage. We
  should fix this.

## Task-scalable use-case

A second issue is that we would like to be able to split work by
reducer, module, or similar (e.g. incoming data versus dashboards).

Our eventual architecture here is:

```
incoming event --> load balancer routing based on module / reducer --> process pool
```

The key reason for this is robustness. We expect to have many modules,
at different levels of performance and maturity. If one module is
unstable, uses excessive resources, etc. we'd like it to not be able
to take down the rest of the system.

This is also true for different views. For example, we might want to
have servers dedicated to:

* Archiving events into the Merkle tree (must be 100% reliable)
* Other reducers
* Dashboards

## Rerouting

In the future, we expect modules to be able to send messages to each
other.

## Implementation path

At some point, we expect we will likely need to implement our own
router. However, for now, we hope to be able to use sticky routing and
content-based routing in existing load balancers. This may involve
communcation protocol changes, such as:

- Moving auth information from the websocket stream to the header
- Moving information into the URL (e.g. `http://server/in#uid=1234`)

Note that these are short-term solutions, as in the long-term, only
the server will know which modules handle a particular event. Once we
route on modules, an event might need to go to serveral servers. At
that point, we will likely need our own custom router / load balancer.

In the short-term:

* [Amazon](https://aws.amazon.com/elasticloadbalancing/application-load-balancer/?nc=sn&loc=2&dn=2)
supports sticky sessions and content-based routing. This can work on data in the headers.
* nginx can be configured to route to different servers based on headers and URLs. This is slightly manual, but would work as well. 

## Homogenous servers

Our goal is to continue to maintain homogenous servers as much as
possible. The same process can handle incoming sockets of data, render
dashboards, etc. The division is handled in devops and in the load
balancer, e.g. by:

- Installing LO modules only on specific servers
- Routing events to specific servers

The goal is to continue to support the single server use-case.

## To do

We need to further think through:

- Long-running processes (e.g. NLP)
- Batched tasks (e.g. nightly processes)

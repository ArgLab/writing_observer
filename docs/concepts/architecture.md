# Architecture

Piotr Mitros

## Introduction

Like all such documents, this document should be taken with a grain of
salt. It my be out-of-date, or not fully implemented.

## Overview

1. Events come from a web browser over a web socket.
2. The server performs a reduce operation of some kind on these
   events. This operation maintains a per-student state (for each
   plug-in) inside of a KVS.
3. A subset of the internal state is used to compute state as sent to
   an educator dashboard.
4. Whenever an event is processed, consumers are notified via a pubsub.
5. Consumers can aggregate these notifications, inspect the external state,
   and make a dashboard.

## Application platform structure

Learning Observer acts as the shared platform that hosts and coordinates
modules. The core `learning_observer` package owns the boot process: it
loads configuration, establishes connections to databases and pub/sub
systems, and exposes the APIs modules use to register reducers,
dashboards, and other artifacts. Individual modules focus on defining
those artifacts, relying on the platform to handle data ingestion and
communication so new functionality can be added without duplicating the
runtime infrastructure.

### Technology choices

1. Generic student information (e.g. names, auth, etc.) cn live in
   flat files on the disk, sqlite, or postgres. As of this writing, this
   is not built.
2. The KVS for the reduce can either be an in-memory queue or
   redis. Redis can be persistent (for deploy) or ephemeral (for
   development). As of this writing, all three work.
3. The pub-sub can be an in-memory queue (for development), redis (fo
   easy deployment), or xmpp (for scalable deployment). As of this writing,
   all three work, but xmpp is buggy/unfinished.
4. The front-end uses bulma and d3.js.

### Architectural Constraints

1. By design, this system should be in a usable (although not
   necessarily scalable or reliable) state with just a `pip
   install`. There should be no complex webs of dependencies.
2. However, there can be a complex web of dependencies for robust,
   scalable deployment. For example, we might use an in-memory
   queue in a base system, and switch to a high-performance data
   store for deployment.
3. For most abstractions, we want to initially build 2-3 plug-ins. For
   example, we're initially building this with 2-3 streaming
   modules. We support 2-3 pubsubs, and 2-3 key-balue stores. This is
   enough to, in most cases, guarantee the abstractions aren't
   specific to one thing. However, it's small enough we can change
   both sides of an API boundary.
4. Once we know we have the right set of abstractions, we can open up
   the flood gates to more plug-ins.

### Process constraints

It's better to say "no" to a feature than to break the
architecture. We're in this for the long haul. It's okay to have
scaffolding, though. Half-built things are okay if they're in the
right place, and can be incrementally evolved to be right.

We try to avoid any technical debt which carries high interest (higher
maintenance costs down the line) -- bad APIs, etc. We don't mind
low-interest technical debt nearly as much (things which need to get
finished later, but won't blow up).

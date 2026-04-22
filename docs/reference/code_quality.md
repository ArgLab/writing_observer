Code Quality
===========

In general, we develop code in multiple passes. We try to build
proofs-of-concept and prototypes to figure out what we're doing. These
try to explore:

- Product issues. E.g. mockups to show teachers in focus groups
- Understanding capabilities. E.g. can we build an NLP algorithm
  to do something?
- Integrations. What information does Google Classroom give us?

These help us understand what we're doing and mitigate risks. Once we
have a clear idea, we move code into the system, either rewriting from
scratch or reusing. Here, the goal is to get the overall architecture
right:

- Put big pieces in the right modules
- Put correct interfaces between those modules

Usually, in this stage, the goal is to get to a minimum working (not
necessarily viable) system to iterate from. This often involves a lot
of _scaffolding code_. Scaffolding code is intended to be thrown away.

Once that's done, we make successive cleanups to make the code
readable, deployable, and production-ready.

We generally don't do a lot of test-driven development. We usually add
tests towards the end of the process for two reasons:

1. Tests can make code less agile, before we know what we're doing and
have the right interfaces. Big changes involve modifying tests. At early
stages, broken / non-working code is a lot less harmful.
2. TDD sometimes leads to code which mirror bugs in tests. Tests should
independently validate code.

We do have a lot of simple tests (`doctest` or
`if __name__ == '__main__:' kinds of things) purely for
speed-of-development. As of this writing, we need many more system tests.

Code Goals and Invariants
-----------

As a research system, our goal is to have an **archival log of
everything that happened**. We'd like to be able to remove pieces of
that (e.g. to comply with GDPR requests), which is documented in more
detail in the Merkle tree docs. You'll see a lot of code which will,
for example, annotate with data from `git` so we know what version of
the system generated a particular piece of data. That's important. The
level of integration with tools like `git` is not a hack. We pick
technologies (like `jupyter notebooks`) which allow good logging as
well.

We would like the system to be **simple to develop, deploy, and
maintain**.
* For the most part, when we add external technologies, we want to
  include simple alternatives which don't require a lot of dev-ops. We
  won't tie ourselves to SaaS services, and if we add a scalable data
  store, we'll usually have a disk-based or memory-based alternative.
* Anything which needs to be done to set up the system should either
  be done automatically at startup, or give clear instructions at
  startup.

We would like the system to be modular, and scalable to a broad set of
analytics modules. The *Writing Observer* is just one module plugged
into the system. We aim (but don't yet achieve) a level of simplicity
where undergrads can develop such modules, and they can work reliably
and scalably. Here, the customer is the developer.

Proofs of concepts and prototypes
-----------

**Proof-of-concepts and prototypes**. We have no particular
standards. The goal is to show a new UX, NLP algorithm, visualization,
integration, or what-not. However, this should be isolated from the
main codebase. We might have a `prototypes` directory, forks,
branches, or simply keep these on our device. We do like to have a
version history here, since it's often helpful to look back (things we
decide not to do sometimes turn out to be useful later).

System code
-----------

As we move code into the main system, standards go up a little bit.

1. We expect code to comply with `pycodestyle`, ignoring the
   restriction on line length. We do run `pylint` as well, but we
   don't expect 100 percent compliance. Before making a PR, please
   check your code with `make codestyle`.
2. We are starting to work hard to have a clean commit record. Each
   commit and each PR should, to the extent possible, do one thing and
   one thing only.

We don't expect initial versions of code to be perfect, but we do
expect successive passes over code to iteratively improve code quality
(documentation, robustness, modularity, etc.). We may increase
standards for initial code quality as the system matures. Initial
low-quality code is best kept behind a feature flag.

Scaffolding code
-----------

Getting interface right and having a working system to develop in
often requires scaffolding code. Scaffolding code shouldn't be used in
production, but is often critical during development. For example, if
we need a high-performance queue, we might use a Python list in the
interrim.

**The major problem we've had is with developers treating scaffolding
code as either a prototype or as final code. Again, scaffolding code
is intended to be thrown away.**

Taking time to improve code quality on scaffolding is wasted time,
since it is going away. If you have time, please work to replace it.

Documentation
-----------

We need a lot more. This makes more sense to do once the system is
more mature.
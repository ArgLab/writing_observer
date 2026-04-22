# Writing Observer and Learning Observer

![Writing Observer Logo](learning_observer/learning_observer/static/media/logo-clean.jpg)

This repository is part of a project to provide an open source
learning analytics dashboard to help instructors be able to manage
student learning processes, and in particular, student writing
processes.

![linting](https://github.com/ArgLab/writing_observer/actions/workflows/pycodestyle.yml/badge.svg)

## Learning Observer

_Learning Observer_ is designed as an open source, open science learning
process data dashboarding framework. You write reducers to handle
per-student writing data, and aggegators to make dashboards. We've
tested this in math and writing, but our focus is on writing process
data.

At a high level, Learning Observer functions as an application platform.
The primary `learning_observer` module bootstraps the system: it loads
configuration, connects to storage and messaging back ends, and brokers
communication with data sources. Other modules plug into that
infrastructure to define the specific reducers, dashboards, and other
items that users interact with, letting teams experiment with new
features without having to reimplement the platform core.

It's not finished, but it's moving along quickly.

## Writing Observer

_Writing Observer_ is a plug-in for Google Docs which visualizes writing
data to teachers. Our immediate goal was to provide a dashboard which
gives rapid, actionable insights to educators supporting remote
learning during this pandemic. We're working to expand this to support
a broad range of write-to-learn and collaborative learning techniques.

## Status

There isn't much to see here for external collaborators yet. This
repository has a series of prototypes to confirm we can:

* collect the data we want;
* extract what we need from it; and
* route it to where we want it to go (there's _a lot_ of data, with
  complex dependencies, so this is actually a nontrivial problem)

Which mitigates most of the technical risk. We also now integrate with
Google Classroom. We also have prototype APIs for making dashboards, and
a few prototype dashboards.

For this to be useful, we'll need to provide some basic documentation
for developers to be able to navigate this repo (in particular,
explaining _why_ this approach works).

This system is designed to be _massively_ scalable, but it is not
currently implemented to be so (mostly for trivial reasons;
e.g. scaffolding code which uses static files as a storage model). It
will take work to flush out all of these performance issues, but we'd
like to do that work once we better understand what we're doing and
that the core approach and APIs are correct.

## Getting Started

We have a short guide to [installing the system](docs/tutorials/install.md).
Getting the base system working is pretty easy. To create a new module
for the system to use, check out our [cookiecutter module guide](docs/tutorials/cookiecutter-module.md).

### System requirements

It depends on what you're planning to use the system for.

The core _Learning Observer_ system works fine on an AWS nano
instance, and that's how we do most of our testing and small-scale
pilots. These instances have 512MB of RAM, and minimal CPU. It's
important that this configuration remains usable.

For deployment and more sophisticated uses (e.g. NLP) in larger
numbers of classrooms, we need **heavy** metal. As we're playing with
algorithms, deep learning is turning out to work surprisingly well,
and at the same time, requires surprisingly large amounts of computing
power. A GPGPU with plenty of RAM is helpful if you want to work with
more sophisticated algorithms, and is likely to be a requirement for
many types of uses.

All _Learning Observer_ development has been on Linux-based platforms
(including Ubuntu and RHEL). There are folks outside of the core team
who have tried to run it on Mac or on WSL, with some success.

Running on RHEL typically uses the following services:

* redis
* nginx

#### bcrypt

A note on bcrypt. The code uses bcrypt for internal password
management. There is a mess of incompatible versions. Be careful if
installing any way other than the official install to get the right
one.

## Contributing or learning more

We're still a small team, and the easiest way is to shoot us a quick
email. We'll gladly walk you through anything you're interested in.

Contact/core maintainer: Piotr Mitros

Licensing: Open source / free software. License: AGPL.

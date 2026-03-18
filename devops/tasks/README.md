Deployment Scripts
==================

Our goals are:

* We'd like to have a flock of LO servers for dynamic assessment,
  Writing Observer, random demos, etc. These should have a common
  configuration, with variations.
* We'd like to have a log of how these are configured at every point
  in time, and any changes, so we can have context for any process
  data we collect.
* We'd like this representation to be interoperable with our process
  data storage formats
* We'd like configuation data to be moderately secure. Device
  configuration won't allow exploits in itself, but it can make
  vulnerabilities more serious. While things like IDs and locations of
  resources don't present an attack vector in themselves, knowing them
  is sometimes the limiting factor on being able to exploit an attack
  vector (for example, if I have an exploit where I can read one
  arbitrary file on your system, being able to leverage that attack
  hinges on knowing what files you have where)
* However, configuration data also sometimes needs to stores things
  which are super-sensitive, like security tokens and similar.
* Making changes should be fast and easy. This happens all the time.
* Digging into archives doesn't need to be easy, just possible. For
  research, only a few types of analysis need it. For operations, you
  usually only need it for debugging or disaster recovery.

Our **planned** architecture is:

* A set of `fabric` script which can spin up / spin down / update
  machines (with appropriate logging)
* A baseline configuration in `ansible`. 
* Deltas from that configuration stored in an independent `git` repo
* Security tokens stored in a seperate TBD data store. We'll populate
  these with templates.
* Log files of when new versions are updated/deployed/brought down, in
  the same system as our process data
* The tagging process data with `git` hashes of what state the system
  was in when it generated it.

We're making the baseline `ansible` configuration pretty featureful,
since as a research project, it's helpful to be able to `ssh` into
machines, and e.g. run `Python` scripts locally.

Whether or not we need `ansible`, `fabric`, or both is a bit of an
open question.

Where we are
------------

This will be out-of-date quickly, but as of this writing:

* We can provision, terminate, and update machines with a baseline
  configuration.
* A lot of stuff is hardcoded, which would make this difficult for
  others to use (e.g. learning-observer.org).
* We install packages, grab things from `git`, etc, but don't handle
  configuration well yet.
* We don't log.

We orchestrate servers with [invoke](https://www.pyinvoke.org/):

* `inv list` will show a listing of deployed machines
* `inv provision [machine]` will spin up a new AWS machine
* `inv update` will update all machines
* `inv terminate [machine]` will shut down a machine
* `inv connect [machine]` will open up an `ssh` session to a machine
* `inv configure [machine]` is typically run after provision, and
  will place configuration files (which might vary
  machine-by-machine) (mostly finished)
* `inv certbot [machine]` will set up SSL (unfinished)
* `inv downloadconfig [machine]` will copy the configuration back.
* `inv create [machine]` is a shortcut to do everything for a new instance in one step (provision, configure, certbotify, and download the SSL config)

A lot of this is unfinished, but still, it's already ahead of the AWS
GUI and doing things by hand. The key functionality missing is:

* High-quality logging
* Fault recovering
* Version control of configurations

To set up a new machine, run:

```
inv provision [machine]
inv configure [machine]
inv certbot [machine]
inv downloadconfig [machine]
```

From there, edit configuration files in `config` and to update the
machine to a new version, run

```
inv configure [machine]
```

Debugging
---------

The most annoying part of this setup is getting `systemd` working,
which is poorly documented, inconsistent, and poorly-engineered. The
tool are `journalctl -xe |tail -100`, looking at `lo.err` (currently
in `/home/ubuntu/`, but should move to `/var/log/` eventually), and
`systemctl status --full learning_observer`. The most common issues
are permissions (e.g. running as the wrong user, log files generated
as `root:root` at some point, etc), running from the wrong directory,
and similar sorts of environment issues.

Logging
-------

We are logging system configuration with `git`. Note that this is
**NOT** atomic or thread-safe. This is perhaps a bug, and perhaps by
design:

* Tasks take a _while_ to run, and they need to run in parallel when
  managing many machines.
* A better (much more complex) approach would use branches or do
  atomic commits at the end (e.g. download to a temporary dir, and
  move right before the commit.
* However, it is possible to reverse-engineered exactly what happened,
  roughly when. This is good enough for now.
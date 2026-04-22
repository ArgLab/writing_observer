Dev-ops scripts
===============

This contains machinery for spinning up, shutting down, and managing
Learning Observer servers. It's usable, but very much not done yet. We
can spin up, spin down, and list machines, but this ought to be more
fault-tolerant, better logged, less hard-coded, etc.

We would like to be cross-platform, and evenually support both
Debian-based distros and RPM-based distros. We're not there yet
either. We'd also like to support multiple cloud providers. We're not
there yet either. However, we probably won't accept PRs which move us
away from this goal.
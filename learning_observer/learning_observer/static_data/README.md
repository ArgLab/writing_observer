There can be more than one....
==============================

This directory contains text files defining a sample pool of
users.

We would like to support either:

* student roster information stored in text files (for debugging,
  testing, or small-scale deployment)
* in a database (for large-scale deployment)
* retrieved in real-time from an LMS

Having more than one abstraction means we're not locked into one
platform. The long-term vision of this project would have it
supporting a broad range of platforms, and that's helpful.

Google is also !@#$%^ bad at anything B2B, and having synthetic data
is a nice fallback. It:

* allows open source developers to contribute who don't have access to
  Google Apps accounts, whether by not passing Google's draconian
  verification process, being randomly flagged, Google being
  backlogged by months in approving accounts, or any of the other
  issues Google runs into.
* Gives a fallback next time Google makes breaking API changes (we can
  use the last-known roster data to stay afloat for a while)

It also allows developers to work off-line, and if we're careful, to
work without a working front-end (since front-end API calls can just
retrieve static files, if we're careful).
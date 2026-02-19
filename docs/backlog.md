Project Backlog
===============

* Figure out why LO doesn't start on reboot, or how to make it restart
  on crashes
* Figure out if/when document ID is missing
* Switch to the annotated canvas
* Be able to pull a document associated with a specific assignment in
  Google Classroom
* Implement roll-offs for whole-document operations (e.g. long-running
  NLP operations, which should be run periodically)
  - Implement simple algorithm, comment on complex algorithms

Robustness
----------

* Confirm what happens with students working in groups
* How do we capture formatting?
* How do we handle an Outline view?
* What happens with large documents?
* What happens with editing outside of the system

Plumbing
-------

* Robust queues client-side
* Client auth/auth
* Handle server disconnects
* Proper test frameworks
  - Replay
* Refactor rosters

Additional features
-------------------

* How do we handle peer groups?
* Create more dashboards
1. Flagging students in need of help?
2. Providing information about use of academic vocabulary?

APIs
----

* Generate dashboards with generic aggregate operations
* Handle client config robustly
* Figure out how to integrate slooow NLP algorithm calls into the
  real-time server architecture

Logging
-------

* Implement robust data store

Scaling
-------

* Database / database schemas for user management if we wish to move
  beyond pilot
* Online settings management?
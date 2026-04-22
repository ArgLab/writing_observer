Authentication Framework
========================

We have two types of authentication:

* We would like to know that events coming into the system are coming
  from where we believe they are.
* We would like to know that users log into the system who can view
  student data are who we think they are.

For the most part, these have very different security profiles. If a
user can spoof events, the worst-case outcome is:

* A disrupted study
* A disrupted teacher dashboard

In small-scale studies, demos, and similar, a high level of security
is not required, especially when running on `localhost`, VPN, or in an
IP-restricted domain.

On the other hand, we **cannot** leak student data. Authenticating
teachers and staff requires a high level of security.

Event authentication
--------------------

Events are authenticated in the file `events.py`. This is
semi-modular. We have several authentication schemes, most of which
rely on a special header. We used to include auth information with
each event, and we have some backwards-compatibility code there as
well.

Event authentication isn't super-modular yet; it's all in one file,
but the schemes are pluggable. Schemes include:

* `guest`. Each session is assigned a unique guest ID. This is nice
  for demos, studies, and coglabs.
* `local_storage`. Designed for Chromebooks. Each user is given a
  unique token, usually stored in the extension's local storage. The
  header sends a unique, secure token mapping to one user.
* `chromebook`. The Chromebook sends a user ID. This is *not secure*
  and vulnerable to spoofing. It can be combined with `local_storage`
  to be secure.
* `hash_identify`. User sends an identity, which is not
  authenticated. This is typically for small coglabs, where we might
  have a URL like `http://myserver/user-study-5/#user=zihan`
* `testcase_auth`. Quick, easy, and insecure for running testcases.

We do maintain providence with events, so we can tell which ones came
from secure or insecure sources.

We need Google OAuth.

Teacher authentication
----------------------

As authentication schemes, we support:

* Password authentication
* Trusting HTTP basic auth from nginx
* Google OAuth

We need to be particularly careful with the second of
these. Delegating authentications to `nginx` means that we need to
have nginx properly configured, or we can be attacked.

User authentication is intended to be fully modular, and we intend to
support more schemes in the future. Right now, each scheme is in its
own file, with `handlers.py` defining a means to log users in, out, as
well as a middleware which annotates the request with user
information.

Session framework
-----------------

We keep track of users through
[aiohttp_session](https://aiohttp-session.readthedocs.io/en/stable/). We
store tokens encrypted client-side, which eliminates the needed for
database fields.

User information
----------------

We keep track of user information in a dictionary. Eventually, this will
probably be a dictionary-like object.

Current fields:

* `name`: We keep full name, since not all languages have a first name /
  last name order and breakdown.
* `nick`: Short name. For a teacher, this might be "Mrs. Q" or "李老师."
  For a student, this might by "Timmy." In the future, we might think
  through contexts and relationships (e.g. a person might be a teacher,
  a coworker, and student)
* `user_id`: Our internal user ID. In most cases, this is the authentication
  scheme, followed by the ID within that scheme. For example, Google user
  1234, we might call 'gc-1234.' Test case user 65432, we might call
  `tc-65432`
* `safe_user_id`: An escaped or scrubbed version of the above. In some cases,
  we have data from unauthenticated sources, and we don't want injection
  attacks. There is an open question as to which of these is canonical,
  and whether these ought to be swapped (e.g. `source_user_id` and
  `user_id`). It depends on where we do JOIN-style operations more often.
* `picture`: Avatar or photo for the user
* `google_id`: Google username

We will want to think about how to handle joins. Users often have multiple
accounts which should be merged:

* A user signs up through two mechanisms (e.g. signs up with passwords and
  then Google)
* Users are autoenrolled (e.g. through two educational institutions)
* Automatic accounts convert into permanent accounts (e.g. data begins
  streaming in for an unauthenticated / guest user)

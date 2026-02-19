Google Docs APIs
================

These are experiments with the Google Docs and Google Drive APIs. On
the whole, the APIs are developer-friendly and easy-to-use. They run
into a few brick walls for our use-case. Upsides:

* We can grab ground truth documents via the Google Drive and Google
  Docs APIs, at least assuming the document is shared with the teacher
  (which may or may not be the case), or by the student.
* We can grab [comments](Link https://developers.google.com/drive/api/v3/reference/comments),
  [Revisions](https://developers.google.com/drive/api/v3/reference/revisions) (although not
  with the same granularity as our extension),
  [comment replies](https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/drive_v3.replies.html),
  and [suggested revisions](https://developers.google.com/docs/api/how-tos/suggestions)
* There is a poorly-document API which appears to monitor for changes (https://developers.google.com/drive/api/v3/reference/channels)
* Some of the APIs include [indexes](https://developers.google.com/docs/api/how-tos/overview)
* We can get a lot more through Vault, but I'm not sure schools would
  grant us that kind of access. It's also tough to test too, since it
  requires a Google Workspace account of the right type.

The major constraints are:

* Google's permissions and auth system, which isn't really designed
  for automation or monitoring. They're designed to grant short-term,
  expiring access, although it looks like Google recently added
  [service accounts](https://github.com/googleapis/google-api-python-client/blob/master/docs/oauth-server.md)
  which may address this issue.
* They're not designed for realtime use (e.g. monitoring writing
  processes)

The APIs couldn't replace our pipeline, but would be a helpful
supplement.

Note that this code would need to be rewritten for *Writing Observer*,
since the [client
library](https://github.com/googleapis/google-api-python-client/blob/master/docs/README.md)
we're using is not asynchronous, and would lead to performance issues.

We also (in the current version) do no pagination; this is just to
understand the types of data returned.

To get started, you will need a `credentials.json` from Google's API
console, set up for a desktop application.
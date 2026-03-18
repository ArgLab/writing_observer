# LTI Grade Demo

A minimal example dashboard that uses the Assignment & Grade Service (AGS) proxy
routes registered during an LTI launch. It surfaces routes under
`/views/wo_lti_grade_demo/`:

- `/lti-grade-demo/` renders a simple HTML dashboard for experimenting with grade
  submissions.
- `/session-summary/` dumps the current LTI launch metadata (provider, course
  context, and active user).
- `/line-items/` lists cleaned AGS line items for the current course (or a
  specified courseId) to help pick a target assignment.
- `/submit-score/` proxies an AGS score payload to the LMS for the current LTI
  session.

The module depends on an active LTI session with `canvas_routes` (or the
relevant LMS routes) enabled so the AGS endpoints are registered in
`learning_observer.integrations.INTEGRATIONS`.

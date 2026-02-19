import datetime

import aiohttp_session
from aiohttp import web

import learning_observer.constants as constants
import learning_observer.integrations
import learning_observer.runtime


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>LTI Grade Demo</title>
  <style>
    body { font-family: sans-serif; margin: 2rem auto; max-width: 960px; }
    h1, h2 { margin-bottom: 0.5rem; }
    .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .row { display: flex; gap: 1rem; flex-wrap: wrap; }
    label { display: block; font-weight: 600; margin: 0.5rem 0 0.25rem; }
    input, select { width: 100%; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; }
    button { padding: 0.6rem 1rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }
    button:disabled { background: #9ca3af; cursor: not-allowed; }
    pre { background: #0b1729; color: #e5e7eb; padding: 0.75rem; border-radius: 8px; overflow-x: auto; }
    .error { color: #b91c1c; }
  </style>
</head>
<body>
  <h1>LTI Grade Demo</h1>
  <p>This sample page reads the LTI launch context from your session and posts a score through the Assignment &amp; Grade Service (AGS) proxy routes.</p>

  <div class="card">
    <h2>Session info</h2>
    <p id="session-status">Loading...</p>
    <pre id="session-json"></pre>
  </div>

  <div class="card">
    <h2>Submit a grade</h2>
    <p>Fill the fields and submit. Defaults use the current LTI user and course.</p>
    <div class="row">
      <div style="flex: 1 1 220px;">
        <label for="courseId">Course ID (defaults to API ID)</label>
        <input id="courseId" placeholder="Course ID" />
      </div>
      <div style="flex: 1 1 220px;">
        <label for="lineItemId">Line Item ID *</label>
        <input id="lineItemId" placeholder="Line item ID" list="lineItemOptions" />
        <datalist id="lineItemOptions"></datalist>
        <button id="loadLineItems" style="margin-top: 0.5rem;">Load line items</button>
      </div>
      <div style="flex: 1 1 220px;">
        <label for="userId">User ID (defaults to launch user)</label>
        <input id="userId" placeholder="LTI userId" />
      </div>
    </div>
    <div class="row">
      <div style="flex: 1 1 180px;">
        <label for="scoreGiven">Score Given</label>
        <input id="scoreGiven" placeholder="e.g. 8" />
      </div>
      <div style="flex: 1 1 180px;">
        <label for="scoreMaximum">Score Maximum</label>
        <input id="scoreMaximum" placeholder="e.g. 10" />
      </div>
      <div style="flex: 1 1 220px;">
        <label for="activityProgress">Activity Progress</label>
        <input id="activityProgress" value="Completed" />
      </div>
      <div style="flex: 1 1 220px;">
        <label for="gradingProgress">Grading Progress</label>
        <input id="gradingProgress" value="FullyGraded" />
      </div>
    </div>
    <div class="row">
      <div style="flex: 1 1 320px;">
        <label for="timestamp">Timestamp (ISO 8601)</label>
        <input id="timestamp" />
      </div>
    </div>
    <p class="error" id="error"></p>
    <button id="submit">Submit grade</button>
  </div>

  <div class="card">
    <h2>Last response</h2>
    <pre id="response">No submission yet.</pre>
  </div>

  <script>
    const sessionStatus = document.getElementById('session-status');
    const sessionJson = document.getElementById('session-json');
    const responsePane = document.getElementById('response');
    const submitButton = document.getElementById('submit');
    const errorPane = document.getElementById('error');
    const lineItemOptions = document.getElementById('lineItemOptions');
    const loadLineItemsButton = document.getElementById('loadLineItems');
    const courseInput = document.getElementById('courseId');
    const lineItemInput = document.getElementById('lineItemId');

    async function loadSession() {
      try {
        const resp = await fetch('/views/lo_lti_grade_demo/session-summary/');
        if (!resp.ok) {
          sessionStatus.textContent = 'Session unavailable – launch via LTI first.';
          sessionJson.textContent = await resp.text();
          submitButton.disabled = true;
          return;
        }
        const data = await resp.json();
        sessionStatus.textContent = `Logged in as ${data.userId || 'unknown user'} (provider: ${data.provider || 'unknown'})`;
        sessionJson.textContent = JSON.stringify(data, null, 2);
        if (data.ltiContext) {
          document.getElementById('courseId').value = data.ltiContext.api_id || '';
        }
        document.getElementById('userId').value = data.userId || '';
        document.getElementById('timestamp').value = new Date().toISOString();
      } catch (err) {
        sessionStatus.textContent = 'Failed to load session.';
        sessionJson.textContent = err;
        submitButton.disabled = true;
      }
    }

    async function loadLineItems() {
      errorPane.textContent = '';
      lineItemOptions.innerHTML = '';
      lineItemInput.placeholder = 'Line item ID';

      const courseId = courseInput.value;
      if (!courseId) {
        errorPane.textContent = 'Course ID is required to load line items';
        return;
      }

      loadLineItemsButton.disabled = true;
      loadLineItemsButton.textContent = 'Loading...';
      try {
        const resp = await fetch(`/views/lo_lti_grade_demo/line-items/?courseId=${encodeURIComponent(courseId)}`);
        const data = await resp.json();
        if (!resp.ok) {
          errorPane.textContent = typeof data === 'string' ? data : (data.detail || 'Failed to load line items');
          return;
        }

        if (!Array.isArray(data) || data.length === 0) {
          errorPane.textContent = 'No line items returned';
          return;
        }

        data.forEach((item) => {
          const option = document.createElement('option');
          option.value = item.id || item['id'] || '';
          option.label = item.label || item.title || option.value;
          lineItemOptions.appendChild(option);
        });

        lineItemInput.placeholder = 'Select or enter line item ID';
      } catch (err) {
        errorPane.textContent = 'Network error while loading line items';
      } finally {
        loadLineItemsButton.disabled = false;
        loadLineItemsButton.textContent = 'Load line items';
      }
    }

    async function submitGrade() {
      errorPane.textContent = '';
      responsePane.textContent = 'Submitting...';
      const payload = {
        courseId: document.getElementById('courseId').value || undefined,
        lineItemId: document.getElementById('lineItemId').value || undefined,
        userId: document.getElementById('userId').value || undefined,
        scoreGiven: document.getElementById('scoreGiven').value ? Number(document.getElementById('scoreGiven').value) : undefined,
        scoreMaximum: document.getElementById('scoreMaximum').value ? Number(document.getElementById('scoreMaximum').value) : undefined,
        activityProgress: document.getElementById('activityProgress').value || undefined,
        gradingProgress: document.getElementById('gradingProgress').value || undefined,
        timestamp: document.getElementById('timestamp').value || undefined,
      };

      try {
        const resp = await fetch('/views/lo_lti_grade_demo/submit-score/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const text = await resp.text();
        if (!resp.ok) {
          errorPane.textContent = text;
        }
        responsePane.textContent = text;
      } catch (err) {
        responsePane.textContent = err;
        errorPane.textContent = 'Network error while submitting score';
      }
    }

    document.getElementById('submit').addEventListener('click', submitGrade);
    loadLineItemsButton.addEventListener('click', loadLineItems);
    loadSession();
  </script>
</body>
</html>
"""


def _current_user_and_context(session):
    user = session.get(constants.USER, {})
    context = user.get("lti_context", {}) if isinstance(user, dict) else {}
    return user, context


def _validate_lti_session(session):
    user, context = _current_user_and_context(session)
    if not user:
        raise web.HTTPUnauthorized(text="No active LTI session")
    if constants.AUTH_HEADERS not in session:
        raise web.HTTPUnauthorized(text="Missing LTI authorization headers")
    if not context:
        raise web.HTTPBadRequest(text="Missing LTI launch context")
    provider = context.get("provider")
    if not provider:
        raise web.HTTPBadRequest(text="Missing LTI provider on session")
    return user, context, provider


async def render_dashboard(request):
    await aiohttp_session.get_session(request)  # ensure session cookie exists
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")


async def session_summary(request):
    session = await aiohttp_session.get_session(request)
    try:
        user, context, provider = _validate_lti_session(session)
    except web.HTTPException as exc:
        raise exc

    response = {
        "userId": user.get(constants.USER_ID),
        "email": user.get("email"),
        "name": user.get("name"),
        "provider": provider,
        "ltiContext": context,
        "hasAuthHeaders": constants.AUTH_HEADERS in session,
    }
    return web.json_response(response)


async def course_line_items(request):
    session = await aiohttp_session.get_session(request)
    _, context, provider = _validate_lti_session(session)

    integrations = learning_observer.integrations.INTEGRATIONS.get(provider)
    if not integrations or "assignments" not in integrations:
        raise web.HTTPServiceUnavailable(text="Line item endpoint is not registered for this provider")

    course_id = request.query.get("courseId") or context.get("api_id")
    if not course_id:
        raise web.HTTPBadRequest(text="courseId is required")

    runtime = learning_observer.runtime.Runtime(request)
    line_items = await integrations["assignments"](runtime, courseId=str(course_id))
    return web.json_response(line_items)


async def submit_score(request):
    session = await aiohttp_session.get_session(request)
    user, context, provider = _validate_lti_session(session)

    integrations = learning_observer.integrations.INTEGRATIONS.get(provider)
    if not integrations or "raw_lineitem_scores" not in integrations:
        raise web.HTTPServiceUnavailable(text="Grade submission endpoint is not registered for this provider")

    try:
        data = await request.json()
    except Exception as exc:  # pragma: no cover - aiohttp provides clear message already
        raise web.HTTPBadRequest(text=f"Invalid JSON body: {exc}")

    line_item_id = data.get("lineItemId")
    if not line_item_id:
        raise web.HTTPBadRequest(text="lineItemId is required")

    course_id = data.get("courseId") or context.get("api_id")
    if not course_id:
        raise web.HTTPBadRequest(text="courseId is required")

    timestamp = data.get("timestamp") or datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

    score_payload = {
        "userId": data.get("userId") or user.get(constants.USER_ID),
        "scoreGiven": data.get("scoreGiven"),
        "scoreMaximum": data.get("scoreMaximum"),
        "activityProgress": data.get("activityProgress", "Completed"),
        "gradingProgress": data.get("gradingProgress", "FullyGraded"),
        "timestamp": timestamp,
    }

    runtime = learning_observer.runtime.Runtime(request)
    result = await integrations["raw_lineitem_scores"](
        runtime,
        courseId=str(course_id),
        lineItemId=str(line_item_id),
        json_body={k: v for k, v in score_payload.items() if v is not None},
    )

    return web.json_response({
        "provider": provider,
        "courseId": str(course_id),
        "lineItemId": str(line_item_id),
        "submittedPayload": score_payload,
        "lmsResponse": result,
    })

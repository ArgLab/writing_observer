# Serve Learning Observer as an LTI 1.3 tool

Learning Observer ships with an IMS LTI 1.3 implementation that relies on the platform's OpenID Connect (OIDC) handshake to authenticate users and obtain scoped API access tokens from the learning management system (LMS). Use this guide to register the tool in an LMS and connect it to a course shell.

## Prerequisites

* A deployment of Learning Observer reachable by the LMS (typically via HTTPS).
* An LMS that supports LTI 1.3 with dynamic registration or manual developer keys (e.g., Canvas or Schoology).
* Administrative access in that LMS to create a developer key / external tool.

## 1. Generate and share a signing key

Learning Observer signs client assertions with an RSA private key when it exchanges OIDC launch data for an LMS access token. Generate a keypair, store the private key somewhere on the application host, and upload the public key to the LMS when you create the developer key.

```bash
# create a 4096-bit RSA keypair
openssl genrsa -out secrets/lti-tool-private.pem 4096
openssl rsa -in secrets/lti-tool-private.pem -pubout > secrets/lti-tool-public.pem
```

Record the filesystem path to the private key; you'll reference it in the application configuration in the next step.

## 2. Configure `creds.yaml`

Enable the LTI provider in `learning_observer/creds.yaml` by adding an entry under `auth.lti.<provider>`. Each provider requires the LMS endpoints, the Learning Observer redirect URL, and the private key location. A Canvas example looks like this:

```yaml
auth:
  lti:
    sample-canvas:
      client_id: "10000000000000"
      auth_uri: "https://canvas.example.edu/api/lti/authorize_redirect"
      jwks_uri: "https://canvas.example.edu/api/lti/security/jwks"
      token_uri: "https://canvas.example.edu/login/oauth2/token"
      redirect_uri: "https://lo.example.edu/lti/sample-canvas/launch"
      private_key_path: "secrets/lti-tool-private.pem"
      api_domain: "https://canvas.example.edu"  # Canvas-specific
```

Set `redirect_uri` to the public URL that will receive the POST launch request (`/lti/<provider>/launch`). The login initiation URL for the LMS is the matching `/lti/<provider>/login` route.

Restart the application after updating configuration so the new provider registration is loaded.

## 3. Enable LMS API routes

Learning Observer only exposes the IMS Names & Roles (NRPS) and Assignment & Grade Service (AGS) proxy routes when the matching feature flag is turned on. Add the appropriate flag to `creds.yaml` so the application registers the routes during startup:

```yaml
feature_flags:
  canvas_routes: true          # Canvas NRPS/AGS proxy endpoints
  # schoology_routes: true     # Schoology NRPS/AGS proxy endpoints
```

## 4. Map the roster source with PMSS

LTI launches identify the LMS provider in the session so roster lookups can decide which backend to call. Create a PMSS overlay that maps the provider to the correct roster source (see [System settings](../concepts/system_settings.md) for more on PMSS). For Canvas, create a file such as `config/roster_source.pmss` alongside `creds.yaml` with the following contents:

```pmss
roster_data[provider="sample-canvas"] {
    source: sample-canvas;
}
```

If you support multiple LMS tenants, add additional selector blocks for their email domains or provider names and point them at `schoology`, `filesystem`, or any other supported roster backend.

## 5. Register the tool in the LMS

When you create the LTI developer key/external tool inside the LMS:

1. Supply the **OIDC login initiation URL** as `https://<your-domain>/lti/<provider>/login`.
2. Supply the **redirect/launch URL** as `https://<your-domain>/lti/<provider>/launch`.
3. Paste the **public key** generated earlier so the LMS can validate the signed client assertions.
4. Copy the LMS-issued **client ID** and the platform endpoints (authorize, JWKS, token) into `creds.yaml` if you have not done so already.

Publish the developer key and install the tool in the desired course/context. The LMS will send the context identifiers in the launch claims so Learning Observer can associate sessions with the right course.

## 6. Verify the launch

* Add the external tool link to a module or assignment inside the LMS course.
* Launch the tool from within the LMS. Learning Observer should redirect the browser to the LMS's authorize endpoint, validate the launch state and nonce, and then create a session for the user when the LMS returns.
* Successful launches land on the root of the application with LMS-specific authorization headers stored in the session for follow-up roster and grade sync operations.

If the launch fails, inspect the Learning Observer logs for messages beginning with `LTI Launch`—they include detailed context whenever state validation, token exchange, or JWT verification fails. Once the LMS recognizes the tool, you can remove or hide other authentication methods; Learning Observer will automatically expose the LTI login routes whenever `auth.lti` providers are configured.

## 7. Plan student identity mapping

LTI launch data only includes the learner's email address, while Writing Observer's Google Workspace integrations emit a Google-specific user identifier. To keep downstream reducers and dashboards working for LTI cohorts, plan to run the maintenance workflow that maps emails to Google IDs. Refer to the [Student Identity Mapping guide](../concepts/student_identity_mapping.md) for an overview of how the reducer and maintenance script cooperate and how to operate the sync in production.

## 8. Submit grades through the AGS proxy

Once the feature flag for your LMS is enabled (for example `canvas_routes: true`), Learning Observer registers proxy endpoints that forward IMS Assignment & Grade Service (AGS) calls using the authorization headers captured during the LTI launch. You can submit grades for a Canvas course line item with a simple POST to the proxy URL:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -b cookies.txt \  # session created by an LTI launch
  https://lo.example.edu/sample-canvas/lineitem_scores/12345/67890 \
  -d '{
    "userId": "student-lti-id",
    "scoreGiven": 8,
    "scoreMaximum": 10,
    "activityProgress": "Completed",
    "gradingProgress": "FullyGraded",
    "timestamp": "2024-06-30T15:04:05Z"
  }'
```

* Replace `sample-canvas` with your configured provider name.
* `12345` is the Canvas course ID and `67890` is the AGS line item ID returned by the `/course_lineitems` endpoint.
* The JSON body follows the [IMS AGS score](https://www.imsglobal.org/spec/lti-ags/v2p0#score-media-type) format and is forwarded verbatim to the LMS.

For server-side use, the corresponding local function accepts the same parameters via `json_body`:

```python
await canvas_functions['raw_lineitem_scores'](
    runtime,
    courseId='12345',
    lineItemId='67890',
    json_body={
        'userId': 'student-lti-id',
        'scoreGiven': 8,
        'scoreMaximum': 10,
        'activityProgress': 'Completed',
        'gradingProgress': 'FullyGraded',
        'timestamp': '2024-06-30T15:04:05Z'
    }
)
```

`canvas_functions` is the dictionary returned by `setup_canvas_provider(...)(app)` during app initialization. Both the HTTP route and the local call reuse the LTI access token stored in the user's session, so no additional authentication headers are required.

### Try it with the sample LTI Grade Demo module

The repository ships with a sample module you can use to poke at the LTI launch context and post grades through a browser form. Install the module (e.g., `pip install -e modules/wo_lti_grade_demo`) and visit `/views/wo_lti_grade_demo/lti-grade-demo/` after launching via LTI. The page shows:

- A session summary pulled from the launch claims (provider, course context IDs, and the current `userId`).
- A minimal grade submission form that forwards to `/views/wo_lti_grade_demo/submit-score/`, which in turn calls the AGS score endpoint registered for the provider detected in the session.
- A "Load line items" helper that calls `/views/wo_lti_grade_demo/line-items/` for the current course (or a manually entered `courseId`) and fills a datalist so you can pick a valid AGS line item ID.

The helper endpoints `/views/wo_lti_grade_demo/session-summary/` and `/views/wo_lti_grade_demo/line-items/` are also available if you prefer to pull the launch metadata and line items directly and post scores with your own client.

### Getting Canvas line items to appear

Canvas only exposes LTI Assignment & Grade Service (AGS) line items for assignments that are tied to an external tool launch (or that were created through the AGS API). A plain Canvas assignment without an LTI tool configured will not show up in `/course_lineitems`. To create a testable line item:

1. In Canvas, open the course and click **Assignments → + Assignment**.
2. Set a name and points, then under **Submission Type** choose **External Tool** and pick your installed LTI tool. Save and publish the assignment.
3. Launch the tool from the assignment at least once so Canvas associates the line item with the tool.
4. Re-run the demo module's "Load line items" helper or call `/course_lineitems` and you should see the new line item label and ID.

If you prefer to create a line item programmatically, POST an AGS line item object to `/api/lti/courses/{courseId}/line_items` (or the proxy route registered by `canvas_routes`). A minimal body looks like:

```json
{
  "scoreMaximum": 10,
  "label": "My LTI Practice Assignment",
  "resourceId": "practice-1"
}
```

Canvas returns the new `id` URL in the response, which is the `lineItemId` you can plug into the grade submission examples above.

### Managing multiple assignments from one LTI tool

If your Writing Observer deployment hosts several learning experiences (for example, multiple dashboards or writing tasks) but you want to keep using a single LTI tool installation, create **one Canvas assignment per experience** and route inside the tool based on the launch claims:

1. In Canvas, add a separate **External Tool** assignment for each activity. All of them can point to the same LTI launch URL; Canvas will still generate distinct AGS line items and a unique `resource_link_id` per assignment.
2. (Optional but recommended) Add a Canvas *Custom Field* on each assignment such as `module_slug=revision` or `activity_id=essay-1`. These become `custom` claims in the LTI launch payload and let you steer users to the right part of your app.
3. In your request handler, read the launch session and route to the correct module using the custom field or `resource_link_id`. A minimal example:

   ```python
   launch = request.session['lti_launch']
   custom = launch.get('custom', {})
   target = custom.get('module_slug') or MODULE_BY_RESOURCE_LINK.get(launch['resource_link_id'])
   return RedirectResponse(f"/views/{target}/")
   ```

4. When posting grades, reuse the AGS line item associated with the launch. You can pull it from `/views/wo_lti_grade_demo/line-items/` (filtered by `courseId` and matched via `label`/`resourceId`) or store the returned `lineItem` claim from the launch for the active assignment.

This approach keeps a single LTI registration while giving instructors separate Canvas assignments and gradebook columns for each experience in your app.

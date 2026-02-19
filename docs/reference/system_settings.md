# System Settings

This page lists every field registered with PMSS for the **Learning Observer
base application**, grouped by the namespace you use in `creds.yaml`. Each
entry includes the YAML path, purpose, default (if any), and the code that
relies on it. Module-specific settings (such as the Writing Observer module)
should be documented alongside their module guides in the reference section.

Refer back to the [system settings concept](../concepts/system_settings.md)
concept guide for details on how these values are loaded and consumed by the
runtime.

## Global application keys

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `run_mode` | Selects `dev`, `deploy`, or `interactive` runtime profiles to control logging and startup behaviour. | required | [`learning_observer/learning_observer/settings.py`](../../learning_observer/learning_observer/settings.py), [`learning_observer/learning_observer/main.py`](../../learning_observer/learning_observer/main.py) |
| `hostname` | Public host name for OAuth callbacks and secure cookie scopes. Include the port when not using 80/443. | required | [`learning_observer/learning_observer/auth/social_sso.py`](../../learning_observer/learning_observer/auth/social_sso.py), [`learning_observer/learning_observer/webapp_helpers.py`](../../learning_observer/learning_observer/webapp_helpers.py) |
| `protocol` | Protocol (`http` or `https`) that governs cookie security and OAuth redirect URLs. | required | [`learning_observer/learning_observer/auth/social_sso.py`](../../learning_observer/learning_observer/auth/social_sso.py), [`learning_observer/learning_observer/webapp_helpers.py`](../../learning_observer/learning_observer/webapp_helpers.py) |
| `clone_module_git_repos` | Controls whether module git repositories are cloned automatically (`y`), skipped (`n`), or prompted (`prompt`). | `prompt` | [`learning_observer/learning_observer/module_loader.py`](../../learning_observer/learning_observer/module_loader.py) |
| `dangerously_allow_insecure_dags` | Enables uploading arbitrary dashboard DAG definitions for development experiments. Leave disabled in production. | `false` | [`learning_observer/learning_observer/dashboard.py`](../../learning_observer/learning_observer/dashboard.py) |
| `fetch_additional_info_from_teacher_on_login` | Starts a background job after Google login to fetch extra teacher documents immediately. | `false` | [`learning_observer/learning_observer/auth/social_sso.py`](../../learning_observer/learning_observer/auth/social_sso.py) |

### `config` namespace

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `config.run_mode` | Mirror of the root `run_mode` so runtime helpers can resolve the value within the `config` namespace. | required | [`learning_observer/learning_observer/main.py`](../../learning_observer/learning_observer/main.py) |
| `config.debug` | List of diagnostic toggles (for example `"tracemalloc"`) that enable extra debugging helpers during development. | `[]` | [`learning_observer/learning_observer/routes.py`](../../learning_observer/learning_observer/routes.py) |

### `server` namespace

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `server.port` | Port that the aiohttp web server binds to. Falling back to an open port in development remains TODO. | `8888` | [`learning_observer/learning_observer/main.py`](../../learning_observer/learning_observer/main.py) |

### Session management (`aio` namespace)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `aio.session_secret` | Secret used to encrypt and sign aiohttp session cookies. Generate a unique value per deployment. | required | [`learning_observer/learning_observer/webapp_helpers.py`](../../learning_observer/learning_observer/webapp_helpers.py) |
| `aio.session_max_age` | Session lifetime in seconds. | required | [`learning_observer/learning_observer/webapp_helpers.py`](../../learning_observer/learning_observer/webapp_helpers.py) |

### Dashboard Settings (`dashboard_settings` namespace)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `dashboard_settings.logging_enabled` | Determine if we should log dashboard sessions. | `false` | [`learning_observer/learning_observer/dashboard.py`](../../learning_observer/learning_observer/dashboard.py) |

### LMS Integration (`lms_integration` namespace)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `lms_integration.logging_enabled` | Determine if we should log lms integration calls. | `false` | [`learning_observer/learning_observer/log_event.py`](../../learning_observer/learning_observer/log_event.py) |

### Redis connection (`redis_connection` namespace)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `redis_connection.redis_host` | Hostname for Redis. | `localhost` | [`learning_observer/learning_observer/redis_connection.py`](../../learning_observer/learning_observer/redis_connection.py) |
| `redis_connection.redis_port` | Port for Redis. | `6379` | [`learning_observer/learning_observer/redis_connection.py`](../../learning_observer/learning_observer/redis_connection.py) |
| `redis_connection.redis_password` | Password for Redis (set to `null` when unused). | `null` | [`learning_observer/learning_observer/redis_connection.py`](../../learning_observer/learning_observer/redis_connection.py) |

### Logging (`logging` namespace)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `logging.debug_log_level` | Chooses how verbose diagnostic logging should be (`NONE`, `SIMPLE`, or `EXTENDED`). | inherits environment default | [`learning_observer/learning_observer/log_event.py`](../../learning_observer/learning_observer/log_event.py) |
| `logging.debug_log_destinations` | Ordered list of destinations that should receive debug logs (`CONSOLE`, `FILE`). | `['CONSOLE', 'FILE']` in development | [`learning_observer/learning_observer/log_event.py`](../../learning_observer/learning_observer/log_event.py) |

### Key-value stores (`kvs` namespace)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `kvs.default.type` | Backend used for the default key-value store (`stub`, `redis`, `redis_ephemeral`, or `filesystem`). | required | [`learning_observer/learning_observer/kvs.py`](../../learning_observer/learning_observer/kvs.py) |
| `kvs.default.expiry` | Expiration (seconds) required when `type` is `redis_ephemeral`. | required for `redis_ephemeral` | [`learning_observer/learning_observer/kvs.py`](../../learning_observer/learning_observer/kvs.py) |
| `kvs.default.path` | Filesystem directory for persisted values when `type` is `filesystem`; supports optional `subdirs`. | required for `filesystem` | [`learning_observer/learning_observer/kvs.py`](../../learning_observer/learning_observer/kvs.py) |
| `kvs.<name>.type` | Additional named KVS pools that modules can request by name. Same accepted values as `kvs.default.type`. | optional | [`learning_observer/learning_observer/kvs.py`](../../learning_observer/learning_observer/kvs.py) |
| `kvs.<name>.expiry` | Per-store expiration when the named pool uses the `redis_ephemeral` backend. | required for `redis_ephemeral` pools | [`learning_observer/learning_observer/kvs.py`](../../learning_observer/learning_observer/kvs.py) |
| `kvs.<name>.path` | Filesystem location (and optional `subdirs`) for the named store when using the `filesystem` backend. | required for `filesystem` pools | [`learning_observer/learning_observer/kvs.py`](../../learning_observer/learning_observer/kvs.py) |

### Roster ingestion (`roster_data` namespace)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `roster_data.source` | Selects the roster provider: `filesystem`, `google`, `schoology`, `x-canvas`, `all`, or `test`. | required | [`learning_observer/learning_observer/rosters.py`](../../learning_observer/learning_observer/rosters.py) |

### Core authentication flags (`auth`)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `auth.password_file` | Enables password authentication using the specified credentials file (generated with `lo_passwd.py`). | disabled | [`learning_observer/learning_observer/routes.py`](../../learning_observer/learning_observer/routes.py) |
| `auth.test_case_insecure` | When `true` or configured with overrides, short-circuits authentication for automated tests. | `false` | [`learning_observer/learning_observer/auth/handlers.py`](../../learning_observer/learning_observer/auth/handlers.py) |
| `auth.demo_insecure` | Demo mode that fabricates user sessions for walkthroughs; may be a boolean or a mapping with a fixed `name`. | `false` | [`learning_observer/learning_observer/auth/handlers.py`](../../learning_observer/learning_observer/auth/handlers.py) |

#### Google OAuth (`auth.google_oauth.web`)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `auth.google_oauth.web.client_id` | Google OAuth client ID. | required | [`learning_observer/learning_observer/auth/social_sso.py`](../../learning_observer/learning_observer/auth/social_sso.py) |
| `auth.google_oauth.web.client_secret` | Google OAuth client secret. | required | [`learning_observer/learning_observer/auth/social_sso.py`](../../learning_observer/learning_observer/auth/social_sso.py) |

#### LTI providers (`auth.lti.<provider>`)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `auth.lti.<provider>.auth_uri` | LMS endpoint that initiates the OIDC login flow. | required | [`learning_observer/learning_observer/auth/lti_sso.py`](../../learning_observer/learning_observer/auth/lti_sso.py) |
| `auth.lti.<provider>.jwks_uri` | JWKS endpoint used to validate LMS ID tokens. | required | [`learning_observer/learning_observer/auth/lti_sso.py`](../../learning_observer/learning_observer/auth/lti_sso.py) |
| `auth.lti.<provider>.token_uri` | OAuth token endpoint for the LMS. | required | [`learning_observer/learning_observer/auth/lti_sso.py`](../../learning_observer/learning_observer/auth/lti_sso.py) |
| `auth.lti.<provider>.redirect_uri` | Callback URL inside Learning Observer. | required | [`learning_observer/learning_observer/auth/lti_sso.py`](../../learning_observer/learning_observer/auth/lti_sso.py) |
| `auth.lti.<provider>.private_key_path` | Location of the private key used to sign LTI messages. | required | [`learning_observer/learning_observer/auth/lti_sso.py`](../../learning_observer/learning_observer/auth/lti_sso.py) |
| `auth.lti.<provider>.api_domain` | Base Canvas API domain for roster and assignment cleaners (Canvas-specific). | required | [`learning_observer/learning_observer/integrations/canvas.py`](../../learning_observer/learning_observer/integrations/canvas.py) |

#### HTTP Basic authentication (`auth.http_basic`)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `auth.http_basic.password_file` | Credential store used when Learning Observer verifies HTTP basic logins directly. Set to `null` when nginx handles auth. | required when present | [`learning_observer/learning_observer/routes.py`](../../learning_observer/learning_observer/routes.py), [`learning_observer/learning_observer/auth/http_basic.py`](../../learning_observer/learning_observer/auth/http_basic.py) |
| `auth.http_basic.login_page_enabled` | Enables the built-in login endpoint that proxies browser-provided credentials into a session. | `false` | [`learning_observer/learning_observer/auth/http_basic.py`](../../learning_observer/learning_observer/auth/http_basic.py) |
| `auth.http_basic.full_site_auth` | Marks that nginx protects every route so middleware should expect auth headers on each request. | `false` | [`learning_observer/learning_observer/auth/http_basic.py`](../../learning_observer/learning_observer/auth/http_basic.py) |
| `auth.http_basic.delegate_nginx_auth` | Indicates that nginx performs the credential check; Learning Observer only trusts forwarded headers. | `false` | [`learning_observer/learning_observer/auth/http_basic.py`](../../learning_observer/learning_observer/auth/http_basic.py) |

### Background services and feature flags

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `feature_flags.*` | Optional feature toggles (`uvloop`, `watchdog`, `canvas_routes`, etc.). `True` enables a flag and allows nested configuration. | varies | [`learning_observer/learning_observer/settings.py`](../../learning_observer/learning_observer/settings.py) |

### Event stream authentication (`event_auth` namespace)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `event_auth.local_storage.userfile` | Path (under the data directory) listing device tokens that should be treated as authenticated. | required for `local_storage` | [`learning_observer/learning_observer/auth/events.py`](../../learning_observer/learning_observer/auth/events.py) |
| `event_auth.local_storage.allow_guest` | Permits unauthenticated fallbacks when the Chromebook or extension token is unknown. | `false` | [`learning_observer/learning_observer/auth/events.py`](../../learning_observer/learning_observer/auth/events.py) |
| `event_auth.http_basic` | Presence enables nginx-backed HTTP basic auth for event streams. No additional keys are required. | disabled | [`learning_observer/learning_observer/auth/events.py`](../../learning_observer/learning_observer/auth/events.py) |
| `event_auth.guest` | Enables guest sessions that mint random IDs for browsers without credentials. | disabled | [`learning_observer/learning_observer/auth/events.py`](../../learning_observer/learning_observer/auth/events.py) |
| `event_auth.hash_identify` | Enables hash-based identity hints (e.g., `/page#user=alice`) for one-off experiments. | disabled | [`learning_observer/learning_observer/auth/events.py`](../../learning_observer/learning_observer/auth/events.py) |
| `event_auth.testcase_auth` | Allows automated tests to tag events with deterministic user IDs. | disabled | [`learning_observer/learning_observer/auth/events.py`](../../learning_observer/learning_observer/auth/events.py) |

### Incoming events blacklist (`incoming_events` namespace)

| YAML path | Description | Default | Used in |
| --- | --- | --- | --- |
| `incoming_events.blacklist_event_action` | Action to take for incoming events (`TRANSMIT`, `MAINTAIN`, or `DROP`) when blacklist rules match. | `TRANSMIT` | [`learning_observer/learning_observer/blacklist.py`](../../learning_observer/learning_observer/blacklist.py) |
| `incoming_events.blacklist_time_limit` | Time limit to return when `blacklist_event_action` is `MAINTAIN` (`PERMANENT`, `MINUTES`, or `DAYS`). | `MINUTES` | [`learning_observer/learning_observer/blacklist.py`](../../learning_observer/learning_observer/blacklist.py) |

## Modules

Modules can define their own PMSS namespaces under `modules.<module_name>`.
Consult each module's reference guide for those settings - for example, the
Writing Observer module documents its configuration alongside the rest of its
module documentation.

## Example snippet

```yaml
run_mode: dev
hostname: localhost:8888
protocol: http
config:
  run_mode: dev
server:
  port: 8888
aio:
  session_secret: "replace-me"
  session_max_age: 3600
redis_connection:
  redis_host: localhost
  redis_port: 6379
  redis_password: null
```

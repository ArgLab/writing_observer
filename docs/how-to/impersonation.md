# Impersonating users

Learning Observer includes a lightweight impersonation flow so administrators can review dashboards and data as another user. The implementation relies on two HTTP routes that adjust the authenticated session and a Dash banner that surfaces the active impersonation.

## Start impersonating

The `start_impersonation` handler is protected by the `@learning_observer.auth.admin` decorator, so only administrators can trigger the flow. It accepts the target user ID as a path parameter and stores that identifier in the encrypted session under the `impersonating_as` key.

```
GET /start-impersonation/{user_id}
```

Once the route runs, the session entry looks like `{ "user_id": <target_user_id> }`, and any request that reads the active user from the session will treat this impersonated identity as the current user.

## Stop impersonating

The stop route clears the impersonation entry from the session.

```
GET /stop-impersonation
```

If no impersonation was active, the handler returns a message indicating that nothing changed.

## How impersonation affects user lookup

Whenever user information is needed during a request, `learning_observer.auth.utils.get_active_user` checks for the `impersonating_as` session entry first. When present, it returns the impersonated profile instead of the authenticated user stored under `user`. This makes downstream code unaware of whether a request is genuine or impersonated.

## Dash banner for impersonation state

Dash pages include a small banner at the top of the layout. On page load, `update_impersonation_header` reads the session from the underlying `aiohttp` request. When an impersonated user is present, the banner renders a label showing the impersonated identity and a “Stop” button that links to `/stop-impersonation`.

# Setting up LO Blocks with Canvas Integration

This guide walks you through integrating LO Blocks with Learning Observer and Canvas via LTI. This setup allows Canvas users to access LO Blocks dashboards while maintaining proper authentication and data flow between all three systems.

## Prerequisites

You'll need access to the following systems:

- **Learning Observer** - Base platform installation
- **LO Blocks** - Dashboard application
- **Canvas** - LMS instance with administrative rights

## Part 1: Canvas Configuration

### Initial Setup

1. **Sign in to Canvas** with administrative privileges

2. **Create test environment** (recommended for initial setup):
   - Create a sample course
   - Add sample students

   > **Note for local testing**: If running Canvas locally via Docker Compose:
   > - No email server is configured by default
   > - All "sent" emails print to the console
   > - You must find confirmation email URLs in the console when adding users

### Configure LTI Application

Follow the [detailed LTI configuration guide](https://learning-observer.readthedocs.io/en/latest/docs/how-to/lti.html) in our documentation.

Within Canvas, you'll want to:

1. Navigate to the Admin portal
2. Click `Developer Keys`, then click `+ Developer Key`
3. Select `LTI Key`
4. Populate the configuration
5. Save the key
6. Enable the key for use

> **Note**: You may need to revisit these settings after completing the Learning Observer configuration (see "Putting it all together" section below).

## Part 2: Learning Observer Configuration

### Base Installation

1. **Install Learning Observer** base platform using the [Tutorial: Install](../tutorials/install.md)

### Module Setup

2. **Create a module** to connect to a reducer:
   - [Tutorial: Build and Run a Module from the Cookiecutter Template](../tutorials/cookiecutter-module.md)
   - Match the `context` in your module to the `source` in your LO Event (see LO Blocks)
   - Add an endpoint in `COURSE_DASHBOARDS` defining the connection to the LO Blocks server

3. **Configure authentication**:
   - Set up password file login using `scripts/lo_passwd.py` (place the outputted file within the `learning_observer/` directory)

### Canvas Integration Settings

4. **Modify roster source settings**

   Edit `learning_observer/rosters.py` to update available PMSS values for `roster_source`.

   ```python
   pmss.parser('roster_source', parent='string', choices=['google', 'demo-canvas', 'schoology', 'all', 'test', 'filesystem'], transform=None)
   ```

5. **Update core settings** in your configuration:

   ```yaml
   auth:
     lti:
       demo-canvas:        # Allows users to sign in via LTI
   
   event_auth:
     lti_session:          # Allows websocket events from LTI-authenticated users
   
   feature_flags:
     canvas_routes: true   # Enables Canvas LTI API calls
   
   roster_data:            # See roster PMSS configuration below
   ```

   > **Important**: Replace `demo-canvas` with an identifier specific to your Canvas instance (e.g., `middleton-canvas`, `easttownhigh-canvas`)

6. **Create roster PMSS file** (`rosters.pmss`):

   ```pmss
   roster_data {
       source: all;
   }
   
   roster_data[provider="demo-canvas"] {
       source: demo-canvas;
   }
   ```

   Any user with the provider `demo-canvas` will use the roster source `demo-canvas` whereas the rest of the users will use rouster source equal to `all`.

7. **Register PMSS file** in `learning_observer/settings.py`:

   ```python
   pmss_settings = pmss.init(
       prog=__name__,
       description="A system for monitoring",
       epilog="For more information, see PMSS documentation.",
       rulesets=[
           pmss.YAMLFileRuleset(filename=learning_observer.paths.config_file()),
           pmss.PMSSFileRuleset(filename='rosters.pmss')
       ]
   )
   ```

**TODO**: Document any other settings needed "for data to flow properly" (referenced but incomplete in original document)

## Part 3: LO Blocks Configuration

1. **Configure websocket connection**

   Inside of `src/lib/state/store.ts` check the following:

   - `WEBSOCKET_URL` points to the Learning Observer instance
   - `websocketLogger` is included in our list of available `loggers`
   - Ensure the `lo_event.init` function uses the same source as defined in the reducer created earlier

2. **Build the application**:

   ```bash
   npx next build
   ```

3. **Start the application**:

   ```bash
   npx next start
   ```

## Part 4: Putting It All Together

### Understanding the Architecture

LO Blocks is a Next.js application with both client and server-side components. This means:

- We cannot serve it directly from Learning Observer (which requires static builds)
- We must run both applications side-by-side on the same machine
- We need a reverse proxy to route traffic between them

### Nginx Reverse Proxy Configuration

We'll use Nginx to route traffic between Learning Observer and LO Blocks.

#### Routing Strategy

- **Default traffic** → Learning Observer
- **`/lo-blocks` path** → LO Blocks application
- Users navigate to LO Blocks via a course dashboard link in Learning Observer

#### Step 1: Configure Next.js Base Path

Edit your `next.config.js` to set the base path:

```javascript
const nextConfig = {
    basePath: '/lo-blocks'
};

export default nextConfig;
```

Then rebuild LO Blocks:

```bash
npx next build
```

> **Important**: The `basePath` setting only affects `next/link` and `next/router`. It does NOT affect `fetch()` calls made by the application.

#### Step 2: Configure Nginx

Create an Nginx configuration to handle both applications:

```
upstream learning_observer {
    server localhost:8002;
}

upstream lo_blocks {
    server localhost:3000;
}

proxy_cache_path /var/cache/nginx/auth levels=1:2 keys_zone=auth_cache:10m max_size=100m inactive=60m;

map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 8001;
    server_name localhost;

    # Default: primary service
    location / {
        proxy_pass http://learning_observer;

        # WebSocket bits
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        # Common headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Cookie $http_cookie;
    }

    # 1) Next.js app mounted at /special-route
    # (this is essentially your original block; I only added a slash to the prefix
    # for clarity in matching deeper paths).
    location /special-route {
        # auth for anything under /special-route
        auth_request /auth-check;

        auth_request_set $user_id $upstream_http_x_user_id;
        auth_request_set $user_email $upstream_http_x_user_email;
        auth_request_set $user_name $upstream_http_x_user_name;

        proxy_pass http://lo_blocks;   # passes /special-route[...] as-is to Next
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header X-User-ID $user_id;
        proxy_set_header X-User-Email $user_email;
        proxy_set_header X-User-Name $user_name;

        proxy_set_header Authorization $http_authorization;
    }

    # 2) NEW: route /api/* -> Next's /special-route/api/*
    #
    # This is the key bit: we don't use 'rewrite' here, we let proxy_pass
    # do the path mapping via its trailing slash behavior.
    location /api/ {
        # Apply the same auth behavior as /special-route
        auth_request /auth-check;

        auth_request_set $user_id $upstream_http_x_user_id;
        auth_request_set $user_email $upstream_http_x_user_email;
        auth_request_set $user_name $upstream_http_x_user_name;

        # Map:
        #   /api/content         -> /special-route/api/content
        #   /api/foo/bar?x=1    -> /special-route/api/foo/bar?x=1
        proxy_pass http://lo_blocks/special-route/api/;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header X-User-ID $user_id;
        proxy_set_header X-User-Email $user_email;
        proxy_set_header X-User-Name $user_name;

        proxy_set_header Authorization $http_authorization;
    }

    # Internal location for auth checking
    location = /auth-check {
        internal;

        proxy_pass http://learning_observer/auth/userinfo;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header X-Original-URI $request_uri;

        proxy_set_header Authorization $http_authorization;
        proxy_set_header Cookie $http_cookie;

        proxy_cache auth_cache;
        proxy_cache_valid 200 5m;
        proxy_cache_key "$http_authorization$cookie_session";
    }

    location /auth/userinfo {
        proxy_pass http://learning_observer/auth/userinfo;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    error_page 401 403 = @auth_error;

    location @auth_error {
        return 401 '{"error": "Authentication required or user does not exist"}';
        add_header Content-Type application/json;
    }
}
```

The configuration should include:

- Proxy pass rules for Learning Observer (default)
- Proxy pass rules for `/lo-blocks` → LO Blocks
- **API fetch() workaround**: Rewrite `/api/*` requests to include the `/lo-blocks` prefix
  - This is necessary because Next.js `fetch()` calls don't respect `basePath`
  - Safe because Learning Observer doesn't use `/api` routes

> **Assumption**: LO Blocks runs on port 3000, Learning Observer runs on port 8002
> To change the Learning Observer port: Add `--port 8002` to the Makefile run command or adjust in `creds.yaml`

### HTTPS Configuration for Canvas

Canvas requires HTTPS for LTI integrations. For local development:

#### Option 1: Cloudflare Tunnel (Recommended for local testing)

1. **Create a secure tunnel**:

   ```bash
   cloudflared tunnel --url http://localhost:8001
   ```

   This creates a tunnel between your local port and a public HTTPS URL.

2. **Update configurations** with the tunnel URL:

   **In `creds.yaml`**:

   ```yaml
   hostname: your-tunnel-url.trycloudflare.com  # Without https://
   
   auth:
     lti:
       demo-canvas:
         redirect_uri: https://your-tunnel-url.trycloudflare.com/auth/lti/callback
   ```

   **In Canvas LTI configuration**:
   - Update all URL fields with the proper domain `https://your-tunnel-url.trycloudflare.com`
   - `target_link_uri: domain/lti/demo-canvas/login`
   - `oidc_initiation_url: domain/lti/demo-canvas/login`
   - `redirect_uris: domain/lti/demo-canvas/launch`

## Verification and Testing

Once everything is configured:

1. **Canvas → Learning Observer connection**:
   - Users should be able to launch the LTI tool from Canvas
   - Authentication should work via LTI

2. **Navigation to LO Blocks**:
   - Users should see the dashboard link in Learning Observer
   - Clicking should navigate to LO Blocks interface

3. **Data persistence**:
   - User progress in LO Blocks should save properly
   - Data flows through websocket connection to Learning Observer

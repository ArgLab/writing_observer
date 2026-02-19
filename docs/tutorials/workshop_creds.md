### creds.yaml

The `creds.yaml` is the primary configuration file on the system. The platform will not launch unless this file is present. Create a copy of the example in `learning_observer/learning_observer/creds.yaml.workshop`. We will copy this over, and then set up the pieces needed for the system to work.

You're welcome to run the `learning observer` between changes. In most cases, it will tell you exactly what needs to be fixed.

```bash
cp learning_observer/learning_observer/creds.yaml.workshop learning_observer/creds.yaml
```

#### User Authentication

As a research platform, the Learning Observer supports many authentication schemes, since it's designed for anything from small cognitive labs and user studies (with no log-in) to large-scale school deployments (e.g. integrating with Google Classroom). This is pluggable.

For this workshop, we will disable Google authentication, and set the system up so we can use it with with no authentication:

```yaml
auth:
    # remove google_oauth from auth
    # google_oauth: ...

    # enable passwordless insecure log-ins
    # useful for quickly seeing the system up and running
    test_case_insecure: true
```

#### Event authentication

Learning event authentication is seperate from user authentication. We also have multiple schemes for this, but for testing and development, we will run without authentication.

```yaml
# Allow all incoming events
event_auth:
    # ...
    testcase_auth: {}
```

#### Session management

Session management requires a unique key for the system. Type in anything (just make it complex enough):

```yaml
# update session information
aio:
    session_secret: asupersecretsessionkeychosenbyyou
    session_max_age: 3600
```

Pro tip: If you start the system missing a command like this, it will usually tell you what's wrong and how to fix it (in the above case, generating a secure GUID to use as your session secret).

#### KVS

```yaml
# If you are using Docker compose, you should change the redis host to
redis_connection:
  redis_host: redis
  redis_port: 6379
```

### admins.yaml & teachers.yaml

The platform expects both of these files to exist under `learning_observer/learning_observer/static_data/`. If these are missing on start-up, the platform create them for you and exit. Normally these are populated with the allowed Admins/Teachers for the system.

### passwd.lo

Each install of the system needs an admin password file associated with it. The `scripts/lo_passwd.py` file can be used to generate this password file. This does not have to be done in the same virtual environment as the main server. If you are using Docker, just create a local virtual environment to run this command.

```bash
python scripts/lo_passwd.py --username admin --password supersecureadminpassword --filename learning_observer/passwd.lo
```

Note that Learning Observer expects the file to be placed in the `learning_observer/` directory, similar to `creds.yaml`.

Depending on how the `creds.yaml` authorization settings are configured, you may be required to use the password you create.

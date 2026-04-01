# Configuring Multiple Roster Sources

This guide explains how to configure Learning Observer to load rosters from
multiple providers using [PMSS (Preference Management Style Sheets)](https://github.com/ETS-Next-Gen/pmss).

## 1. Define roster sources in PMSS

Create a PMSS file (for example `rosters.pmss`) that declares the roster sources
and the provider/domain specific overrides. The default rule selects `all`
roster data, while provider- and domain-specific rules replace that value when a
match is found.

```pmss
roster_data {
    source: all;
}

roster_data[provider="example-schoology"] {
    source: schoology;
}

/* Note that Canvas requires a slightly different source format */
roster_data[provider="example-canvas"] {
    source: example-canvas;
}

roster_data[domain="learning-observer.org"] {
    source: google;
}
```

Save the file alongside your configuration so that it can be referenced by the
application.

## 2. Load the PMSS ruleset in `settings.py`

Add the new PMSS file to the `pmss.init` call in `settings.py`. This loads both
the standard YAML configuration and the roster rules you just defined.

```python
# settings.py
pmss_settings = pmss.init(
    prog=__name__,
    description="A system for monitoring",
    epilog="For more information, see PMSS documentation.",
    rulesets=[
        pmss.YAMLFileRuleset(filename=learning_observer.paths.config_file()),
        pmss.PMSSFileRuleset(filename="rosters.pmss"),
    ],
)
```

> **Note:** The PMSS file path is currently hard-coded. Future work will make
> this discovery automatic.

## 3. Ensure roster sources are supported

Each roster source requires the associated integration to be configured:

- `google` requires Google OAuth credentials and callback URLs to be set up.
- `example-canvas` (and other Canvas instances) may need additional PMSS options to
  expose Canvas-specific configuration, such as API tokens and instance URLs.
- `schoology` requires the Schoology integration to be enabled and configured.

Verify that the necessary credentials and configuration options exist before
enabling a source.

## 4. Enable feature flags for roster routes

In the system settings, confirm that the relevant feature flags are enabled so the
system exposes the API routes for each provider. Flags follow the
`<provider>_routes` naming pattern, for example:

```yml
# creds.yaml
feature_flags: {google_routes, canvas_routes, schoology_routes}
```

These flags allow the application to access the provider-specific endpoints and
retrieve roster data.

## 5. Test with multiple contexts

Access the system through each supported context to verify that rosters appear
as expected:

- Sign in with Google to check the `google` roster data.
- Launch from Canvas via LTI to verify the `example-canvas` roster.
- Launch from Schoology to validate the `example-schoology` roster.

The user's session context (provider and domain) is evaluated in
`learning_observer/rosters.py` to choose the appropriate PMSS setting. As you
switch between providers, confirm that the roster displayed matches the source
specified in your PMSS configuration.

## 6. PMSS as a user-specific configuration tool

This setup demonstrates how PMSS can tailor settings per user or institution by
matching on provider and domain. While roster selection is the primary use case
now, the same approach can be extended to differentiate other settings for
specific audiences in the future.

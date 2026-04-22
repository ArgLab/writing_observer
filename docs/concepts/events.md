# Event Format

Our event format is inspired in part by IMS Caliper, xAPI/Tincan, and the edX
tracking log events. None of these standards are quite right for our
application, but several are close. They're pretty good standards!

## Limitations of Industry Formats

* **Verbosity.** Both Caliper and xAPI require a lot of cruft to be appended to
  events. For example, we have random GUIDs, URLs, and other redundancy on each
  event. Having a little bit of context (e.g. a header) or a little rationale
  (e.g. IDs which point into a data store) is sometimes good, but too much is a
  problem. With too much redundancy, events can get massive:
  * Our speed in handling large data scales with data size. Megabytes can be
    done instantly, gigabytes in minutes, and terabytes in hours. Cutting data
    sizes makes working with data easier.
  * Repeating oneself can lead to inconsistent data. Data formats where data
    goes in one place (or where redundancy is intentional and engineered for
    data correction) are more robust and less bug-prone.
* **Envelopes.** Caliper payloads are bundled in JSON envelopes. This is a
  horrible format because:
  * It results in a lot of additional parsing...
  * ... of very large JSON objects.
  * If there's an error or incompatibility anywhere, you can easily lose a
    whole block of data.
  * You can't process events in realtime, for example, for formative feedback.

Text files with one JSON event per line are more robust and more scalable:

* They can be processed as a stream, without loading the whole file.
* Individual corrupt events don't break the entire pipeline-you can skip bad
  events.
* They can be streamed over a network.
* They can be preprocessed without decoding. For example, you can filter a file
  for a particular type of event, student ID, or otherwise with a plain text
  search. The primary goal of first-stage preprocessing is simply to quickly cut
  down data size, so it doesn't need to reject 100% of irrelevant events.

* **Details.** In many cases, the details of a format are inappropriate for a
  given purpose. There are event types which are in neither Tincan/xAPI nor
  Caliper, and don't fit neatly into their frameworks. For example:
  * Formats specify timestamps with great precision, while coarse events (such
    as a student graduating) don't maintain that precision.
  * In one of our clients, events are generated without a user identifier, which
    is then added by the server once the user is authenticated. For these
    events, validation fails.
  * Related to the above, fields are sometimes repeated (e.g. client-side
    timestamp, server-side timestamp, and further timestamps as the event is
    processed by downstream systems). Much of this fits into security;
    downstream systems should not trust data from upstream systems. For example,
    a student shouldn't be able to fake submitting a homework assignment earlier
    than they did, and a school should not be able to backdate a state exam
    response.

There are similar minor mismatches for group events, very frequent events (such
as typing), and other types of events not fully anticipated when the standards
were created.

I'd like to emphasize that, in contrast to most industry formats, these are
quite good. They're not fundamentally broken.

## How We'd Like to Leverage Industry Formats

Fortunately, we don't need 100% compatibility for pretty good interoperability.
Our experience is that event formats are almost never interchangeable between
systems; even with standardized formats, the meaning changes based on the
pedagogical design. This level of compatibility is enough to give interoperability
without being constrained by details of these formats.

Our goal is to be compatible where convenient. Pieces we'd like to borrow:

* Critically, the universe has converged on events as JSON lines. This already
  allows for common data pipelines.
* We can borrow vocabulary-verbs, nouns, and similar.
* We can borrow field formats, where sensible.

With this level of standardization, adapting to data differences is typically
already less work than adapting to differences in underlying pedagogy.

## Where We Are

We have not yet done more careful engineering of our event format. Aside from a
JSON-event-per-line, the above level of compatibility is mostly aspirational.

## Incoming Event Flow

Incoming events reach the Learning Observer through `/wsapi/in/`, which
establishes a long-lived websocket for each client session. The websocket stream
is processed through a series of generators that progressively enrich and
validate each message before it reaches reducers.

1. **Initial decode and logging.** Every websocket frame is decoded by
   `event_decoder_and_logger`, which writes the raw payloads to per-session log
   files. When the Merkle feature flag is enabled, the same routine also commits
   events to the Merkle store using the configured backend. This stage ensures
   that we always have an immutable audit log of the stream.
2. **Lock fields and metadata.** Clients typically send a `lock_fields` event
   first to declare metadata such as the `source`, `activity`, or other
   immutable context. These fields are cached and injected into subsequent
   events so downstream reducers receive consistent metadata. Server-side
   metadata like IP and user agent is added separately via `compile_server_data`
   and cannot be spoofed by the client.
3. **Authentication.** The pipeline buffers events until
   `learning_observer.auth.events.authenticate` confirms the session. Successful
   authentication attaches the derived `auth` context-containing identifiers
   like the `user_id`-to each event before it continues. The websocket
   acknowledges authentication so the client can react if credentials are
   missing or invalid.
4. **Protection stages.** Events flow through guardrails that:
   * stop processing on an explicit `terminate` event and close the associated
     log files,
   * block sources that appear on the runtime blacklist, notifying the client
     when a block occurs, and
   * handle optional blob storage interactions (`save_blob` and `fetch_blob`)
     that reducers can request.
5. **Reducer preparation.** After authentication and metadata are in place we
   call `handle_incoming_client_event`. This builds a pipeline from the declared
   client `source`. Each source maps to a set of stream analytics modules that
   expose coroutine reducers. Reducers are partially applied with metadata
   (including the authenticated user) so they can maintain per-student state.
6. **Reducer execution.** Every canonicalized event passes through the prepared
   reducers. Events are logged a second time-now with server metadata and
   authentication context-and reducers update their internal state. If the
   reducer definitions change during a session (e.g. due to a hot reload in
   development) the pipeline is rebuilt on the next event.

This staged processing allows us to maintain separate concerns for logging,
authentication, safety checks, and analytics while keeping the event format
itself lightweight. Clients only need to agree on the JSON structure of events,
while the server handles durability and routing responsibilities on their
behalf.

## Configuring domain-based event blacklisting

Incoming events can be blacklisted through PMSS rules so that specific domains
either continue streaming, are told to retry later, or drop events entirely.
The `blacklist_event_action` setting controls the action and defaults to
`TRANSMIT`. Define rules under the `incoming_events` namespace and include a
`domain` attribute to scope the behavior per organization. When the action is
`MAINTAIN`, the `blacklist_time_limit` setting controls whether the client
should wait a short time or stop sending forever.

```pmss
incoming_events {
  blacklist_event_action: TRANSMIT;
}

incoming_events[domain="example.org"] {
  blacklist_event_action: DROP;
}

incoming_events[domain="pilot.example.edu"] {
  blacklist_event_action: MAINTAIN;
  blacklist_time_limit: DAYS;
}
```

When a client connects, the server extracts a candidate domain from the event
payload and uses it to resolve the `blacklist_event_action` setting. If
a rule returns `DROP`, the client is instructed to stop sending events.
`MAINTAIN` asks the client to retain events and retry after a delay (as defined
by `blacklist_time_limit`), while `TRANSMIT` streams events normally.

# Learning Observer Event Library

This is a module used to stream events into the Learning Observer (and, in the future, potentially other Learning Record Stores). This is in development. The requirements are:

- We would like to be able to stream events with multiple loggers.
  - In most cases, in practice, we use a websocket logger, with a persistent connection.
  - For occasional events, we support AJAX logging.
  - In addition, for ease-of-debugging, we can print events to the console
  - We are beginning to support a workflow with `react` integration, which provides for very good observability
- We follow the general format used in Caliper, xAPI, and Open edX of one JSON object per event
- We use a free-form JSON format, but encourage following Caliper / xAPI guidelines where convenient
- We currently support JavaScript, but would like to support other languages in the future

Examples of places where we intentionally diverge from standards:

- Good events are like onions -- they have layers. We don't assume we can e.g. trust timestamps or authentication from the system generating events, or that we will have all context up-front. Systems can add timestamps, authentication, and similar, much like e.g. SMTP messages being passed between systems. 
- We do need to have a header for metadata + authentication
- We'd like to be at least sensitive to bandwidth. It's not worth resending data with each event that can be in a header or in update events. A lot of standards have large, cumbersome events (which are not human-friendly, and expensive to store and process)
- We're a lot more freeform in what we send and accept, since learning contexts can be pretty rich (and technology evolves) in ways which standards don't always keep up with.

Our goal is to simplify compatibility and to maintain compliance where reasonable, but to be more flexible than strict compliance with xAPI or Caliper.

## Installation

This package will support browser-based events, Node, and Python.

However, before installing in either environment, we need to download the [xAPI](https://xapi.com/overview/) components. These components are used to determine the type of events being used.

```bash
cd xapi
./download_xapi_json.sh
```

### As a Node package

To use in a separate node project, such as the `/extension/writing_process`, you need to make the project available on your system.

```bash
npm install
npm link
```

Then from the other node project, run

```bash
npm link lo_event
```

*Note:* you may need to rerun `npm link lo_event` after you run `npm install` at the target location.

If this runs into issues, a more robust way is to run `npm pack` to create a tarball npm package, and then to `npm install` that package. This has the downside of requiring a reinstall on every change, which is somewhat cumbersome.

### As a Python package

Simply install the package as a normal python module.

```bash
pip install .
```

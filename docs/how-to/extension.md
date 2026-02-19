# Writing Observer Extension

The Writing Observer browser extension collects rich event data while a writer works in Google Docs so that the Learning Observer platform can analyse the writing process. The extension code lives in [`extension/writing-process/`](../../extension/writing-process/) and is packaged with [Extension CLI](https://oss.mobilefirst.me/extension-cli/) and webpack.

## Project Layout

The directory contains a standard Extension CLI project:

- `src/` - extension source files. Webpack writes the bundled content scripts and background bundles back into this directory as `*.bundle.js` files.
  - `writing.js` and `writing_common.js` run in the Google Docs page and capture keystrokes and context.
  - `background.js` and `service_worker.js` coordinate logging, open the websocket connection to Learning Observer, and respond to browser lifecycle events.
  - `pages/` stores the popup, options page, and other extension UI assets.
- `assets/` - icons used by the published extension.
- `webpack.config.js` - bundles the source code and excludes Node-specific dependencies required by the `lo-event` package.
- `test/` - placeholder for unit tests executed by the Extension CLI test runner.

## Prerequisites

- Node.js and npm (the project was last updated with Node 18.x, though later LTS versions should also work).
- Google Chrome for manual testing.
- Access to the [`lo-event`](../../modules/lo_event/) package, which provides messaging utilities that the extension uses to communicate with Learning Observer services.

## Install Dependencies

Install everything from inside the extension directory:

```bash
cd extension/writing-process
npm install
```

The `lo-event` dependency is declared as a `file:` package in `package.json`, so it is linked from the local repository when you install. If `npm install` cannot resolve it automatically, install it explicitly:

```bash
npm install ../../modules/lo_event
# or link it for iterative development
cd ../../modules/lo_event
npm link
cd -
npm link lo-event
```

## Everyday development tasks

Most workflows are exposed through npm scripts. Run them from `extension/writing-process/`.

### Bundle source files

Use webpack to generate the bundled scripts that the extension loads at runtime.

```bash
npm run bundle         # one-off build of background.js, writing.js, etc.
npm run bundle:watch   # continuously rebuild while editing
```

The bundles are written to `src/*.bundle.js`. Ensure these bundles exist before packaging the extension or running tests.

### Run the extension in development

Extension CLI can watch the project, rebuild on changes, and output an unpacked extension in `dist/`.

```bash
npm run ext:start          # Chrome/Chromium development build
```

Both commands keep watching the filesystem and rebuild when files change. Load the unpacked directory they produce (see [Loading the extension locally](#loading-the-extension-locally)).

### Run automated tests

```bash
npm run ext:test   # run the Extension CLI test suite
npm run coverage   # generate an lcov coverage report via nyc
```

The default tests under `test/` are minimal; extend them as new functionality is added.

### Clean build artefacts and generate docs

```bash
npm run ext:clean  # remove dist/
npm run ext:docs   # produce API docs in public/documentation/
npm run ext:sync   # refresh Extension CLI config files
```

Use these scripts before packaging to ensure the release contains only fresh bundles.

## Building for release

`npm run build` is the primary release command. It removes any existing `dist/` directory, builds the webpack bundles, and then invokes `ext:build`.

```bash
npm run build
```

After the command completes you will have:

1. `dist/` – the unpacked extension directory that can be loaded directly in Chromium-based browsers.
2. `release.zip` – an archive suitable for uploading to the Chrome Web Store or distributing manually.

You can also call the lower-level packaging commands when needed:

```bash
npm run ext:build          # Chrome release bundle only
```

## Loading the extension locally

1. Run `npm run build` (or `npm run ext:start`) to populate the `dist/` directory.
2. Navigate to `chrome://extensions/` in Chrome.
3. Enable **Developer mode** and click **Load unpacked**.
4. Select the `extension/writing-process/dist` directory.

## Deploying updates

- Upload the generated `release.zip` to the Chrome Web Store dashboard when publishing new versions.
- Update the `version` field in `src/manifest.json` to match the release number before packaging.
- If the Learning Observer websocket endpoint changes, update `WEBSOCKET_SERVER_URL` in `src/background.js` so that the extension sends analytics to the correct server.

## System design overview

The extension relies on two complementary streams of information:

- **Content scripts (`writing.js`, `writing_common.js`)** run inside Google Docs. They capture keystrokes, document metadata, and lifecycle events, and send structured messages to the background service worker.
- **Background/service worker (`service_worker.js`, `background.js`)** manages the analytics pipeline. It listens for messages from content scripts, observes Google Docs network requests (notably `save` and `bind` endpoints), and forwards data to Learning Observer via the `lo-event` logging framework. It activates only when a Google Docs tab has injected the content script to avoid unnecessary logging.

This design protects against frequent changes in Google Docs. The network listener provides redundancy when Google modifies the document structure, while the keystroke data keeps precise typing information.

## Maintaining compatibility with Google Docs

Google occasionally introduces changes that can disrupt the extension, especially around Manifest V3 requirements and Google Docs rendering updates. To reduce churn:

- Keep an eye on [Chrome extension updates](https://developer.chrome.com/docs/extensions/whatsnew/). Manifest-level changes (e.g. the MV2 &rarr; MV3 migration) often require updates to background scripts and permissions.
- When Google Docs changes its network endpoints, temporarily enable `RAW_DEBUG` in `src/background.js` to capture raw traffic and help reverse-engineer new request formats.
- Test the extension after major Google Docs updates to confirm that keystroke logging and document reconstruction still work as expected.

For deeper architectural details, consult the inline documentation within each source file in `extension/writing-process/src/`.

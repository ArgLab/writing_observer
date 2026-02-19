# Tutorial: Build and Run a Module from the Cookiecutter Template

This tutorial walks through generating a new Learning Observer module from the cookiecutter template, installing it, and seeing it run inside the system. We assume you already have the development environment installed and can start the stack with `make run`.

## 1. Prepare your environment

1. Activate the Python environment you use for Learning Observer development.
2. Make sure the `cookiecutter` command is available. If you have not installed it yet, run:

   ```bash
   pip install cookiecutter
   ```

3. From the repository root, change into the `modules/` directory:

   ```bash
   cd modules/
   ```

## 2. Generate a module from the template

1. Run cookiecutter against the Learning Observer template:

   ```bash
   cookiecutter lo_template_module/
   ```

2. Fill in the prompts with information for your module. At minimum you will supply:
   * **project_name** – Human-friendly title that appears in the UI.
   * **project_short_description** – A one-line summary shown with the module.
   * **reducer** – The name of the default reducer function the template creates.
3. Cookiecutter writes a new module directory inside `modules/`. If you entered `Revision Counter` as the name, the generated package would live in `modules/revision_counter/`.

The template scaffolds all of the pieces Learning Observer expects, including a reducer, Dash layout, entry points, and packaging configuration so the module can be installed like any other Python package. You'll find these generated files within `modules/<your-module>/`, including `module.py`, `reducers.py`, the Dash dashboard, and the accompanying `setup.cfg` that defines how the package is exposed.

## 3. Explore the generated code (optional but recommended)

1. Inspect `module.py` to see the metadata exposed to Learning Observer, the default execution DAG, reducer list, and Dash page configuration. The file lives in `modules/<your-module>/<project_slug>/module.py`.
2. Review `reducers.py` to understand how the template reducer counts events and where to extend it for your own analytics. You can find it next to `module.py` in the generated package directory.
3. Open `dash_dashboard.py` to learn how the generated layout publishes the reducer output on a Dash page. Use this as a starting point for your own visualizations.

   While you examine `module.py`, note that each reducer entry includes a
   `context` string. That value must match the `source` identifier the
   event producer sends on every message (for example the Google Docs
   extension reports `org.mitros.writing_analytics`). The stream
   analytics loader uses the pairing to dispatch events to the correct
   reducers. If you change the `context` in your module, be sure to
   update the emitting client so its `source` field matches—otherwise the
   reducer will never receive the events you expect.

## 4. Install the module in editable mode

Installing the module registers its entry point so Learning Observer can discover it. From the repository root run:

```bash
pip install -e modules/<your-module-directory>/
```

Replace `<your-module-directory>` with the directory created in step 2 (for example, `modules/revision_counter/`). The template’s `setup.cfg` already declares the `lo_modules` entry point that exposes `module.py` to the system, so no additional registration is required.

## 5. Start Learning Observer

1. Return to a terminal at the repository root.
2. Launch the stack:

   ```bash
   make run
   ```

3. Wait for the services to come up, then open `http://localhost:8888/` in a browser. Your new module should appear on the home screen because the template registers it as a course dashboard card by default inside `module.py`.

   The generated dashboard expects URL hash parameters (for example
   `#course_id=<id>`) so the client-side websocket helper
   knows which course to query. Navigating through the home page card
   fills these values in automatically. If you copy or bookmark the
   dashboard URL, make sure to keep the hash segment - without it the
   websocket connection will never send a query and the page will stay
   blank.

## 6. Stream sample data to exercise the module

To see live data, send synthetic writing events using the helper script.

1. Open a second terminal with your environment activated.
2. Run the streaming script from the repository root:

   ```bash
   python scripts/stream_writing.py --streams=5
   ```

   This sends five concurrent simulated students worth of Google Docs events to the default local endpoint using the helper found at `scripts/stream_writing.py`.
3. Refresh your browser. The default reducer counts incoming events, so you should see the totals increase on the Dash page included with the template. Both the reducer and the dashboard live alongside `module.py` in your generated package.

A common cause for missing data is having 0 reducer output available in storage. Check your [Key Value Store](../concepts/key_value_store.md) settings to assess how the reducer output is being stored.

## 7. Next steps

* Customize the reducer in `reducers.py` to compute the metrics your dashboard requires. See the [reducers concept overview](../concepts/reducers.md) for guidance.
* Expand the Dash layout to visualize your new metrics. The [dashboard how-to](../how-to/dashboards.md) walks through available UI patterns.
* Add additional reducers, exports, or pages to `module.py` as your module grows. Refer back to the [communication protocol concepts](../concepts/communication_protocol.md) when defining new DAG exports.

With these steps you have a working, template-based module running end-to-end inside Learning Observer. From here you can iterate on analytics and UI changes quickly by editing the generated files and reloading the server.

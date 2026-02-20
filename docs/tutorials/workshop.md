# Learning Observer Workshop

This document will step you through the Learning Observer workshop. Our goals for this workshop are:

* Give an overview of the platform
* Collect feedback on how to make the platform useful for your own work
* Collect feedback on different major components of the platform
* Have fun hacking learning analytics together

We recommend working in groups of three. This way:

* You can help each other
* At least one person will (hopefully) have a working machine

We suggest having at least **2 terminals** ready for this workshop. The first terminal will be for installing and running the system, while the second will be any additional scripts to need to run.

Prerequisites:

* Unix-style system
  * Ubuntu is most tested
  * MacOS should work as well, but is less tested
  * Windows should work with WSL, but you'll need to [install it beforehand](workshop/wsl-install.md).
* `python 3`. We tested and recommend 3.10 and 3.11, but anything newer than 3.9 should work

Recommendations:

* `virtualenvwrapper`. If you prefer a different package management system, you can use that instead.

Options:

* `redis`. We need a key-value store. However, if you don't have this, we can use files on the file system or in-memory. If you use `docker compose`, it will spin this up for you. Beyond this workshop, we strongly recommend using a `redis` (the recommended `redis` going forward is [ValKey](https://en.wikipedia.org/wiki/Valkey), as opposed to redis proprietary)
* `docker`. We're not big fans of `docker` for this type of work, so this pathway is less tested. However, by popularity, we do provide a `docker` option. We tested with docker 26.1. You should only use this if you're fluent in `docker`, since you'll probably need to tweak instructions slightly (especially if you're not on 26.1).

If you'd like to use `docker`, we have a quick [tutorial](docker.md).

If you can install the prerequisites before the workshop, it will save a lot of time, and not put us at risk of issues due to hotel bandwidth.

We have a document with a more in-depth overview of the [technologies](technologies.md) we use.

### Python environment

We recommend working in a Python environment of some sort. Our preferred tool is [virtualenvwrapper](https://pypi.org/project/virtualenvwrapper/). You are welcome to use your own (`anaconda`, or as you prefer). `virtualenvwrapper` lets you manage packages and dependencies without making a mess on your computer.

If you don't have a way of managing Python virtual environments, or would prefer to use `virtualenvwrapper`, we have a [short guide](workshop/workshop-virtualenv.md). *We strongly recommend working in some virtual environment, however*.

## Download

First make sure you clone the repository:

```bash
git clone https://github.com/ArgLab/writing_observer.git lo_workshop
```

**or**, if you have a github account properly configured with ssh:

```bash
git clone git@github.com:ArgLab/writing_observer.git lo_workshop
```

```bash
cd lo_workshop/
```

NOTE: All future commands should be ran starting from the repository's root directory. The command will specify if changing directories is needed.

## Local environment

Make sure you are on a fresh virtual environment. In `virtualenvwrapper`:

You can either run this

```bash
mkvirtualenv lo_workshop
workon lo_workshop
```

or run this to set up the virtual environment

```bash
python -m venv lo_workshop
source lo_workshop/bin/activate
```

Then run the install command:

```bash
pip install --upgrade pip # Probably not needed, but good form
make install
```

This will download required backpages. This might take a while, depending on hotel bandwidth.

## Configuration

Before starting the system, let's take care of any extra configuration steps. We are currently in the process of moving configuration formats from YAML to [PMSS](https://github.com/ETS-Next-Gen/pmss).

We may discuss this in the workshop later, but for now, we will configure using YAML.

We need a system configuration for this workshop. You can copy over this file with the command below, or you can make the changes yourself as per [these instruction](/docs/workshop_creds.md). In essence, the changes are:

1. Disable teacher authentication. We have pluggable authentication schemes, and we disable Google oauth and other schemes.
2. Disable learning event authentication. Ditto, but for incoming data.
3. Give a key for session management. This should be unique for security
4. Switch from redis to on-disk storage. We have pluggable databases. On-disk storage means you don't need to install redis.

Making these yourself is a good exercise. Note we are switching configuration formats, but the options will stay the same.

Copy the workshop `creds.yaml` file:

```bash
cp learning_observer/learning_observer/creds.yaml.workshop learning_observer/creds.yaml
```

If you have a file comparison tool like `meld`, it might be worth comparing our changes: `meld learning_observer/creds.yaml learning_observer/learning_observer/creds.yaml.example`

## Test the system

To run the system, use the run command

```bash
make run
```

*This does a lot of sanity checks on startup, and won't work the first time.* Rather, it will download required files, and create a file files (like `admins.yaml` and `teachers.yaml`, which are one way to define roles for teachers and admins on the system, but which we won't need for this workshop since we are using an insecure login). Once it is done, it will give you an opportunity to check whether it fixed issues correctly (we're working on having nice warnings, but we're not 100% of the way there). It did, so just run it again (perhaps 1-3 more times if it has more things to configure):

```bash
make run
```

You should be able to navigate to either `http://localhost:8888/`, `http://0.0.0.0:8888/`, or `http://127.0.0.1:8888/`, depending on your operating system, and see a list of courses and analytics modules. None are installed. We'll build one next!

## Build your own module

### Create from template

We provide a cookiecutter template for creating new modules for the Learning Observer. If you are using Docker, just create a local virtual environment to run this command. To create one run,

```bash
cd modules/
cookiecutter lo_template_module/
```

Cookiecutter will prompt you for naming information and create a new module in the `modules/` directory. By default, this is called `learning_observer_template`, but pick your own name and substitute it into the commands below.

### Installing

To install the newly created project, use `pip` like any other Python package.

```bash
pip install -e [name of your module]
```

Reload your web page, and you will see the new module. Click on it.

## Streaming Data

We can stream data into the system to simulate a classroom of students working. Once the system is up and running, open **a new terminal** and run

```bash
workon lo_workshop
python scripts/stream_writing.py --streams=10
```

To avoid cache issues, we recommend this order:

* Restart your server
* Run the above command
* Load the dashboard

This will generate events for 10 students typing a set of loremipsum texts and send them to the server. This will send event mimicking those from our Google Docs extension. You should see an event count in the template dashboard.

## Event Format

You can look at the format of these specific events in the `/learning_observer/learning_observer/logs/` directory. In the test system, we simply put events into log files, but we are gradually moving towards a more sophisticated, open-science, family-rights oriented data store (shown at the bottom of [this document](system_design.md). This is theoretically interesting, since it gives a cryptographically-verifiable way to audit what data was created and what analyses ran.

There are several good standards for [event formats](events.md), and to integrate learning data, we will need to support them all. Most of these have converged on a line of JSON per event, but the specifics are format-specific. We are including [some code](https://github.com/ArgLab/writing_observer/blob/master/modules/lo_event/lo_event/xapi.cjs) to help support the major ones. However, the events here are somewhat bound to how Google Docs thinks about documents.

## module.py

Have a quick look at the `module.py` file. This defines:

1. A set of reducers to run over event streams. These process data as it comes in. The context tells the system which types of events the reducers handle.
2. A set of queries for that data. These define calls dashboards can make into the system
3. A set of dashboards. `DASH_PAGES` are visible pages, and `COURSE_DASHBOARDS` will typically select a subset of those to show to teachers when they log in.

## reducers.py

Have a look at the `reducers.py` file. We define a simple reducer which simply counts events:

```python
@student_event_reducer(null_state={"count": 0})
async def student_event_counter(event, internal_state):
    '''
    An example of a per-student event counter
    '''
    state = {"count": internal_state.get('count', 0) + 1}

    return state, state
```

This function takes an event and updates a state. We will expand this in order to measure the median interval between the past 10 edits. This can be a poorman's estimate of typing speed. The function returns two parameters, one is an internal state (which might be a list of the timestamps of the past 10 events), and one is used for the dashboard (which might be the median value). We're planning to eliminate this in the future, though, and just have one state, so that's what we'll do here:

```python
import numpy

from learning_observer.stream_analytics.helpers import student_event_reducer

def median_interval(timestamps):
    if len(timestamps) < 2:
        return None

    deltas = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    deltas.sort()
    return int(numpy.median(deltas))


@student_event_reducer(null_state={"count": 0})
async def student_event_counter(event, internal_state):
    '''
    An example of a per-student event counter
    '''
    timestamp = event['client'].get('timestamp', None)
    count = internal_state.get('count', 0) + 1

    if timestamp is not None:
        ts = internal_state.get('timestamps', [])
        ts = ts + [timestamp]
        if len(ts) > 10:
            ts = ts[1:]
    else:
        ts = internal_state.get('timestamps', [])

    state = {
        "count": count,
        "timestamps": ts,  # We used to put this in internal_state
        "median_interval": median_interval(ts)  # And this in external_state
    }

    return state, state
```

Now, we have a typing speed estimator! It does not yet show up in the dashboard.

## Queries and communications protocol

In our first version of this system, we would simply compile the state for all the students, and ship that to the dashboard. However, that didn't allow us to make interactive dashboards, so we created a query language. This is inspired by SQL (with JOIN and friends), but designed for streaming data. It can be written in Python or, soon, JavaScript, which compile queries to an XML object.

In `module.py`, you see this line:

```python
EXECUTION_DAG = learning_observer.communication_protocol.util.generate_base_dag_for_student_reducer('student_event_counter', 'my_event_module')
```

This is shorthand for a common query which JOINs the class roster with the output of the reducers. The Python code for the query itself is [here](https://github.com/ArgLab/writing_observer/blob/berickson/workshop/learning_observer/learning_observer/communication_protocol/util.py#L58), but the jist of the code is:

```python
'roster': course_roster(runtime=q.parameter('runtime'), course_id=q.parameter("course_id", required=True)),
keys_node: q.keys(f'{module}.{reducer}', STUDENTS=q.variable('roster'), STUDENTS_path='user_id'),
select_node: q.select(q.variable(keys_node), fields=q.SelectFields.All),
join_node: q.join(LEFT=q.variable(select_node), RIGHT=q.variable('roster'), LEFT_ON='provenance.provenance.value.user_id', RIGHT_ON='user_id')
```

You can add a `print(EXECUTION_DAG)` statement to see the JSON representation this compiles to.

To see the data protocol, open up develop tools from your browser, click on network, and see the `communication_protocol` response.

In the interests of time, we won't do a deep dive here, but this is our third iteration at a query language, and we would love feedback on how to make this better.

## Dashboard framework

For creating simple dashboards, we use [dash](https://dash.plotly.com/) and [plotly](https://plotly.com/python/).

* These are rather simple Python frameworks for making plots and dashboards.
* Unfortunately, the code in the template module is still a bit complex. We're working to simplify it, but we're not there yet.

We'd suggest skimming a few example [visualizations](https://plotly.com/python/pie-charts/) to get a sense of what they do.

For now, though, all we want to do is add the intercharacter interval to our dashboard. Modify `dash_dashboard.py` to add a span for it:

```python
        html.Span(f' - {s["count"]} events'),
        html.Span(f' - {s.get("median_interval", 0)} ICI')
```

You should be able to see the intercharacter interval in a new span.

## Commit your changes

To avoid losing work, we recommend committing your changes now (and periodically there-after):

```bash
git add [directory of your module]
git commit -a -m "My changes"
```

## `react` dashboards

Behind the scenes, `dash` uses `react`, and if we want to go beyond what we can do with `plotly` and `dash`, fortunately, it's easy enough to build components directly in `react`. To see how these are build:

```bash
cd modules/lo_dash_react_components/
ls src/lib/components
```

And have a look at `LONameTag`. This component is used to show a student name with either a photo (if available in their profile) or initials (if not), and is used in the simple template dashboard. We have a broad array of components here, including:

- Various ways of visualizing what students know and can do. My favorite is a Vygotskian-style display which places concepts as either mastered, in the zone of proximal development (students can understand with supports), and ones students can't do at all
- Various tables and cards of student data
- Various ways of visualizing course content

We have many more not committed.

Getting this up-and-running can be a little bit bandwidth-intensive (since these are developed with `node.js`), but if hotel bandwidth suffices, in most cases, it is sufficent to run:

```bash
npm install
npm run build-css
npm run-script react-start
```

And then navigate to `http://localhost:3000`. *NOTE: The default URL is different. Ignore it.* If there is a lint error, ignore it as well.

Once set up, the development workflow here is rather fast, since the UX updates on code changes. Most of these are either early prototypes or designed to be used in specific contexts, but `LOStudentTable` and `ZPDPlot` look nice. So does `DAProblemDisplay`, if you scroll way down.

## Better data sources: `lo_event` and `lo_assess`

### `lo_event`

Our data streaming library is [lo_event](https://github.com/ArgLab/writing_observer/tree/master/modules/lo_event). This library is designed to stream events (typically) from a JavaScript client, and handles all of the complexity of things like persistance, queuing, and retries for you. Cookiecutter cde, but it should save you a bunch of time.

### `lo_assess`

Much more interesting, in development (and probably in need of renaming) is [`lo_assess`](https://github.com/ArgLab/writing_observer/tree/pmitros/loevent-v2/modules/lo_event/lo_event/lo_assess).

There is an XML format (based on edX OLX, which is in turn based on LON-CAPA XML) for creating interactives.

The very neat thing about this tool is that we *guarantee* that the state of the system at any point in time can be reconstructed from process data. The UX is controlled through React events, which are funneled into `lo_event`. You can see this using the time travel function of [Redux dev tools](https://github.com/reduxjs/redux-devtools). We've developed a handful of interactives in this format, including a GPT-powered graphic organizer, a Vygotskian-style dynamic assessment for middle school mathematics, but for this workshop, we have a little demo of a tool which can change text styles using ChatGPT for different audiences.

To see the format, see the XML inside of `modules/toy-assess/src/app/changer/page.js`. Right now, this is inside of a .jsx file, but it will be stand-alone XML in the near future.

Running this is a little bit involved, as you may need to configure Azure ChatGPT credentials (Azure provides better privacy compliance frameworks than using OpenAI directly):

```
export OPENAI_URL="https://[your-location].api.cognitive.microsoft.com"
export AZURE_OPENAI_ENDPOINT="https://[your-location].api.cognitive.microsoft.com"

export OPENAI_DEPLOYMENT_ID="[your-azure-deployment-id]"
export AZURE_OPENAI_DEPLOYMENT_ID="[your-azure-deployment-id]"

export OPENAI_API_KEY=`cat [your-azure-openai-key]`
export AZURE_OPENAI_API_KEY=`cat [your-azure-openai-key]`
```
(We don't require both, but it's handy if you switch libraries)

As an alternative, in `modules/toy-assess/src/app/lib/route.js` you can change the line

```
const listChatCompletions = openai.listChatCompletions;
```

To:

```
const listChatCompletions = stub.listChatCompletions;
```

Which will disable ChatGPT (and always give the same response).

At this point, you can run:
```
cd [base_dir]/modules/lo_event/
npm pack
cd [basedir]/modules/toy-assess/
# rm -Rf .next/cache/  # If necessary
npm install
npm install ../lo_event-0.0.1.tgz
npm run dev
```

And the server should be running on `localhost:3000`.

## `pmss`

We are creating a new settings format, based on css. This is called `pmss`. It works pretty well already. The basic idea is, like CSS, that we would like to be able to cascade settings. The core problem is that, like CSS, we want well-specified exceptions:

* "Our key-value store is local redis, except for schools in Australia, where our key-value store is hosted in Australia, to comply with local law"
* "We would like student rosters at JHS to come from Google Classroom, except for afterschool programs, which come from files on disk"

CSS gives a well-understood syntax for expressing these sorts of configurations, and will hopefully help us avoid the mess of special cases which evolve in most learning systems.

Note that this is a stand-alone library, and can be used in your own system too. That said, as with all code, it is still evolving, and we do not guarantee backwards-compatibility.

## Jupyter

We will not demo this, due to time constraints, but it is possible to run a Jupyter instance with access to our data store (see `ipython_integration.py`, `offline.py`, and `interactive_development.py`). We have means to monitor the communication between the python kernel and ipython/jupyter notebook. This should allow us to track all analyses which ran, either for family rights audits (how was my data used?) or open science audits (was there p-hunting?).

This is in the prototype stage; we are not yet using this for data analysis.

## Dev-ops

If you browse the devops directory, which has scripts in progress for
spinning up a cloud instance and managing flocks of _Learning
Observer_ instances.

## gitserve

The system can serve static content directly from a git repo. This allows us:

* Have a git hash for which version of static data we're using (and we do include this in cookies / logs!)
* Have branches (e.g. for AB tests or different uses)

Some of this can be configured as part of the creds.yaml file.

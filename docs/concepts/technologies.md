# Technologies in the _Learning Observer_

### Technologies


You are welcome to use your own instance of redis; however, `docker compose` allows us to spin up an instance of Redis and connect to it. See the Docker Compose section for more information.

The provided run commands all include watchdog turned on to ease development time on re-running the application.


Several potential contributors have asked for a list of technologies
needed to be productive helping developing the *Learning Observer* or
modules for the *Learning Observer*. A short list:

* We use [Python](https://www.python.org/) on the server side, and JavaScript on the client side. We do rely on current Python (dev systems are mostly 3.10 as of this writing).
* Since we're managing large numbers of web socket connections, we make heavy use of [asynchronous Python](https://docs.python.org/3/library/asyncio.html). If you haven't done async programming before, there is deep theory behind it. However, we again recommend any short tutorial for aiohttp, and then learning in context.
* Our web framework is [aiohttp](https://docs.aiohttp.org/en/stable/).
* We are moving towards [react](https://react.dev/) and [redux](https://redux.js.org/).
* Simple dashboards can be built with [plot.ly](https://plotly.com/python/)
* Our main database is the original [redis](https://redis.io/), but we plan to switch to a different redis due to licensing and other nasty changes by a company which coopted this from the open source community. We have a simple key-value store abstraction, so this is easy to swap out.
* We make heavy use of `git`, as well as of data structures which are `git`-like. I recommend reading [Git Internals](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
  and following [Write Yourself a Git](https://wyag.thb.lt/)
* Our CSS framework is currently [Bulma](https://bulma.io/), but that may change.
* Our icon library is [Font Awesome](https://fontawesome.com/)
* For rapid prototyping, we use [P5.js](https://p5js.org/), although we hope to avoid this beyond the prototype phase. This is super-easy to learn (even for little kids), and super-fast to develop in. It doesn't do to production-grade software, though (responsive, i18n, a11y, testability, etc.). The best way to learn this is by helping a child do the Khan Academy JavaScript courses :)
* Our web server is [nginx](https://nginx.org/en/), but that's easy to
  change.
* Our dev-ops framework is home baked, but uses [boto](http://boto.cloudhackers.com/), [invoke](https://www.pyinvoke.org/), [Fabric](https://www.fabfile.org/), and a
  little bit of [ansible](https://docs.ansible.com/ansible/latest/dev_guide/developing_python_3.html).
* We recommend Debian/Ubuntu, but run on Fedora/Red Hat. People have successfully run this on MacOS and on Windows/WSL, but this is not well-tested.
* At some point, we do plan do add [postgresql](https://www.postgresql.org/).
* For a while, when we thought we'd need queues, we used an XMPP server. I don't think we need queues, but if we do, it will come back.

For grad students, interns, student volunteers, and other contributors who are here primarily to learn: One of the fun things here is that most of these are _deeply interesting tools_ with a strong theoretical basis in their design.

On the whole, our goal is to keep a *small set of dependencies*. To add a new tool to the system, it will need to do something _substantially_ different than what's in the system already. We do plan on adding Postgresql once needed, but not too much beyond that.

Note that some modules within the system (including and especially the _Writing Observer_) do have more extensive dependencies. The _Writing Observer_ uses _a lot_ of different NLP libraries, and until we streamline that, can be quite annoying to install. 

# Deprecations

* We are deprecating [D3](https://d3js.org/) for displaying data in
  real-time on the client, and otherwise, as a front-end framework. D3
  is a relatively small and simple library with a fairly steep
  learning curve (in much the same way as Go is a small and simple
  game). Much of the use of this is obsoleted by our use of react.
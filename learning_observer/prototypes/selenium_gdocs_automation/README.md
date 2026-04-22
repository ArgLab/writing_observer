Front-end test infrastructure
=============================

It'd be great if we could do front-end testing. This is a prototype of
using Google Docs with [Selenium](https://www.selenium.dev/).

Conclusions:

1. Google plays a game of cat-and-mouse to prevent front-end
   automation. It's annoying. I presume this is to stop some kind of
   fraud. One might think Google would have better ways to shut
   down fraud, but in this case, Google chose to externalize costs
   onto customers.
2. People figure out work-arounds and Google shuts them down
3. The code, as committed, works right now, by using
   [undetected-chromedriver](https://pypi.org/project/undetected-chromedriver/).
4. But it's possible it will stop tomorrow.

Given the current size of the development team and the risk profile, I
decided not to throw more time into this right now. Joining the Google
cat-and-mouse game might make sense if/when the project expands.

.. Learning Observer documentation master file, created by
   sphinx-quickstart on Mon May  1 13:11:55 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Learning Observer
=================

Learning Observer is designed as an open source, open science learning
process data dashboarding framework. You write reducers to handle
per-student writing data, and aggegators to make dashboards. We've
tested this in math and writing, but our focus is on writing process
data.

At a high level, Learning Observer operates as an application platform:
the core :mod:`learning_observer` package boots the system, loads
configured modules, and manages shared data services, while each module
provides the specific dashboards, reducers, and other artifacts that
users interact with.

Our documentation is organized into four main categories, each serving a different purpose. You can explore them below:

- :doc:`Tutorials <tutorials>` - Step-by-step guides to help you learn by doing.
- :doc:`Concepts <concepts>` - Explanations of key ideas and background knowledge.
- :doc:`How-To <how-to>` - Practical instructions to solve specific goals.
- :doc:`Reference <reference>` - Detailed API/configuration information.

.. toctree::
   :hidden:
   :maxdepth: 3

   tutorials
   concepts
   how-to
   reference

Additional Information
----------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

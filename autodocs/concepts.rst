Concepts
=============

Explanations of key ideas, principles, and background knowledge.
Follow this recommended sequence to build context before diving into
implementation details:

- :doc:`History <docs/concepts/history>` - establishes the background and
  problem space the project is addressing.
- :doc:`System Design <docs/concepts/system_design>` - explains how the product
  strategy and user needs translate into an overall system approach.
- :doc:`Architecture <docs/concepts/architecture>` - outlines the concrete
  architecture that implements the system design.
- :doc:`Technologies <docs/concepts/technologies>` - surveys the primary tools
  and platforms we rely on to realize the architecture.
- :doc:`System Settings <docs/concepts/system_settings>` - describes how the
  system loads global and cascading settings.
- :doc:`Events <docs/concepts/events>` - introduces the event model that drives
  data flowing through the system.
- :doc:`Reducers <docs/concepts/reducers>` - details how incoming events are
  aggregated into the state our experiences depend on.
- :doc:`Communication Protocol <docs/concepts/communication_protocol>` - discusses how
  the system queries data from reducers for dashboards.
- :doc:`Student Identity Mapping <docs/concepts/student_identity_mapping>` - explain
  how learners information is mapped across integrations.
- :doc:`Scaling <docs/concepts/scaling>` - covers strategies for growing the
  system once the fundamentals are in place.
- :doc:`Auth <docs/concepts/auth>` - describes authentication considerations
  that secure access to the system.
- :doc:`Privacy <docs/concepts/privacy>` - documents how we protect learner data
  and comply with privacy expectations.

.. toctree::
   :hidden:
   :maxdepth: 1
   :titlesonly:

   docs/concepts/history
   docs/concepts/system_design
   docs/concepts/architecture
   docs/concepts/technologies
   docs/concepts/system_settings
   docs/concepts/events
   docs/concepts/reducers
   docs/concepts/communication_protocol
   docs/concepts/student_identity_mapping
   docs/concepts/scaling
   docs/concepts/auth
   docs/concepts/privacy

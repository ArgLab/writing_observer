# Learning Observer GPT

This module allows users make queries to a GPT model.

This code is abstracted directly from the `wo_bulk_essay_analysis` module and should be treated as scaffolding as we determine the appropriate way to use query GPT responders.

## Long-term goals / Future work

### General Design

Currently the GPT responders are using an Object Oriented approach which clashes with much of Learning Observer's design. We ought to change this from an OO approach to a Functional Programming approach.

### Querying Responders

This package currently initializes a single GPT responder for use. In practice, we need to keep track of multiple responders depending on the context/use case. The different responders ought to be defined and queried via PMSS like

```css
.wo .group_a {
  gpt_responder: openai;
  model: gpt-4o;
  temperature: 0.5;
}

.dynamic-assessment {
  gpt_responder: ollama;
  ollama_server: http://my-ollama-server.learning-observer.org/
}

[school=ncsu] {
   open_ai_creds: [NCSU-billed account]
}

// ... and so on
```

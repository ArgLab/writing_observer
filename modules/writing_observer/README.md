# Writing Observer

**Last updated:** September 30th, 2025

The Writing Observer module wraps the NLP and feedback services that power Writing Observer features. It exposes a consistent interface for:

* generating writing indicators from the Analytics for Writing Evaluation (AWE) stack, see [AWE Workbench](https://github.com/ETS-Next-Gen/AWE_Workbench)
* surfacing grammar and usage issues through LanguageTool
* forwarding communication protocol queries to GPT-based responders

This document explains how to configure the module and reuse individual components inside another system.

## Quick Start

1. Ensure the module is installed in your environment `pip install modules/writing_observer`.
2. Configure module level settings in `creds.yaml` (see the next section).
3. Import the module into your project and call the service(s) you require.

> The module is designed so that any feature can be toggled on or off. This lets you reuse only the pieces that are available in your deployment environment.

## Configuration (`creds.yaml`)

Below is a representative configuration block. Any unspecified key falls back to the documented default value.

## Config (`creds.yaml`)

```yaml
modules:
  writing_observer:
    use_nlp: false
    use_google_documents: false
    use_languagetool: false
    languagetool_host: http://localhost
    languagetool_port: 8081
    verbose: false
    gpt_responders:
      ollama:
        model: llama2
        host: http://localhost:11434
      openai:
        model: gpt-3.5-turbo-16k
        api_key: your-secret-key
```

### Top-level flags

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `use_nlp` | bool | `false` | Enable AWE NLP indicators such as parts of speech, main idea detection, and academic language metrics. |
| `use_google_documents` | bool | `false` | Sync reconstructed reducer state with a Google Doc using the Google Docs API. |
| `use_languagetool` | bool | `false` | Run LanguageTool analysis on submitted text. |
| `verbose` | bool | `false` | Log reducer state whenever it updates (useful when debugging pipelines). |

### LanguageTool options

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `languagetool_host` | str | `http://localhost` | Host URL for the LanguageTool server. |
| `languagetool_port` | int | `8081` | Port on which LanguageTool is available. |

Set `use_languagetool` to `true` only when LanguageTool is reachable at the configured host and port.

### GPT responders

The `gpt_responders` object declares one or more providers. The system iterates over the responders in the order they appear and selects the first one that is correctly configured. This allows you to offer fallbacks (for example, try a local Ollama instance before hitting OpenAI).

Currently supported responders:

#### Ollama

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | str | `llama2` | Model name served by the Ollama runtime. |
| `host` | str | `http://localhost:11434` | Base URL of the Ollama server. You can also supply this via the `OLLAMA_HOST` environment variable. |

#### OpenAI

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | str | `gpt-3.5-turbo-16k` | Chat completion model to call. |
| `api_key` | str | _(required)_ | Secret API key for your OpenAI account. You can also provide it through the `OPENAI_API_KEY` environment variable. |

## Feature-by-feature guidance

### NLP indicators (AWE)

1. Set `use_nlp: true` in the configuration.
2. Ensure the AWE libraries are installed and accessible from the runtime environment.
3. Call the relevant reducers or service functions to compute indicators such as parts-of-speech counts or academic language percentages.

These indicators are useful for automated writing evaluation and can be combined with LanguageTool or GPT feedback.

### Google Docs synchronization

Enable `use_google_documents` when you want the module to keep a Google Doc up to date with reconstructed reducer state. You must supply Google API credentials in the broader system configuration (outside the scope of this document).

### LanguageTool error detection

1. Run or connect to a LanguageTool server.
2. Configure `languagetool_host` and `languagetool_port`.
3. Set `use_languagetool: true`.

The module will then enrich reducer output with spelling and usage error information, which can be displayed directly to writers or incorporated into other feedback flows.

### GPT-based feedback

1. Add one or more entries to `gpt_responders` (see tables above).
2. Provide any required credentials via configuration or environment variables.
3. Enable the module feature or reducer that consumes GPT responses (for instance, conversational feedback or revision suggestions).

## Tips for integration

* Toggle features gradually during development to keep dependencies manageable.
* Use the `verbose` flag while integrating new reducers to observe state transitions and diagnose issues.
* Keep secrets (such as API keys) out of version control by relying on environment variables or secret management tooling.
* When deploying in containers, expose the LanguageTool and Ollama ports to the module runtime.

## Further resources

* [LanguageTool server documentation](https://dev.languagetool.org/http-server)
* [Ollama documentation](https://docs.ollama.ai/)
* [OpenAI API reference](https://platform.openai.com/docs/)

These resources provide additional setup instructions and troubleshooting guides for the third-party services referenced above.

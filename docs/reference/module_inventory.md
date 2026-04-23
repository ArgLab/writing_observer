# Module Inventory

This page is a quick-reference inventory of modules/packages in this monorepo:
what they are and what they do.

## Current modules at a glance

### Common modules

| Module | What it does |
| --- | --- |
| `lo_dash_react_components` | Shared custom Dash UI components used across dashboards. |
| `lo_gpt` | Shared interfaces/utilities for accessing LLMs. |
| `lo_template_module` | Cookiecutter template used to scaffold new Learning Observer modules. |

### Additional module

| Module | What it does |
| --- | --- |
| `ccss` | Common Core State Standards-related package/resources. |

### Writing-focused modules

| Module | What it does |
| --- | --- |
| `portfolio_diff` | Next.js code for the portfolio dashboard UI. |
| `wo_classroom_text_highlighter` | Classroom text highlight dashboard module. |
| `wo_bulk_essay_analysis` | Classroom dashboard for bulk essay analysis (LLM-assisted workflows). |
| `wo_portfolio_diff` | Learning Observer entrypoint module for the built/deployed `portfolio_diff` dashboard. |
| `writing_observer` | Core writing-process analytics module and integrations. |

### Unused / superseded modules

| Module | Current state |
| --- | --- |
| `language_tool` | Standalone module is not actively used; relevant functionality now lives in `writing_observer`. |
| `websocket_debug` | Standalone module is not actively used; websocket debugging is mostly handled by scripts in `scripts/`. |

### Prototype modules

| Module | What it does | Current status |
| --- | --- | --- |
| `lo_action_summary` | Dashboard listing student events/actions. | Prototype. |
| `lo_lti_grade_demo` | Demo for LTI grade submission and reading flow. | Prototype/demo. |
| `lo_event` | Event-focused module (includes Next.js dashboard component work). | Moved to its own repository. |
| `toy-assess` | Initial LO Blocks implementation. | Being phased out (still used in some studies). |
| `lo_toy_sba` | Save/load state module used primarily with `toy-assess` + `lo_event`. | Prototype support module. |

### Legacy prototype dashboards (not fully migrated)

When the communication protocol changed to an async-generator pattern, some
prototype dashboards were not migrated.

| Module | What it does | Note |
| --- | --- | --- |
| `wo_common_student_errors` | Aggregate classroom LanguageTool dashboard. | Legacy prototype; may be folded into newer dashboard patterns. |
| `wo_document_list` | Toy dashboard showing documents across students. | Legacy prototype. |
| `wo_highlight_dashboard` | Initial highlight dashboard implementation. | Superseded by newer highlight work. |

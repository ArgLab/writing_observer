# Student Identity Mapping

This document describes the current approach for reconciling a student's identity across the Google Workspace context used by Writing Observer and external platforms that only surface an email address (for example when the application is launched as an LTI tool).

## Why the mapping exists

When Writing Observer runs inside Google Workspace we naturally have access to the Google user identifier that shows up in event payloads. However, when the product is embedded as an LTI application we receive the learner's email address but do not receive the Google identifier. Many downstream reducers and dashboards expect to look students up by the Google identifier that is emitted by Google Docs events. Without an explicit bridge between those two identifiers we would be unable to join activity data with roster or profile information for LTI launches.

## Data sources involved

Two pieces of infrastructure cooperate to keep an email-to-Google-ID lookup table available:

1. **`student_profile` reducer** – The `student_profile` KVS pipeline in `writing_analysis.py` stores the latest email address and Google identifier (`safe_user_id`) observed for each student. The reducer only updates its state when either value changes. The resulting records live in the reducer's internal key-value namespace and therefore need to be copied to a place where other services can access them. 【F:modules/writing_observer/writing_observer/writing_analysis.py†L233-L253】
2. **`map_emails_to_ids_in_kvs.py` script** – This maintenance script scans the reducer's internal keys, extracts any records that contain both `email` and `google_id`, and writes a dedicated `email-studentID-mapping:{email}` entry to the key-value store. The explicit mapping gives any service that only knows the email address a way to recover the Google identifier. 【F:scripts/map_emails_to_ids_in_kvs.py†L1-L29】

This flow is intentionally simple: the reducer captures whatever the client reports, and the script copies the data to keys that other components already know how to query.

## Operating the script

The email mapping script is normally run in the same environment as other KVS maintenance tasks. It requires access to the same credentials file that the main server use. Thus, we need to run the script from the `learning_observer` directory. A manual run looks like this:

```bash
cd learning_observer/
python ../scripts/map_emails_to_ids_in_kvs.py
```

The script performs a full scan every time it runs, so it is safe to execute multiple times or to schedule as a recurring job.

## Limitations and future direction

The current reducer-plus-script approach fills an immediate gap but remains a stopgap solution:

* **Tight coupling to Google identity** – The reducer only records the Google identifier surfaced by Google Docs. If we ingest events from another platform, there is no canonical place to persist its identifiers.
* **No user object abstraction** – Each consumer must know which KVS keys to query. A shared user object (or identity service) would allow the system to attach multiple external identifiers, roles, and profile attributes to a learner and to expose them through a stable API.
* **Operational overhead** – Because the mapping lives in the KVS, we must remember to run the maintenance script anywhere we expect the lookup table to be fresh.

In the future we plan to introduce a formal user object that encapsulates identifiers, roles, and cross-system metadata. That abstraction would make this lookup process unnecessary by giving every component a single source of truth for student identity. Until then, this document serves as a reference for the current mapping workflow.

# Prompt History & AI Collaboration Log

### 1. Architecture & Schema Design Prompt
* **Prompt**: "Draft a relational schema and data dictionary for an omnichannel customer support ticket router handling email, chat, and phone across agents with specific skills, concurrency limits, and operating calendars."
* **AI Output Summary**: Provided core entities (Ticket, Agent, SLAEvent, etc.).
* **Human Review & Modifications**: Added bridge relationship structures, zero-padded deterministic ID nomenclature (`TKT-2026-000001`, `ASN-TKT-001`), and explicitly isolated ground-truth labels from input feature tables.

### 2. Business Logic & Anomaly Generation Prompt
* **Prompt**: "Write Python routines implementing business-hour SLA math and inject 5 specific labelled anomalies (capacity overflow, transfer loop, calendar bypass, safety mismatch, reopen loss)."
* **AI Output Summary**: Provided skeleton generator code.
* **Human Review & Modifications**: Reconciled the weekday calculation logic to prevent infinite calendar loops, enforced fixed PRNG seeding, and integrated pytest suites to confirm zero checksum deviations between duplicate runs.
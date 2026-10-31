# Enterprise Omnichannel Case Routing Data Dictionary

### 1. Customer
* `customer_id` (VARCHAR, PK): Deterministic ID format `CUST-000001`.
* `tier` (VARCHAR, Required): `STANDARD`, `PREMIUM`, `VIP`.
* `preferred_language` (VARCHAR, Required): ISO 639-1 code (`en`, `es`, `fr`, `de`).

### 2. Channel
* `channel_id` (VARCHAR, PK): `EMAIL`, `CHAT`, `PHONE`.
* `calendar_type` (VARCHAR, Required): `BUSINESS_HOURS` (9 AM - 5 PM Mon-Fri) or `24_7`.

### 3. Intent
* `intent_id` (VARCHAR, PK): E.g., `INT-BILLING`, `INT-TECHNICAL`, `INT-GENERAL`.
* `default_urgency` (VARCHAR, Required): `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
* `required_skill_id` (VARCHAR, FK -> Skill.skill_id).

### 4. Agent
* `agent_id` (VARCHAR, PK): Deterministic ID format `AGT-000001`.
* `max_capacity` (INTEGER, Required): Max concurrent slots (e.g., Phone=1, Email=5, Chat=3).
* `active_shift` (VARCHAR, Required): `DAY`, `NIGHT`, `SWING`.

### 5. Ticket
* `ticket_id` (VARCHAR, PK): Format `TKT-2026-000001`.
* `customer_id` (VARCHAR, FK -> Customer.customer_id).
* `channel_id` (VARCHAR, FK -> Channel.channel_id).
* `intent_id` (VARCHAR, FK -> Intent.intent_id).
* `language` (VARCHAR, Required): Case language.
* `urgency` (VARCHAR, Required): `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
* `calculated_priority` (INTEGER, Required): 1 (Critical) to 4 (Low).
* `current_status` (VARCHAR, Required): `NEW`, `ASSIGNED`, `RESOLVED`, `CLOSED`, `REOPENED`.
* `created_at` (TIMESTAMP, Required): ISO 8601 string.
* `sla_deadline` (TIMESTAMP, Required): Derived SLA target timestamp.

### 6. Message
* `message_id` (VARCHAR, PK): Format `MSG-<ticket-id>-001`.
* `ticket_id` (VARCHAR, FK -> Ticket.ticket_id).
* `sender_type` (VARCHAR, Required): `CUSTOMER` or `AGENT`.
* `content` (TEXT, Required): Message body.
* `created_at` (TIMESTAMP, Required): ISO 8601 string.

### 7. AssignmentEvent
* `assignment_id` (VARCHAR, PK): Format `ASN-<ticket-id>-001`.
* `ticket_id` (VARCHAR, FK -> Ticket.ticket_id).
* `agent_id` (VARCHAR, FK -> Agent.agent_id).
* `event_type` (VARCHAR, Required): `INITIAL_ROUTING`, `TRANSFER`, `ESCALATION`, `CAPACITY_BREACH_FORCED`.
* `assigned_at` (TIMESTAMP, Required).

### 8. SLAEvent
* `sla_event_id` (VARCHAR, PK): Format `SLA-<ticket-id>`.
* `ticket_id` (VARCHAR, FK -> Ticket.ticket_id).
* `target_minutes` (INTEGER, Required): Calculated target window.
* `actual_minutes` (INTEGER, Optional): Time taken to resolve.
* `is_breached` (BOOLEAN, Required): True if actual > target.

### 9. Resolution
* `resolution_id` (VARCHAR, PK): Format `RES-<ticket-id>`.
* `ticket_id` (VARCHAR, FK -> Ticket.ticket_id).
* `resolved_at` (TIMESTAMP, Required).
* `csat_score` (INTEGER, Optional): 1 to 5 customer score.

### 10. GroundTruthAnomaly
* `anomaly_id` (VARCHAR, PK): Format `ANOM-00001`.
* `entity_id` (VARCHAR, FK -> Ticket.ticket_id).
* `anomaly_type` (VARCHAR, Required): Identifies deliberate negative test scenarios.
* `description` (TEXT, Required): Diagnostic label.
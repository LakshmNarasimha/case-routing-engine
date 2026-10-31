# Omnichannel Case Routing Engine & Synthetic Data Pipeline

An enterprise-grade routing system and deterministic synthetic event generator modeling omnichannel customer support operations, skill/capacity-based dispatching, business-calendar SLA calculation, and ground-truth anomaly injection.

## Features
* **Deterministic Reproducibility**: Fixed seed generation ensures byte-identical CSV outputs.
* **Omnichannel Routing**: Matches cases on agent skills, languages, active channels, and capacity quotas.
* **Explicit Event Sourcing**: Tracks ticket lifecycle, agent assignments, transfers, and escalations.
* **Isolated Ground-Truth Labels**: Edge-case anomalies are logged in `ground_truth.csv` without leaking into transaction tables.

## Setup & Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
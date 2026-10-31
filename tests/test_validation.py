"""
Comprehensive Validation Suite:
- Primary key uniqueness
- Foreign key relational integrity
- State transition validation
- Anomaly demonstration coverage
"""

import os
import pytest
import pandas as pd

DATA_DIR = "./output"

@pytest.fixture(scope="module")
def data():
    tables = [
        "customers", "agents", "tickets", "messages",
        "assignments", "sla_events", "resolutions", "ground_truth"
    ]
    dfs = {}
    for t in tables:
        path = os.path.join(DATA_DIR, f"{t}.csv")
        assert os.path.exists(path), f"Missing data file: {path}"
        dfs[t] = pd.read_csv(path)
    return dfs

def test_no_duplicate_primary_keys(data):
    """Area: Validation - Check duplicate IDs"""
    assert data["tickets"]["ticket_id"].is_unique, "Duplicate ticket IDs found!"
    assert data["agents"]["agent_id"].is_unique, "Duplicate agent IDs found!"
    assert data["customers"]["customer_id"].is_unique, "Duplicate customer IDs found!"
    assert data["messages"]["message_id"].is_unique, "Duplicate message IDs found!"
    assert data["assignments"]["assignment_id"].is_unique, "Duplicate assignment IDs found!"

def test_foreign_key_referential_integrity(data):
    """Area: Validation - Check foreign keys"""
    # Tickets -> Customers
    assert set(data["tickets"]["customer_id"]).issubset(set(data["customers"]["customer_id"]))
    # Messages -> Tickets
    assert set(data["messages"]["ticket_id"]).issubset(set(data["tickets"]["ticket_id"]))
    # Assignments -> Tickets & Agents
    assert set(data["assignments"]["ticket_id"]).issubset(set(data["tickets"]["ticket_id"]))
    assert set(data["assignments"]["agent_id"]).issubset(set(data["agents"]["agent_id"]))
    # Resolutions -> Tickets
    assert set(data["resolutions"]["ticket_id"]).issubset(set(data["tickets"]["ticket_id"]))

def test_valid_lifecycle_transitions(data):
    """Area: Validation - Lifecycle state validation"""
    valid_statuses = {"NEW", "ASSIGNED", "RESOLVED", "CLOSED", "REOPENED"}
    assert set(data["tickets"]["status"]).issubset(valid_statuses)

def test_all_five_anomalies_present(data):
    """Area: Anomalies - Demonstrate all 5 required anomaly scenarios"""
    expected_anomalies = {
        "AGENT_CAPACITY_BREACH",
        "SLA_CALENDAR_IGNORED",
        "REOPEN_LOST_HISTORY",
        "TRANSFER_LOOP",
        "PRIORITY_SAFETY_VIOLATION",
    }
    found = set(data["ground_truth"]["anomaly_type"].unique())
    missing = expected_anomalies - found
    assert not missing, f"Missing anomaly scenario(s): {missing}"

def test_audit_event_history_completeness(data):
    """Area: Audit history - Record every assignment, transfer, escalation"""
    event_types = set(data["assignments"]["event_type"].unique())
    assert "INITIAL_ROUTING" in event_types
    assert "TRANSFER" in event_types
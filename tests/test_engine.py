"""Automated Verification Suite for Routing Logic and Synthetic Datasets."""

import os
import pytest
import pandas as pd
from run import run_pipeline, compute_sha256


@pytest.fixture(scope="session")
def generated_data(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("test_output")
    run_pipeline(scale="starter", output_dir=str(tmp_dir), seed=20261022)
    tables = {}
    for name in [
        "customers",
        "agents",
        "tickets",
        "messages",
        "assignments",
        "sla_events",
        "resolutions",
        "ground_truth",
    ]:
        tables[name] = pd.read_csv(os.path.join(tmp_dir, f"{name}.csv"))
    return tables, str(tmp_dir)


def test_primary_key_uniqueness(generated_data):
    tables, _ = generated_data
    assert tables["customers"]["customer_id"].is_unique
    assert tables["agents"]["agent_id"].is_unique
    assert tables["tickets"]["ticket_id"].is_unique
    assert tables["messages"]["message_id"].is_unique
    assert tables["assignments"]["assignment_id"].is_unique
    assert tables["sla_events"]["sla_event_id"].is_unique


def test_foreign_key_integrity(generated_data):
    tables, _ = generated_data
    valid_customer_ids = set(tables["customers"]["customer_id"])
    valid_ticket_ids = set(tables["tickets"]["ticket_id"])
    valid_agent_ids = set(tables["agents"]["agent_id"])

    assert set(tables["tickets"]["customer_id"]).issubset(valid_customer_ids)
    assert set(tables["messages"]["ticket_id"]).issubset(valid_ticket_ids)
    assert set(tables["assignments"]["ticket_id"]).issubset(valid_ticket_ids)
    assert set(tables["assignments"]["agent_id"]).issubset(valid_agent_ids)
    assert set(tables["sla_events"]["ticket_id"]).issubset(valid_ticket_ids)


def test_ground_truth_isolation(generated_data):
    tables, _ = generated_data
    gt = tables["ground_truth"]
    assert len(gt) > 0
    assert set(gt["anomaly_type"]).issubset(
        {
            "AGENT_CAPACITY_BREACH",
            "SLA_CALENDAR_IGNORED",
            "REOPEN_LOST_HISTORY",
            "TRANSFER_LOOP",
            "PRIORITY_SAFETY_VIOLATION",
        }
    )
    assert "anomaly_type" not in tables["tickets"].columns
    assert "is_anomaly" not in tables["assignments"].columns


def test_deterministic_reproducibility(tmp_path):
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    run_pipeline(scale="starter", output_dir=str(dir1), seed=20261022)
    run_pipeline(scale="starter", output_dir=str(dir2), seed=20261022)

    for file in ["tickets.csv", "assignments.csv", "ground_truth.csv"]:
        hash1 = compute_sha256(str(dir1 / file))
        hash2 = compute_sha256(str(dir2 / file))
        assert hash1 == hash2, f"Determinism failure in file {file}"
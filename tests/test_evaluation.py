"""Test evaluation metrics, hidden-set protocol, and safety targets."""
import pytest
from sahaay.evaluation.harness import evaluate_dataset, run_hidden_set_protocol
from sahaay.evaluation.metrics import compute_urgent_recall_ci

def test_urgent_recall_ci():
    y_true = ["P0", "P1", "P0", "P2", "P3"]
    y_pred = ["P0", "P1", "P1", "P2", "P3"]
    recall, ci_low, ci_high = compute_urgent_recall_ci(y_true, y_pred)
    assert recall == 1.0 # All P0/P1 stayed in P0/P1
    assert ci_low <= recall <= ci_high

def test_hidden_set_protocol():
    res = run_hidden_set_protocol()
    assert "predictions" in res
    assert len(res["predictions"]) > 0
    # Hidden set evaluation should output predicted urgency and latency for each record
    first_pred = res["predictions"][0]
    assert "predicted_urgency" in first_pred
    assert "latency_ms" in first_pred

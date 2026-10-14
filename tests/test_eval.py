"""Unit tests for the evaluation and ablation benchmark suite."""
import json
import os

import pytest

from eval.evaluate import compute_metrics, run_naive_diff


def test_compute_metrics():
    pred = {"Acme", "Cloud Division"}
    gt = {"Acme", "Cloud Division", "Legacy"}
    metrics = compute_metrics(pred, gt)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == pytest.approx(0.6667, 0.01)
    assert metrics["true_positives"] == 2
    assert metrics["false_negatives"] == 1


def test_run_naive_diff():
    v1_ents = ["Acme", "DataSync Platform"]
    v2_ents = ["Acme", "AcmeSync"]
    diff = run_naive_diff(v1_ents, v2_ents, [], [])
    assert diff["added_entities"] == ["AcmeSync"]
    assert diff["removed_entities"] == ["DataSync Platform"]


def test_gold_label_files_exist_and_valid():
    gold_dir = "eval/gold_labels"
    assert os.path.isdir(gold_dir)
    files = ["synthetic_v1_v2.json", "synthetic_v2_v3.json", "real_policy_v1_v2.json"]
    for f in files:
        path = os.path.join(gold_dir, f)
        assert os.path.exists(path), f"Missing gold file: {path}"
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            assert data["status"] == "needs human review"
            assert "expected_added_entities" in data
            assert "expected_removed_entities" in data

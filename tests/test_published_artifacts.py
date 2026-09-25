from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sensitivity_grid_is_complete() -> None:
    payload = json.loads((ROOT / "results" / "sensitivity.json").read_text(encoding="utf-8"))
    assert payload["design_count"] == 20
    assert payload["centering_sigma_mas"] == [10.0, 20.0, 25.0, 100.0]
    assert payload["command_failure_fractions"] == [0.0, 0.01, 0.02, 0.03, 0.04]
    with (ROOT / "results" / "sensitivity_designs.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        assert len(list(csv.DictReader(handle))) == 20


def test_primary_estimates_keep_estimands_separate() -> None:
    payload = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))
    metrics = {metric["name"]: metric for metric in payload["metrics"]}
    geometric = metrics["mean_geometric_throughput_given_command_success"]["estimate"]
    effective = metrics["mean_effective_throughput_worst_case_scenario"]["estimate"]
    assert 0.94 < geometric < 0.96
    assert 0.90 < effective < geometric
    assert "mean_throughput" not in metrics


def test_dashboard_serves_generated_evidence() -> None:
    for name in ("summary.json", "warnings.json", "sensitivity.json", "sensitivity_designs.csv"):
        assert (ROOT / "results" / name).read_bytes() == (
            ROOT / "web-react" / "public" / "results" / name
        ).read_bytes()

from __future__ import annotations

from pathlib import Path

import pytest

from jwst_nirspec_msa_throughput_sandbox.exceptions import DataSchemaError, ProvenanceError
from jwst_nirspec_msa_throughput_sandbox.provenance import (
    ManifestRow,
    append_manifest_row,
    get_git_commit,
    read_manifest,
    sha256_text,
)
from jwst_nirspec_msa_throughput_sandbox.results_io import Metric, validate_summary, write_summary

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_real_manifest_is_readable_and_complete():
    rows = read_manifest(REPO_ROOT / "data" / "manifest.csv")
    assert len(rows) == 8
    ids = {r["product_id"] for r in rows}
    assert "shutter_operability_fraction" in ids
    for row in rows:
        assert row["source_url"].startswith("http")
        assert row["sha256"] and row["sha256"] != "TODO_VERIFY"


def test_append_and_read_manifest_roundtrip(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    row = ManifestRow(
        product_id="test_param", source="unit test", source_url="https://example.org",
        retrieved_utc="2026-07-15T00:00:00Z", sha256=sha256_text("42"), file_size_bytes=0,
        selection_reason="test", licence_or_terms="test",
    )
    append_manifest_row(manifest_path, row)
    rows = read_manifest(manifest_path)
    assert len(rows) == 1
    assert rows[0]["product_id"] == "test_param"


def test_read_missing_manifest_raises():
    with pytest.raises(ProvenanceError):
        read_manifest("does_not_exist.csv")


def test_get_git_commit_never_raises(tmp_path):
    # This project directory is not a git repository; must return the
    # documented sentinel rather than raising.
    result = get_git_commit(tmp_path)
    assert isinstance(result, str)
    assert result != ""


def test_write_summary_roundtrip(tmp_path):
    metrics = [Metric(name="mean_throughput", estimate=0.5, units="dimensionless", sample_size=100)]
    payload = write_summary(
        tmp_path / "summary.json", project="test", data_kind="synthetic_monte_carlo",
        metrics=metrics, provenance={"seed": 1}, warnings=[],
    )
    assert payload["data_kind"] == "synthetic_monte_carlo"
    assert (tmp_path / "summary.json").is_file()


def test_validate_summary_rejects_missing_keys():
    with pytest.raises(DataSchemaError):
        validate_summary({"project": "x"})


def test_validate_summary_rejects_bad_metric():
    with pytest.raises(DataSchemaError):
        validate_summary({
            "project": "x", "data_kind": "y", "metrics": [{"name": "a"}],
            "provenance": {}, "warnings": [],
        })

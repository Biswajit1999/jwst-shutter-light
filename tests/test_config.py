from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from jwst_nirspec_msa_throughput_sandbox.config import load_config
from jwst_nirspec_msa_throughput_sandbox.exceptions import DataSchemaError

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_load_real_config():
    config = load_config(REPO_ROOT / "config" / "analysis.yml")
    assert config.project.author == "Biswajit Jana"
    assert config.monte_carlo.demo_trials > 0
    assert config.monte_carlo.production_trials >= config.monte_carlo.demo_trials


def test_missing_file_raises():
    with pytest.raises(DataSchemaError):
        load_config("does_not_exist.yml")


def test_missing_section_raises(tmp_path):
    path = tmp_path / "bad.yml"
    path.write_text(yaml.safe_dump({"project": {}}), encoding="utf-8")
    with pytest.raises(DataSchemaError):
        load_config(path)


def test_invalid_confidence_level_raises(tmp_path):
    base = yaml.safe_load((REPO_ROOT / "config" / "analysis.yml").read_text(encoding="utf-8"))
    base["validation"]["confidence_level"] = 1.5
    path = tmp_path / "bad.yml"
    path.write_text(yaml.safe_dump(base), encoding="utf-8")
    with pytest.raises(DataSchemaError):
        load_config(path)


def test_invalid_wavelength_range_raises(tmp_path):
    base = yaml.safe_load((REPO_ROOT / "config" / "analysis.yml").read_text(encoding="utf-8"))
    base["monte_carlo"]["wavelength_min_um"] = 5.0
    base["monte_carlo"]["wavelength_max_um"] = 1.0
    path = tmp_path / "bad.yml"
    path.write_text(yaml.safe_dump(base), encoding="utf-8")
    with pytest.raises(DataSchemaError):
        load_config(path)

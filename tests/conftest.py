from __future__ import annotations

from pathlib import Path

import pytest

from jwst_nirspec_msa_throughput_sandbox.config import load_config
from jwst_nirspec_msa_throughput_sandbox.geometry import MSAGeometry
from jwst_nirspec_msa_throughput_sandbox.psf import PSFModel

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def config():
    return load_config(REPO_ROOT / "config" / "analysis.yml")


@pytest.fixture()
def geometry() -> MSAGeometry:
    return MSAGeometry()


@pytest.fixture()
def psf_model() -> PSFModel:
    return PSFModel()

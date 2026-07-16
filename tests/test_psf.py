from __future__ import annotations

import numpy as np
import pytest

from jwst_nirspec_msa_throughput_sandbox.exceptions import DataSchemaError
from jwst_nirspec_msa_throughput_sandbox.psf import (
    DIFFRACTION_LIMIT_ONSET_UM,
    PSFModel,
    diffraction_fwhm_mas,
    fwhm_to_sigma_mas,
    is_diffraction_limited,
    psf_sigma_mas,
)


def test_fwhm_matches_verified_literature_anchor():
    # Jakobsen et al. 2022 verified anchor: FWHM = 80 mas at 2.5 um.
    fwhm = float(diffraction_fwhm_mas(2.5))
    assert fwhm == pytest.approx(80.0, rel=1e-6)


def test_fwhm_increases_with_wavelength():
    fwhm_short = float(diffraction_fwhm_mas(1.0))
    fwhm_long = float(diffraction_fwhm_mas(5.0))
    assert fwhm_long > fwhm_short


def test_fwhm_scales_linearly_with_wavelength():
    fwhm_1 = float(diffraction_fwhm_mas(1.0))
    fwhm_2 = float(diffraction_fwhm_mas(2.0))
    assert fwhm_2 == pytest.approx(2.0 * fwhm_1, rel=1e-9)


def test_non_positive_wavelength_rejected():
    with pytest.raises(DataSchemaError):
        diffraction_fwhm_mas(-1.0)
    with pytest.raises(DataSchemaError):
        diffraction_fwhm_mas(0.0)


def test_non_finite_wavelength_rejected():
    with pytest.raises(DataSchemaError):
        diffraction_fwhm_mas(np.nan)


def test_non_positive_mirror_diameter_rejected():
    with pytest.raises(DataSchemaError):
        diffraction_fwhm_mas(2.5, mirror_diameter_m=0.0)


def test_fwhm_to_sigma_conversion_factor():
    fwhm = 80.0
    sigma = float(fwhm_to_sigma_mas(fwhm))
    assert sigma == pytest.approx(fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0))), rel=1e-9)


def test_fwhm_to_sigma_rejects_non_positive():
    with pytest.raises(DataSchemaError):
        fwhm_to_sigma_mas(0.0)


def test_psf_sigma_positive_and_finite():
    sigma = psf_sigma_mas(np.linspace(0.6, 5.3, 20))
    assert np.all(np.isfinite(sigma))
    assert np.all(sigma > 0)


def test_diffraction_limit_onset_boundary():
    onset = DIFFRACTION_LIMIT_ONSET_UM
    assert bool(is_diffraction_limited(onset)) is True
    assert bool(is_diffraction_limited(onset - 0.1)) is False


def test_psf_model_dataclass_matches_module_functions():
    model = PSFModel()
    assert float(model.fwhm_mas(2.5)) == pytest.approx(float(diffraction_fwhm_mas(2.5)))
    assert float(model.sigma_mas(2.5)) == pytest.approx(float(psf_sigma_mas(2.5)))
    assert model.anchor_fwhm_mas == pytest.approx(80.0)
    assert model.anchor_wavelength_um == pytest.approx(2.5)

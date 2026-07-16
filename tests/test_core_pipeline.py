from __future__ import annotations

import numpy as np
import pytest

from jwst_nirspec_msa_throughput_sandbox.core import (
    SigmaRecoveryResult,
    recover_effective_sigma,
    run_pipeline,
)
from jwst_nirspec_msa_throughput_sandbox.exceptions import InsufficientDataError
from jwst_nirspec_msa_throughput_sandbox.geometry import rectangular_aperture_transmission


def test_run_pipeline_basic(config, geometry, psf_model):
    result = run_pipeline(config, n_trials=500, geometry=geometry, psf_model=psf_model, seed=1)
    assert result.monte_carlo.n_trials == 500
    assert 0.0 <= result.monte_carlo.mean_throughput <= 1.0
    assert len(result.offset_sweep) > 0
    assert len(result.wavelength_sweep) > 0
    assert result.failed_shutter_heatmap.size > 0
    assert result.throughput_bootstrap.ci_low <= result.throughput_bootstrap.estimate <= result.throughput_bootstrap.ci_high


def test_run_pipeline_rejects_zero_trials(config, geometry, psf_model):
    with pytest.raises(InsufficientDataError):
        run_pipeline(config, n_trials=0, geometry=geometry, psf_model=psf_model)


def test_run_pipeline_warns_below_minimum_sample_size(config, geometry, psf_model):
    result = run_pipeline(config, n_trials=5, geometry=geometry, psf_model=psf_model, seed=1)
    assert any("minimum_sample_size" in w for w in result.warnings)


def test_run_pipeline_deterministic_with_seed(config, geometry, psf_model):
    r1 = run_pipeline(config, n_trials=300, geometry=geometry, psf_model=psf_model, seed=99)
    r2 = run_pipeline(config, n_trials=300, geometry=geometry, psf_model=psf_model, seed=99)
    assert r1.monte_carlo.mean_throughput == pytest.approx(r2.monte_carlo.mean_throughput)


def test_injection_recovery_effective_sigma(geometry, psf_model):
    # Validation gate: inject a known effective 1D PSF sigma into the forward
    # model (deterministic offset sweep, no noise), then fit it back out.
    # Recovery must match the injected truth to within a tight tolerance.
    injected_sigma = 55.0
    offsets = np.linspace(-180.0, 180.0, 40)
    throughput = rectangular_aperture_transmission(
        offsets, 0.0, injected_sigma, injected_sigma, geometry.open_width_mas, geometry.open_height_mas
    )
    result = recover_effective_sigma(offsets, throughput, geometry.open_width_mas, initial_guess_mas=50.0)
    assert isinstance(result, SigmaRecoveryResult)
    assert result.recovered_sigma_mas == pytest.approx(injected_sigma, rel=1e-3)
    assert result.convergence.converged is True


def test_injection_recovery_rejects_too_few_points(geometry):
    with pytest.raises(InsufficientDataError):
        recover_effective_sigma(np.array([0.0, 1.0]), np.array([0.9, 0.8]), geometry.open_width_mas)


def test_starter_helpers_still_work():
    from jwst_nirspec_msa_throughput_sandbox.core import demo_series, robust_summary

    values = demo_series()
    summary = robust_summary(values)
    assert summary.count == 128

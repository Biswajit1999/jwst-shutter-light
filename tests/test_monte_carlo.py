from __future__ import annotations

import numpy as np
import pytest

from jwst_nirspec_msa_throughput_sandbox.exceptions import InsufficientDataError
from jwst_nirspec_msa_throughput_sandbox.monte_carlo import (
    failed_shutter_grid,
    generate_trials,
    run_monte_carlo,
)


def test_generate_trials_deterministic_with_seed():
    a = generate_trials(100, 20.0, 0.6, 5.3, 0.825, seed=42)
    b = generate_trials(100, 20.0, 0.6, 5.3, 0.825, seed=42)
    assert np.array_equal(a.dx_mas, b.dx_mas)
    assert np.array_equal(a.shutter_open, b.shutter_open)


def test_generate_trials_wavelength_within_bounds():
    trials = generate_trials(500, 20.0, 1.0, 3.0, 0.5, seed=1)
    assert np.all(trials.wavelength_um >= 1.0) and np.all(trials.wavelength_um <= 3.0)


def test_generate_trials_shutter_operability_fraction_converges():
    trials = generate_trials(20000, 20.0, 0.6, 5.3, 0.3, seed=7)
    assert np.mean(trials.shutter_open) == pytest.approx(0.3, abs=0.02)


def test_generate_trials_rejects_zero_trials():
    with pytest.raises(InsufficientDataError):
        generate_trials(0, 20.0, 0.6, 5.3, 0.825, seed=1)


def test_generate_trials_rejects_negative_trials():
    with pytest.raises(InsufficientDataError):
        generate_trials(-5, 20.0, 0.6, 5.3, 0.825, seed=1)


def test_generate_trials_rejects_bad_operability_fraction():
    with pytest.raises(InsufficientDataError):
        generate_trials(100, 20.0, 0.6, 5.3, 1.5, seed=1)


def test_run_monte_carlo_basic(geometry, psf_model):
    result = run_monte_carlo(2000, 20.0, 0.6, 5.3, 0.825, geometry, psf_model, seed=20260713)
    assert result.n_trials == 2000
    assert 0.0 <= result.mean_throughput <= 1.0
    assert result.fraction_shutter_closed == pytest.approx(1 - 0.825, abs=0.03)


def test_run_monte_carlo_zero_trials_raises(geometry, psf_model):
    with pytest.raises(InsufficientDataError):
        run_monte_carlo(0, 20.0, 0.6, 5.3, 0.825, geometry, psf_model, seed=1)


def test_all_shutters_closed_gives_zero_throughput(geometry, psf_model):
    result = run_monte_carlo(500, 20.0, 0.6, 5.3, 0.0, geometry, psf_model, seed=1)
    assert result.mean_throughput == 0.0
    assert result.fraction_shutter_closed == pytest.approx(1.0)


def test_failed_shutter_grid_shape_and_fraction():
    grid = failed_shutter_grid(20, 10, 0.825, seed=5)
    assert grid.shape == (10, 20)
    assert grid.dtype == bool


def test_failed_shutter_grid_rejects_invalid_dims():
    with pytest.raises(InsufficientDataError):
        failed_shutter_grid(0, 10, 0.825, seed=5)

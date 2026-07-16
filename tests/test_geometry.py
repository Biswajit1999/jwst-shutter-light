from __future__ import annotations

import numpy as np
import pytest

from jwst_nirspec_msa_throughput_sandbox.exceptions import DataSchemaError
from jwst_nirspec_msa_throughput_sandbox.geometry import (
    MSAGeometry,
    analytic_zero_offset_transmission,
    rectangular_aperture_transmission,
    shutter_grid_centers,
)


def test_default_geometry_matches_verified_constants():
    geo = MSAGeometry()
    assert geo.pitch_x_mas == pytest.approx(268.0)
    assert geo.pitch_y_mas == pytest.approx(530.0)
    assert geo.open_width_mas == pytest.approx(199.0)
    assert geo.open_height_mas == pytest.approx(461.0)
    assert geo.total_shutters == 4 * 365 * 171


def test_pitch_smaller_than_open_area_rejected():
    with pytest.raises(DataSchemaError):
        MSAGeometry(open_width_mas=1000.0)


def test_non_positive_open_dimensions_rejected():
    with pytest.raises(DataSchemaError):
        MSAGeometry(open_width_mas=0.0)


def test_transmission_matches_analytic_zero_offset_closed_form():
    # Validation-gate: the general numerical transmission function must agree
    # with the independently-derived closed-form erf expression at dx=dy=0.
    sigma = 60.0
    numeric = rectangular_aperture_transmission(0.0, 0.0, sigma, sigma, 199.0, 461.0)
    analytic = analytic_zero_offset_transmission(sigma, sigma, 199.0, 461.0)
    assert float(numeric) == pytest.approx(analytic, rel=1e-9)


def test_transmission_decreases_with_offset():
    sigma = 60.0
    t0 = float(rectangular_aperture_transmission(0.0, 0.0, sigma, sigma, 199.0, 461.0))
    t1 = float(rectangular_aperture_transmission(100.0, 0.0, sigma, sigma, 199.0, 461.0))
    assert t0 > t1
    assert 0.0 <= t1 <= t0 <= 1.0


def test_transmission_null_control_tiny_psf_large_aperture_approaches_one():
    # Null control: PSF much narrower than the aperture, centred -> throughput ~ 1.
    t = float(rectangular_aperture_transmission(0.0, 0.0, 1.0, 1.0, 199.0, 461.0))
    assert t == pytest.approx(1.0, abs=1e-6)


def test_transmission_bounds_always_in_zero_one():
    rng = np.random.default_rng(0)
    dx = rng.uniform(-500, 500, 200)
    dy = rng.uniform(-500, 500, 200)
    sigma = rng.uniform(5, 200, 200)
    t = rectangular_aperture_transmission(dx, dy, sigma, sigma, 199.0, 461.0)
    assert np.all(t >= 0.0) and np.all(t <= 1.0)


def test_non_finite_offset_rejected():
    with pytest.raises(DataSchemaError):
        rectangular_aperture_transmission(np.nan, 0.0, 60.0, 60.0, 199.0, 461.0)


def test_non_positive_sigma_rejected():
    with pytest.raises(DataSchemaError):
        rectangular_aperture_transmission(0.0, 0.0, 0.0, 60.0, 199.0, 461.0)


def test_analytic_zero_offset_rejects_non_positive_sigma():
    with pytest.raises(DataSchemaError):
        analytic_zero_offset_transmission(-1.0, 60.0, 199.0, 461.0)


def test_shutter_grid_centers_shape():
    geo = MSAGeometry()
    xs, ys = shutter_grid_centers(geo, 5, 3)
    assert xs.shape == (3, 5)
    assert ys.shape == (3, 5)
    # centre of an odd-count 1D grid should be exactly at zero
    assert xs[0, 2] == pytest.approx(0.0)


def test_shutter_grid_rejects_oversized_request():
    geo = MSAGeometry()
    with pytest.raises(DataSchemaError):
        shutter_grid_centers(geo, geo.shutters_per_quadrant_x + 1, 3)


def test_shutter_grid_rejects_non_positive_counts():
    geo = MSAGeometry()
    with pytest.raises(DataSchemaError):
        shutter_grid_centers(geo, 0, 3)

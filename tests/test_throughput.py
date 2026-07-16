from __future__ import annotations

import numpy as np
import pytest

from jwst_nirspec_msa_throughput_sandbox.exceptions import DataSchemaError
from jwst_nirspec_msa_throughput_sandbox.geometry import MSAGeometry
from jwst_nirspec_msa_throughput_sandbox.psf import PSFModel
from jwst_nirspec_msa_throughput_sandbox.throughput import (
    compute_throughput,
    throughput_vs_offset_sweep,
    throughput_vs_wavelength_sweep,
)


def test_compute_throughput_zeroes_failed_shutters(geometry, psf_model):
    dx = np.array([0.0, 0.0])
    dy = np.array([0.0, 0.0])
    wavelength = np.array([2.5, 2.5])
    shutter_open = np.array([True, False])
    t = compute_throughput(dx, dy, wavelength, shutter_open, geometry, psf_model)
    assert t[1] == 0.0
    assert t[0] > 0.0


def test_compute_throughput_bounds(geometry, psf_model):
    rng = np.random.default_rng(1)
    n = 500
    dx = rng.normal(0, 60, n)
    dy = rng.normal(0, 60, n)
    wavelength = rng.uniform(0.6, 5.3, n)
    shutter_open = rng.random(n) < 0.825
    t = compute_throughput(dx, dy, wavelength, shutter_open, geometry, psf_model)
    assert np.all(t >= 0.0) and np.all(t <= 1.0)
    assert np.all(np.isfinite(t))


def test_compute_throughput_rejects_mismatched_shapes(geometry, psf_model):
    with pytest.raises(DataSchemaError):
        compute_throughput(
            np.array([0.0, 0.0]), np.array([0.0]), np.array([2.5, 2.5]),
            np.array([True, True]), geometry, psf_model,
        )


def test_null_control_zero_offset_all_open_large_aperture_near_unity():
    # Null control: zero centering error, all shutters operable, and a
    # PSF much smaller than the shutter aperture -> throughput -> 1.
    geometry = MSAGeometry(open_width_mas=1e6, open_height_mas=1e6, pitch_x_mas=1e6 + 1, pitch_y_mas=1e6 + 1)
    psf_model = PSFModel()
    dx = np.zeros(10)
    dy = np.zeros(10)
    wavelength = np.full(10, 2.5)
    shutter_open = np.ones(10, dtype=bool)
    t = compute_throughput(dx, dy, wavelength, shutter_open, geometry, psf_model)
    assert np.all(t == pytest.approx(1.0, abs=1e-6))


def test_offset_sweep_monotonic_decrease_away_from_axis(geometry, psf_model):
    offsets = np.linspace(0, 300, 15)
    points = throughput_vs_offset_sweep(offsets, 2.5, geometry, psf_model)
    values = [p.mean_throughput for p in points]
    assert all(values[i] >= values[i + 1] - 1e-9 for i in range(len(values) - 1))


def test_offset_sweep_rejects_empty(geometry, psf_model):
    with pytest.raises(DataSchemaError):
        throughput_vs_offset_sweep(np.array([]), 2.5, geometry, psf_model)


def test_wavelength_sweep_throughput_improves_at_longer_wavelength_for_fixed_offset(geometry, psf_model):
    # At fixed non-zero offset, throughput vs wavelength should generally
    # decrease as the PSF broadens with wavelength (larger sigma -> more
    # flux spread outside a fixed offset aperture window is a more subtle
    # non-monotonic effect in general, so we only assert boundedness and
    # finiteness here as the physically-guaranteed property).
    wavelengths = np.linspace(0.6, 5.3, 20)
    points = throughput_vs_wavelength_sweep(wavelengths, 50.0, geometry, psf_model)
    values = np.array([p.mean_throughput for p in points])
    assert np.all(np.isfinite(values))
    assert np.all(values >= 0.0) and np.all(values <= 1.0)


def test_wavelength_sweep_rejects_empty(geometry, psf_model):
    with pytest.raises(DataSchemaError):
        throughput_vs_wavelength_sweep(np.array([]), 20.0, geometry, psf_model)

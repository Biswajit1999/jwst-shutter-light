"""Per-trial NIRSpec MSA throughput model: combines geometry, PSF and shutter operability.

Scope note (docs/RESEARCH_BLUEPRINT.md gap statement): this models only the
*geometric slit-loss* component of throughput (what fraction of a point
source's PSF flux geometrically passes through an open shutter aperture,
given a target-centering offset), plus a hard 0 for failed-closed shutters.
It does NOT model detector quantum efficiency, optical-train reflectivity,
grating efficiency or other end-to-end system throughput terms — this is an
instrument-physics QA sandbox, not a replacement for the official pipeline's
path-loss corrections (see docs/ASSUMPTIONS_AND_LIMITATIONS.md).

The PSF is treated as circularly symmetric (sigma_x = sigma_y = psf sigma at
the trial wavelength) — a simplification of the true NIRSpec PSF, which has
some anisotropy; documented in docs/ASSUMPTIONS_AND_LIMITATIONS.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from jwst_nirspec_msa_throughput_sandbox.exceptions import DataSchemaError
from jwst_nirspec_msa_throughput_sandbox.geometry import MSAGeometry, rectangular_aperture_transmission
from jwst_nirspec_msa_throughput_sandbox.psf import PSFModel


def compute_throughput(
    dx_mas: np.ndarray,
    dy_mas: np.ndarray,
    wavelength_um: np.ndarray,
    shutter_open: np.ndarray,
    geometry: MSAGeometry,
    psf_model: PSFModel,
) -> np.ndarray:
    """Per-trial throughput in [0, 1]: geometric slit transmission, zeroed where the shutter has failed closed."""
    dx = np.asarray(dx_mas, dtype=float)
    dy = np.asarray(dy_mas, dtype=float)
    wavelength = np.asarray(wavelength_um, dtype=float)
    open_mask = np.asarray(shutter_open, dtype=bool)

    shapes = {dx.shape, dy.shape, wavelength.shape, open_mask.shape}
    if len(shapes) > 1:
        raise DataSchemaError(f"inconsistent array lengths across trial inputs: {shapes}")

    sigma = psf_model.sigma_mas(wavelength)
    transmission = rectangular_aperture_transmission(
        dx, dy, sigma, sigma, geometry.open_width_mas, geometry.open_height_mas
    )
    throughput = np.where(open_mask, transmission, 0.0)

    if not np.all(np.isfinite(throughput)):
        raise DataSchemaError("computed throughput contains non-finite values")
    if np.any(throughput < 0.0) or np.any(throughput > 1.0):
        raise DataSchemaError("computed throughput outside physical bounds [0, 1]")
    return throughput


@dataclass(frozen=True)
class ThroughputSweepPoint:
    parameter_value: float
    mean_throughput: float
    median_throughput: float
    sample_size: int


def throughput_vs_offset_sweep(
    offsets_mas: np.ndarray,
    wavelength_um: float,
    geometry: MSAGeometry,
    psf_model: PSFModel,
) -> list[ThroughputSweepPoint]:
    """On-axis-in-y sweep: throughput at each 1D dispersion-direction offset, fixed wavelength, all shutters open."""
    offsets = np.asarray(offsets_mas, dtype=float)
    if offsets.size == 0:
        raise DataSchemaError("offsets_mas must not be empty")
    sigma = float(psf_model.sigma_mas(wavelength_um))
    points = []
    for off in offsets:
        t = rectangular_aperture_transmission(
            off, 0.0, sigma, sigma, geometry.open_width_mas, geometry.open_height_mas
        )
        points.append(ThroughputSweepPoint(parameter_value=float(off), mean_throughput=float(t), median_throughput=float(t), sample_size=1))
    return points


def throughput_vs_wavelength_sweep(
    wavelengths_um: np.ndarray,
    offset_mas: float,
    geometry: MSAGeometry,
    psf_model: PSFModel,
) -> list[ThroughputSweepPoint]:
    """Sweep throughput across wavelength at a fixed (dx, dy=0) centering offset, all shutters open."""
    wavelengths = np.asarray(wavelengths_um, dtype=float)
    if wavelengths.size == 0:
        raise DataSchemaError("wavelengths_um must not be empty")
    points = []
    for wl in wavelengths:
        sigma = float(psf_model.sigma_mas(wl))
        t = rectangular_aperture_transmission(
            offset_mas, 0.0, sigma, sigma, geometry.open_width_mas, geometry.open_height_mas
        )
        points.append(ThroughputSweepPoint(parameter_value=float(wl), mean_throughput=float(t), median_throughput=float(t), sample_size=1))
    return points


__all__ = [
    "compute_throughput",
    "ThroughputSweepPoint",
    "throughput_vs_offset_sweep",
    "throughput_vs_wavelength_sweep",
]

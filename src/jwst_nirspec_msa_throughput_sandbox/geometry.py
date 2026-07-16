"""NIRSpec micro-shutter array (MSA) geometry, from verified instrument parameters.

All numeric constants below are traced to a primary source; see
`data/manifest.csv` and `IMPLEMENTATION_PLAN.md` Sec 2 for the full
verification record (source URL + retrieval date for each parameter).

Source: Ferruit et al. 2022, "The Near-Infrared Spectrograph (NIRSpec) on the
James Webb Space Telescope II. Multi-object spectroscopy (MOS)", A&A,
arXiv:2202.03306, Sec 2.2:

- Shutter pitch: 105 um x 204 um (dispersion x spatial) physical, average
  on-sky projection 268 mas x 530 mas (the true projected pitch varies
  266-270 mas x 520-539 mas across the field of view due to optical
  distortion; the field-average value is used here as a documented
  simplification of the true field-dependent distortion map).
- Shutter open area: 78 um x 178 um physical, ~199 mas x 461 mas on-sky
  (commonly rounded to 0.20" x 0.46" in the literature).
- Array layout: 4 quadrants, each 365 x 171 individually addressable
  shutters => 249,660 shutters total.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm

from jwst_nirspec_msa_throughput_sandbox.exceptions import DataSchemaError

# --- Verified physical constants (on-sky projection, milliarcsec) ---
SHUTTER_PITCH_X_MAS = 268.0   # dispersion direction, field-averaged
SHUTTER_PITCH_Y_MAS = 530.0   # spatial direction, field-averaged
SHUTTER_OPEN_WIDTH_MAS = 199.0    # open aperture, dispersion direction
SHUTTER_OPEN_HEIGHT_MAS = 461.0   # open aperture, spatial direction
SHUTTERS_PER_QUADRANT_X = 365
SHUTTERS_PER_QUADRANT_Y = 171
N_QUADRANTS = 4
TOTAL_SHUTTERS = SHUTTERS_PER_QUADRANT_X * SHUTTERS_PER_QUADRANT_Y * N_QUADRANTS

# In-flight operability fraction (Rawle et al. 2022, arXiv:2208.04673 abstract:
# "82.5% of the unvignetted shutter population is usable for science").
DEFAULT_OPERABILITY_FRACTION = 0.825


@dataclass(frozen=True)
class MSAGeometry:
    """NIRSpec MSA shutter geometry, on-sky milliarcsec units."""

    pitch_x_mas: float = SHUTTER_PITCH_X_MAS
    pitch_y_mas: float = SHUTTER_PITCH_Y_MAS
    open_width_mas: float = SHUTTER_OPEN_WIDTH_MAS
    open_height_mas: float = SHUTTER_OPEN_HEIGHT_MAS
    shutters_per_quadrant_x: int = SHUTTERS_PER_QUADRANT_X
    shutters_per_quadrant_y: int = SHUTTERS_PER_QUADRANT_Y
    n_quadrants: int = N_QUADRANTS

    def __post_init__(self) -> None:
        if self.open_width_mas <= 0 or self.open_height_mas <= 0:
            raise DataSchemaError("shutter open dimensions must be positive")
        if self.pitch_x_mas < self.open_width_mas or self.pitch_y_mas < self.open_height_mas:
            raise DataSchemaError("shutter pitch cannot be smaller than the open aperture")

    @property
    def total_shutters(self) -> int:
        return self.shutters_per_quadrant_x * self.shutters_per_quadrant_y * self.n_quadrants


def rectangular_aperture_transmission(
    dx_mas: np.ndarray | float,
    dy_mas: np.ndarray | float,
    sigma_x_mas: np.ndarray | float,
    sigma_y_mas: np.ndarray | float,
    open_width_mas: float,
    open_height_mas: float,
) -> np.ndarray:
    """Fraction of a 2D-Gaussian point-source PSF's flux passing a rectangular aperture.

    The true NIRSpec PSF is closer to an Airy/diffraction pattern with
    wings; approximating it as a separable 2D Gaussian (independent x/y
    marginals) is a documented simplification (see
    docs/ASSUMPTIONS_AND_LIMITATIONS.md) consistent with this project's
    explicitly "simplified" scientific question. For a target whose PSF
    centroid is offset by (dx, dy) from the shutter centre, the transmitted
    flux fraction through the open rectangular aperture
    [-open_width/2, open_width/2] x [-open_height/2, open_height/2] is the
    product of two independent 1D Gaussian-CDF integrals (exact for a
    separable Gaussian PSF and a rectangular aperture — this part is exact
    given the Gaussian-PSF assumption, not an additional approximation).

    All inputs may be scalars or same-shaped arrays; returns an array (or
    scalar) of throughput values in [0, 1].
    """
    dx = np.asarray(dx_mas, dtype=float)
    dy = np.asarray(dy_mas, dtype=float)
    sigma_x = np.asarray(sigma_x_mas, dtype=float)
    sigma_y = np.asarray(sigma_y_mas, dtype=float)

    if np.any(sigma_x <= 0) or np.any(sigma_y <= 0):
        raise DataSchemaError("PSF sigma must be strictly positive")
    if not (np.all(np.isfinite(dx)) and np.all(np.isfinite(dy))):
        raise DataSchemaError("centering offsets must be finite")
    if open_width_mas <= 0 or open_height_mas <= 0:
        raise DataSchemaError("aperture open dimensions must be positive")

    half_w = open_width_mas / 2.0
    half_h = open_height_mas / 2.0

    t_x = norm.cdf((half_w - dx) / sigma_x) - norm.cdf((-half_w - dx) / sigma_x)
    t_y = norm.cdf((half_h - dy) / sigma_y) - norm.cdf((-half_h - dy) / sigma_y)
    transmission = t_x * t_y

    # Numerically clip tiny floating-point overshoot (e.g. 1.0000000000000002)
    # rather than silently letting an out-of-[0,1] value propagate.
    return np.clip(transmission, 0.0, 1.0)


def analytic_zero_offset_transmission(sigma_x_mas: float, sigma_y_mas: float, open_width_mas: float, open_height_mas: float) -> float:
    """Closed-form on-axis (dx=dy=0) transmission, used as the validation-contract analytic limit.

    At zero offset, T = erf(w / (2*sqrt(2)*sigma_x)) * erf(h / (2*sqrt(2)*sigma_y)),
    the standard result for the flux fraction of a centred 2D Gaussian
    passing a centred rectangular aperture. This is algebraically identical
    to `rectangular_aperture_transmission(0, 0, ...)` and is provided
    separately, in closed form, purely so the validation test has an
    independent reference implementation to compare against.
    """
    from scipy.special import erf

    if sigma_x_mas <= 0 or sigma_y_mas <= 0:
        raise DataSchemaError("PSF sigma must be strictly positive")
    tx = erf(open_width_mas / (2.0 * np.sqrt(2.0) * sigma_x_mas))
    ty = erf(open_height_mas / (2.0 * np.sqrt(2.0) * sigma_y_mas))
    return float(tx * ty)


def shutter_grid_centers(geometry: MSAGeometry, n_x: int, n_y: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (x_mas, y_mas) 2D meshgrid arrays of shutter centre coordinates for an n_x x n_y sub-grid.

    Used for the illustrative MSA geometry figure and the failed-shutter
    heatmap; `n_x`, `n_y` are typically a small illustrative subset of the
    real 365x171-per-quadrant array, not the full array, for figure clarity.
    """
    if n_x <= 0 or n_y <= 0:
        raise DataSchemaError("n_x and n_y must be positive")
    if n_x > geometry.shutters_per_quadrant_x or n_y > geometry.shutters_per_quadrant_y:
        raise DataSchemaError("requested sub-grid exceeds one quadrant's real shutter count")
    xs = (np.arange(n_x) - (n_x - 1) / 2.0) * geometry.pitch_x_mas
    ys = (np.arange(n_y) - (n_y - 1) / 2.0) * geometry.pitch_y_mas
    grid_x, grid_y = np.meshgrid(xs, ys)
    return grid_x, grid_y


__all__ = [
    "SHUTTER_PITCH_X_MAS",
    "SHUTTER_PITCH_Y_MAS",
    "SHUTTER_OPEN_WIDTH_MAS",
    "SHUTTER_OPEN_HEIGHT_MAS",
    "SHUTTERS_PER_QUADRANT_X",
    "SHUTTERS_PER_QUADRANT_Y",
    "N_QUADRANTS",
    "TOTAL_SHUTTERS",
    "DEFAULT_OPERABILITY_FRACTION",
    "MSAGeometry",
    "rectangular_aperture_transmission",
    "analytic_zero_offset_transmission",
    "shutter_grid_centers",
]

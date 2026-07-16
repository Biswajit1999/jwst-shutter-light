"""Wavelength-dependent NIRSpec PSF width.

Source: Jakobsen et al. 2022, "The Near-Infrared Spectrograph (NIRSpec) on
the James Webb Space Telescope I. Overview of the instrument and its
capabilities", A&A 661, A80, arXiv:2202.03305 — verified anchor: the PSF
FWHM in the NIRSpec slit plane at 2.5 um is 80 mas, and the PSF is
diffraction-limited (Strehl ratio > 0.8) at wavelengths above 2.46 um.

The JWST primary mirror effective aperture is D = 6.5 m (standard public
JWST observatory specification). The diffraction-limited FWHM scaling
FWHM(lambda) = lambda / D (in radians, converted to mas) reproduces the
80 mas anchor at 2.5 um to within 1% (0.0793" = 79.3 mas computed vs. 80 mas
literature value), confirming this is the correct functional form rather
than an independently invented scaling law.

TODO_VERIFY: the literature anchor above only confirms the PSF is fully
diffraction-limited (Strehl > 0.8) *above* 2.46 um. Below that wavelength the
true PSF is somewhat broader than the pure lambda/D law predicts (departure
from diffraction-limited performance), but no verified quantitative
Strehl-vs-wavelength curve for NIRSpec was found in the time available for
this implementation pass. This module therefore applies the pure
diffraction-limited lambda/D law across the *entire* NIRSpec range
(0.6-5.3 um), which is a documented, flagged simplification consistent with
this project's explicitly "simplified" scientific question — it likely
*underestimates* short-wavelength (<2.46 um) slit losses somewhat. See
docs/ASSUMPTIONS_AND_LIMITATIONS.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from jwst_nirspec_msa_throughput_sandbox.exceptions import DataSchemaError

JWST_MIRROR_DIAMETER_M = 6.5

# Verified literature anchor (Jakobsen et al. 2022): FWHM=80 mas at 2.5 um.
_ANCHOR_WAVELENGTH_UM = 2.5
_ANCHOR_FWHM_MAS = 80.0

# Radians -> milliarcsec conversion.
_RAD_TO_MAS = 206264.8 * 1000.0

# Gaussian FWHM <-> sigma conversion factor: FWHM = 2*sqrt(2*ln(2)) * sigma.
_FWHM_TO_SIGMA = 1.0 / (2.0 * np.sqrt(2.0 * np.log(2.0)))

NIRSPEC_WAVELENGTH_MIN_UM = 0.6
NIRSPEC_WAVELENGTH_MAX_UM = 5.3
DIFFRACTION_LIMIT_ONSET_UM = 2.46  # Strehl ratio > 0.8 above this wavelength


def _pure_diffraction_fwhm_mas(wavelength_um: np.ndarray, mirror_diameter_m: float) -> np.ndarray:
    wavelength_m = wavelength_um * 1e-6
    return (wavelength_m / mirror_diameter_m) * _RAD_TO_MAS


# Calibration factor mapping the pure geometric lambda/D formula onto the
# verified literature anchor (80 mas at 2.5 um); expected to be close to 1.0.
_CALIBRATION_FACTOR = _ANCHOR_FWHM_MAS / float(_pure_diffraction_fwhm_mas(np.asarray(_ANCHOR_WAVELENGTH_UM), JWST_MIRROR_DIAMETER_M))


def diffraction_fwhm_mas(
    wavelength_um: np.ndarray | float, mirror_diameter_m: float = JWST_MIRROR_DIAMETER_M
) -> np.ndarray:
    """PSF FWHM (mas) as a function of wavelength (um), calibrated to the verified 80 mas @ 2.5 um anchor."""
    wl = np.asarray(wavelength_um, dtype=float)
    if np.any(wl <= 0) or not np.all(np.isfinite(wl)):
        raise DataSchemaError("wavelength must be finite and positive")
    if mirror_diameter_m <= 0:
        raise DataSchemaError("mirror_diameter_m must be positive")
    return _CALIBRATION_FACTOR * _pure_diffraction_fwhm_mas(wl, mirror_diameter_m)


def fwhm_to_sigma_mas(fwhm_mas: np.ndarray | float) -> np.ndarray:
    fwhm = np.asarray(fwhm_mas, dtype=float)
    if np.any(fwhm <= 0):
        raise DataSchemaError("FWHM must be positive")
    return fwhm * _FWHM_TO_SIGMA


def psf_sigma_mas(wavelength_um: np.ndarray | float, mirror_diameter_m: float = JWST_MIRROR_DIAMETER_M) -> np.ndarray:
    """Gaussian-equivalent PSF sigma (mas) at the given wavelength(s)."""
    return fwhm_to_sigma_mas(diffraction_fwhm_mas(wavelength_um, mirror_diameter_m))


def is_diffraction_limited(wavelength_um: np.ndarray | float) -> np.ndarray:
    """True where the literature confirms Strehl ratio > 0.8 (i.e. wavelength_um >= 2.46 um)."""
    wl = np.asarray(wavelength_um, dtype=float)
    return wl >= DIFFRACTION_LIMIT_ONSET_UM


@dataclass(frozen=True)
class PSFModel:
    """Container bundling the verified PSF scaling constants for provenance reporting."""

    mirror_diameter_m: float = JWST_MIRROR_DIAMETER_M
    anchor_wavelength_um: float = _ANCHOR_WAVELENGTH_UM
    anchor_fwhm_mas: float = _ANCHOR_FWHM_MAS
    calibration_factor: float = _CALIBRATION_FACTOR
    diffraction_limit_onset_um: float = DIFFRACTION_LIMIT_ONSET_UM

    def fwhm_mas(self, wavelength_um: np.ndarray | float) -> np.ndarray:
        return diffraction_fwhm_mas(wavelength_um, self.mirror_diameter_m)

    def sigma_mas(self, wavelength_um: np.ndarray | float) -> np.ndarray:
        return psf_sigma_mas(wavelength_um, self.mirror_diameter_m)


__all__ = [
    "JWST_MIRROR_DIAMETER_M",
    "NIRSPEC_WAVELENGTH_MIN_UM",
    "NIRSPEC_WAVELENGTH_MAX_UM",
    "DIFFRACTION_LIMIT_ONSET_UM",
    "PSFModel",
    "diffraction_fwhm_mas",
    "fwhm_to_sigma_mas",
    "psf_sigma_mas",
    "is_diffraction_limited",
]

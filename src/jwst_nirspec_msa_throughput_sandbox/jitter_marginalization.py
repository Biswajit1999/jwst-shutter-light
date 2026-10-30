"""Independent Gaussian MSA slit-loss sensitivity calculations.

All throughputs are geometric fractions CONDITIONAL on a shutter opening.
Gaussian PSFs and Gaussian acquisition errors are hypothetical model choices;
this module does not implement official JWST path-loss corrections.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.special import ndtr


def _positive(name: str, value: float) -> float:
    value = float(value)
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and strictly positive")
    return value


def _transmission_1d(offset: np.ndarray | float, width: float, sigma: float) -> np.ndarray:
    return ndtr((width / 2 - offset) / sigma) - ndtr((-width / 2 - offset) / sigma)


def geometric_transmission(
    dx: np.ndarray | float, dy: np.ndarray | float, *,
    width: float = 199.0, height: float = 461.0,
    psf_sigma_x: float = 80.0 / 2.354820045,
    psf_sigma_y: float = 80.0 / 2.354820045,
) -> np.ndarray:
    """Exact rectangular-aperture integral under a separable Gaussian PSF (mas)."""
    for name, value in (("width", width), ("height", height),
                        ("psf_sigma_x", psf_sigma_x), ("psf_sigma_y", psf_sigma_y)):
        _positive(name, value)
    x, y = np.broadcast_arrays(np.asarray(dx, float), np.asarray(dy, float))
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        raise ValueError("offsets must be finite")
    return np.clip(_transmission_1d(x, width, psf_sigma_x) *
                   _transmission_1d(y, height, psf_sigma_y), 0.0, 1.0)


def analytic_jitter_mean(
    mean_x: float = 0.0, mean_y: float = 0.0, *,
    jitter_sigma_x: float = 20.0, jitter_sigma_y: float = 20.0,
    width: float = 199.0, height: float = 461.0,
    psf_sigma_x: float = 80.0 / 2.354820045,
    psf_sigma_y: float = 80.0 / 2.354820045,
) -> float:
    """Exact expectation for independent Gaussian acquisition offsets.

    Convolution of independent Gaussian PSF and pointing jitter adds variances.
    This is NOT a confidence interval on a planned observation.
    """
    for name, value in (("jitter_sigma_x", jitter_sigma_x),
                        ("jitter_sigma_y", jitter_sigma_y)):
        if not np.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative")
    return float(geometric_transmission(
        mean_x, mean_y, width=width, height=height,
        psf_sigma_x=np.hypot(_positive("psf_sigma_x", psf_sigma_x), jitter_sigma_x),
        psf_sigma_y=np.hypot(_positive("psf_sigma_y", psf_sigma_y), jitter_sigma_y),
    ))


def correlated_jitter_mean(
    mean_x: float, mean_y: float, *,
    jitter_sigma_x: float, jitter_sigma_y: float, rho: float,
    order: int = 16, width: float = 199.0, height: float = 461.0,
    psf_sigma_x: float = 80.0 / 2.354820045,
    psf_sigma_y: float = 80.0 / 2.354820045,
) -> float:
    """2D Gauss-Hermite expectation for correlated Gaussian centering errors.

    Quadrature nodes sample the acquisition-offset distribution, not the PSF.
    At rho=0 the result should converge to analytic_jitter_mean.
    """
    if not isinstance(order, int) or not 2 <= order <= 80:
        raise ValueError("quadrature order must be an integer in [2, 80]")
    if not np.isfinite(rho) or abs(rho) > 1:
        raise ValueError("rho must lie in [-1, 1]")
    if not all(np.isfinite(v) and v >= 0 for v in (jitter_sigma_x, jitter_sigma_y)):
        raise ValueError("jitter sigmas must be finite and nonnegative")
    cov = np.array([[jitter_sigma_x**2, rho * jitter_sigma_x * jitter_sigma_y],
                    [rho * jitter_sigma_x * jitter_sigma_y, jitter_sigma_y**2]])
    eigval, eigvec = np.linalg.eigh(cov)
    factor = eigvec @ np.diag(np.sqrt(np.maximum(eigval, 0.0)))
    nodes, weights = np.polynomial.hermite.hermgauss(order)
    z0, z1 = np.meshgrid(nodes * np.sqrt(2), nodes * np.sqrt(2), indexing="ij")
    dx = mean_x + factor[0, 0] * z0 + factor[0, 1] * z1
    dy = mean_y + factor[1, 0] * z0 + factor[1, 1] * z1
    w = np.outer(weights, weights) / np.pi
    return float(np.sum(w * geometric_transmission(
        dx, dy, width=width, height=height,
        psf_sigma_x=psf_sigma_x, psf_sigma_y=psf_sigma_y,
    )))


def local_sensitivities(*, mean_x: float = 20.0, jitter_sigma_x: float = 20.0,
                        step_mas: float = 0.1, **kwargs: float) -> dict[str, float]:
    """Central differences in mean dispersion offset and jitter RMS (per mas)."""
    if not np.isfinite(step_mas) or step_mas <= 0 or jitter_sigma_x <= step_mas:
        raise ValueError("step must be positive and smaller than jitter_sigma_x")
    def f(x: float, s: float) -> float:
        return analytic_jitter_mean(mean_x=x, jitter_sigma_x=s, **kwargs)
    return {
        "d_mean_d_offset_per_mas": (f(mean_x + step_mas, jitter_sigma_x) -
                                   f(mean_x - step_mas, jitter_sigma_x)) / (2 * step_mas),
        "d_mean_d_jitter_per_mas": (f(mean_x, jitter_sigma_x + step_mas) -
                                   f(mean_x, jitter_sigma_x - step_mas)) / (2 * step_mas),
    }


def diagnostic_report() -> dict[str, object]:
    """Reproducible synthetic model-sensitivity grid, no observed data."""
    results = []
    for rho in (0.0, 0.4, 0.8):
        vals = [correlated_jitter_mean(35, 80, jitter_sigma_x=35,
                jitter_sigma_y=100, rho=rho, order=n) for n in (16, 32, 64, 80)]
        results.append({"rho": rho, "quadrature_order": [16, 32, 64, 80],
                        "throughput": vals, "order_64_to_80_delta": vals[-1] - vals[-2]})
    return {"model": "Gaussian PSF + Gaussian pointing error; conditional shutter opening",
            "units": "mas", "wavelength_anchor_um": 2.5,
            "analytic_independent": analytic_jitter_mean(mean_x=35, mean_y=15,
                                    jitter_sigma_x=35, jitter_sigma_y=25),
            "correlation_sweep": results,
            "local_sensitivity": local_sensitivities()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(diagnostic_report(), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()

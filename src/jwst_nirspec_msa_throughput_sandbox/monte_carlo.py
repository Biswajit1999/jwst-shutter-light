"""Monte Carlo trial generation and orchestration for the NIRSpec MSA throughput sandbox.

Each trial draws:
- a target-centering offset (dx, dy) from an independent 2D Gaussian with
  sigma = ``centering_sigma_mas`` (fiducial 20 mas, the verified MSATA
  in-flight performance; see docs/RESEARCH_BLUEPRINT.md, IMPLEMENTATION_PLAN.md
  Sec 2 item 8),
- a wavelength drawn uniformly from [wavelength_min_um, wavelength_max_um]
  (the verified NIRSpec range 0.6-5.3 um),
- a shutter-open Bernoulli draw at ``operability_fraction`` (verified in-flight
  aggregate operability, 82.5%; IMPLEMENTATION_PLAN.md Sec 2 item 4).

All output is synthetic Monte Carlo data (`data_kind = "synthetic_monte_carlo"`
in results/summary.json), not real telemetry.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from jwst_nirspec_msa_throughput_sandbox.exceptions import InsufficientDataError
from jwst_nirspec_msa_throughput_sandbox.geometry import MSAGeometry
from jwst_nirspec_msa_throughput_sandbox.psf import PSFModel
from jwst_nirspec_msa_throughput_sandbox.throughput import compute_throughput


@dataclass(frozen=True)
class TrialInputs:
    dx_mas: np.ndarray
    dy_mas: np.ndarray
    wavelength_um: np.ndarray
    shutter_open: np.ndarray


def generate_trials(
    n_trials: int,
    centering_sigma_mas: float,
    wavelength_min_um: float,
    wavelength_max_um: float,
    operability_fraction: float,
    seed: int,
) -> TrialInputs:
    """Draw `n_trials` independent Monte Carlo trial inputs."""
    if n_trials <= 0:
        raise InsufficientDataError(f"n_trials must be positive, got {n_trials}")
    if centering_sigma_mas <= 0:
        raise InsufficientDataError(f"centering_sigma_mas must be positive, got {centering_sigma_mas}")
    if not (0.0 <= operability_fraction <= 1.0):
        raise InsufficientDataError(f"operability_fraction must be in [0, 1], got {operability_fraction}")
    if wavelength_min_um >= wavelength_max_um:
        raise InsufficientDataError("wavelength_min_um must be < wavelength_max_um")

    rng = np.random.default_rng(seed)
    dx = rng.normal(loc=0.0, scale=centering_sigma_mas, size=n_trials)
    dy = rng.normal(loc=0.0, scale=centering_sigma_mas, size=n_trials)
    wavelength = rng.uniform(wavelength_min_um, wavelength_max_um, size=n_trials)
    shutter_open = rng.random(n_trials) < operability_fraction
    return TrialInputs(dx_mas=dx, dy_mas=dy, wavelength_um=wavelength, shutter_open=shutter_open)


@dataclass(frozen=True)
class MonteCarloRunResult:
    n_trials: int
    throughput: np.ndarray
    trial_inputs: TrialInputs
    mean_throughput: float
    median_throughput: float
    fraction_shutter_closed: float
    mean_throughput_open_only: float


def run_monte_carlo(
    n_trials: int,
    centering_sigma_mas: float,
    wavelength_min_um: float,
    wavelength_max_um: float,
    operability_fraction: float,
    geometry: MSAGeometry,
    psf_model: PSFModel,
    seed: int,
) -> MonteCarloRunResult:
    """Run `n_trials` independent Monte Carlo throughput trials and summarize.

    Raises InsufficientDataError for n_trials <= 0 (propagated from
    `generate_trials`); does not silently clip to zero trials.
    """
    trials = generate_trials(
        n_trials, centering_sigma_mas, wavelength_min_um, wavelength_max_um, operability_fraction, seed
    )
    throughput = compute_throughput(
        trials.dx_mas, trials.dy_mas, trials.wavelength_um, trials.shutter_open, geometry, psf_model
    )
    open_mask = trials.shutter_open
    fraction_closed = float(1.0 - np.mean(open_mask))
    mean_open_only = float(np.mean(throughput[open_mask])) if np.any(open_mask) else 0.0

    return MonteCarloRunResult(
        n_trials=n_trials,
        throughput=throughput,
        trial_inputs=trials,
        mean_throughput=float(np.mean(throughput)),
        median_throughput=float(np.median(throughput)),
        fraction_shutter_closed=fraction_closed,
        mean_throughput_open_only=mean_open_only,
    )


def failed_shutter_grid(
    n_x: int, n_y: int, operability_fraction: float, seed: int
) -> np.ndarray:
    """Illustrative independent-Bernoulli shutter-operability heatmap at the verified aggregate fraction.

    Explicitly a synthetic illustrative realization (independent per-shutter
    draws at the verified *aggregate* operability), not a real MSA operability
    map — see IMPLEMENTATION_PLAN.md TODO_VERIFY item on spatial structure of
    shutter failures.
    """
    if n_x <= 0 or n_y <= 0:
        raise InsufficientDataError("n_x and n_y must be positive")
    if not (0.0 <= operability_fraction <= 1.0):
        raise InsufficientDataError("operability_fraction must be in [0, 1]")
    rng = np.random.default_rng(seed)
    return rng.random((n_y, n_x)) < operability_fraction


__all__ = [
    "TrialInputs",
    "generate_trials",
    "MonteCarloRunResult",
    "run_monte_carlo",
    "failed_shutter_grid",
]

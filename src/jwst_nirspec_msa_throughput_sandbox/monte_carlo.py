"""Monte Carlo trial generation and orchestration for the NIRSpec MSA throughput sandbox.

Each trial draws:
- a target-centering offset (dx, dy) from an independent 2D Gaussian with
  sigma = ``centering_sigma_mas`` (fiducial 20 mas, the verified MSATA
  in-flight performance; see docs/RESEARCH_BLUEPRINT.md, IMPLEMENTATION_PLAN.md
  Sec 2 item 8),
- a wavelength drawn uniformly from [wavelength_min_um, wavelength_max_um]
  (the verified NIRSpec range 0.6-5.3 um),
- a commanded-open success draw at ``command_success_probability``. The
  conservative default is 96%, representing the current STScI statement that
  up to 4% of otherwise operable shutters may remain closed when commanded.

Static shutter operability is deliberately absent: APT/MPT uses the current
position-specific operability map before observation planning, so an aggregate
usable-shutter fraction is not a per-observation photon-throughput probability.

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
    command_succeeded: np.ndarray


def generate_trials(
    n_trials: int,
    centering_sigma_mas: float,
    wavelength_min_um: float,
    wavelength_max_um: float,
    command_success_probability: float,
    seed: int,
) -> TrialInputs:
    """Draw `n_trials` independent Monte Carlo trial inputs."""
    if n_trials <= 0:
        raise InsufficientDataError(f"n_trials must be positive, got {n_trials}")
    if centering_sigma_mas <= 0:
        raise InsufficientDataError(f"centering_sigma_mas must be positive, got {centering_sigma_mas}")
    if not (0.0 <= command_success_probability <= 1.0):
        raise InsufficientDataError(
            "command_success_probability must be in [0, 1], got "
            f"{command_success_probability}"
        )
    if wavelength_min_um >= wavelength_max_um:
        raise InsufficientDataError("wavelength_min_um must be < wavelength_max_um")

    rng = np.random.default_rng(seed)
    dx = rng.normal(loc=0.0, scale=centering_sigma_mas, size=n_trials)
    dy = rng.normal(loc=0.0, scale=centering_sigma_mas, size=n_trials)
    wavelength = rng.uniform(wavelength_min_um, wavelength_max_um, size=n_trials)
    command_succeeded = rng.random(n_trials) < command_success_probability
    return TrialInputs(
        dx_mas=dx,
        dy_mas=dy,
        wavelength_um=wavelength,
        command_succeeded=command_succeeded,
    )


@dataclass(frozen=True)
class MonteCarloRunResult:
    n_trials: int
    throughput: np.ndarray
    trial_inputs: TrialInputs
    mean_effective_throughput: float
    median_geometric_throughput: float
    fraction_command_failed: float
    mean_geometric_throughput: float


def run_monte_carlo(
    n_trials: int,
    centering_sigma_mas: float,
    wavelength_min_um: float,
    wavelength_max_um: float,
    command_success_probability: float,
    geometry: MSAGeometry,
    psf_model: PSFModel,
    seed: int,
) -> MonteCarloRunResult:
    """Run `n_trials` independent Monte Carlo throughput trials and summarize.

    Raises InsufficientDataError for n_trials <= 0 (propagated from
    `generate_trials`); does not silently clip to zero trials.
    """
    trials = generate_trials(
        n_trials,
        centering_sigma_mas,
        wavelength_min_um,
        wavelength_max_um,
        command_success_probability,
        seed,
    )
    throughput = compute_throughput(
        trials.dx_mas,
        trials.dy_mas,
        trials.wavelength_um,
        trials.command_succeeded,
        geometry,
        psf_model,
    )
    open_mask = trials.command_succeeded
    fraction_closed = float(1.0 - np.mean(open_mask))
    mean_open_only = float(np.mean(throughput[open_mask])) if np.any(open_mask) else 0.0

    return MonteCarloRunResult(
        n_trials=n_trials,
        throughput=throughput,
        trial_inputs=trials,
        mean_effective_throughput=float(np.mean(throughput)),
        median_geometric_throughput=float(np.median(throughput[open_mask])) if np.any(open_mask) else 0.0,
        fraction_command_failed=fraction_closed,
        mean_geometric_throughput=mean_open_only,
    )


def failed_shutter_grid(
    n_x: int, n_y: int, operability_fraction: float, seed: int
) -> np.ndarray:
    """Illustrative independent-Bernoulli shutter-operability heatmap at the verified aggregate fraction.

    Explicitly a synthetic illustrative realization (independent per-shutter
    draws at the verified *aggregate* operability), not a real MSA operability
    map — see IMPLEMENTATION_PLAN.md VERIFICATION_PENDING item on spatial structure of
    shutter failures.
    """
    if n_x <= 0 or n_y <= 0:
        raise InsufficientDataError("n_x and n_y must be positive")
    if not (0.0 <= operability_fraction <= 1.0):
        raise InsufficientDataError("operability_fraction must be in [0, 1]")
    rng = np.random.default_rng(seed)
    return rng.random((n_y, n_x)) < operability_fraction


__all__ = [
    "MonteCarloRunResult",
    "TrialInputs",
    "failed_shutter_grid",
    "generate_trials",
    "run_monte_carlo",
]

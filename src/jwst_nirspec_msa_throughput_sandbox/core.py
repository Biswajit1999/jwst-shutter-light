"""Pipeline orchestration composing the reusable scientific modules.

`run_pipeline` is the single non-notebook entry point for the Monte Carlo
throughput analysis. It is deliberately network-free (no archive access is
performed for this project; see docs/DATASET_PLAN.md, mode = "official
instrument parameters + synthetic Monte Carlo") so it can be exercised
identically in tests (small trial counts) and in production (large trial
counts) — see scripts/run_analysis.py for the CLI entry point.

Every output of `run_pipeline` is synthetic Monte Carlo data, never real
telemetry; callers must set `data_kind="synthetic_monte_carlo"` when writing
results/summary.json (see results_io.write_summary).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import curve_fit

from jwst_nirspec_msa_throughput_sandbox.config import AnalysisConfig
from jwst_nirspec_msa_throughput_sandbox.exceptions import ConvergenceError, DataSchemaError, InsufficientDataError
from jwst_nirspec_msa_throughput_sandbox.geometry import MSAGeometry
from jwst_nirspec_msa_throughput_sandbox.logging_utils import get_logger
from jwst_nirspec_msa_throughput_sandbox.monte_carlo import MonteCarloRunResult, failed_shutter_grid, run_monte_carlo
from jwst_nirspec_msa_throughput_sandbox.psf import PSFModel
from jwst_nirspec_msa_throughput_sandbox.throughput import (
    ThroughputSweepPoint,
    throughput_vs_offset_sweep,
    throughput_vs_wavelength_sweep,
)
from jwst_nirspec_msa_throughput_sandbox.uncertainty import BootstrapResult, FitConvergence, bootstrap_statistic, check_fit_convergence

LOGGER = get_logger(__name__)

# Deprecated starter helpers retained only so the original smoke test
# (tests/test_starter_core.py) keeps passing; not used by run_pipeline.
from dataclasses import dataclass as _dataclass  # noqa: E402


@_dataclass(frozen=True)
class Summary:
    count: int
    median: float
    mad: float


def validate_numeric(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError("values must be one-dimensional")
    if arr.size == 0:
        raise ValueError("values must not be empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError("values contain non-finite entries")
    return arr


def robust_summary(values: np.ndarray) -> Summary:
    arr = validate_numeric(values)
    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    return Summary(count=int(arr.size), median=median, mad=mad)


def demo_series(seed: int = 20260713, size: int = 128) -> np.ndarray:
    """Return deterministic synthetic data labelled only for smoke testing."""
    if size < 8:
        raise ValueError("size must be at least 8")
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=1.0, size=size)


def _gaussian_aperture_1d_model(dx: np.ndarray, sigma_mas: float, open_width_mas: float) -> np.ndarray:
    """1D marginal transmission model used to fit an effective centering sigma from a throughput-vs-offset sweep."""
    from scipy.special import erf

    half = open_width_mas / 2.0
    return 0.5 * (erf((half - dx) / (np.sqrt(2.0) * sigma_mas)) - erf((-half - dx) / (np.sqrt(2.0) * sigma_mas)))


@dataclass(frozen=True)
class SigmaRecoveryResult:
    injected_sigma_mas: float
    recovered_sigma_mas: float
    convergence: FitConvergence


def recover_effective_sigma(
    offsets_mas: np.ndarray, throughput: np.ndarray, open_width_mas: float, initial_guess_mas: float = 50.0
) -> SigmaRecoveryResult:
    """Fit an effective 1D PSF sigma back out of a throughput-vs-offset sweep (dy=0, wavelength fixed).

    Used by the validation-gate test to confirm the forward model and the
    fit are mutually consistent (injection recovery). Fit parameters are
    normalized to O(1) (sigma in units of `initial_guess_mas`) before fitting,
    per CLAUDE_TASK.md's requirement, so the covariance conditioning check in
    `check_fit_convergence` is meaningful.
    """
    offsets = np.asarray(offsets_mas, dtype=float)
    y = np.asarray(throughput, dtype=float)
    if offsets.size < 3:
        raise InsufficientDataError("need at least 3 offset points to fit an effective sigma")
    if offsets.shape != y.shape:
        raise DataSchemaError("offsets_mas and throughput must have the same shape")

    scale = initial_guess_mas

    def model(dx: np.ndarray, sigma_norm: float) -> np.ndarray:
        return _gaussian_aperture_1d_model(dx, sigma_norm * scale, open_width_mas)

    try:
        popt, pcov = curve_fit(model, offsets, y, p0=[1.0])
    except RuntimeError as exc:
        raise ConvergenceError(f"effective-sigma fit did not converge: {exc}") from exc

    residuals = y - model(offsets, *popt)
    dof = offsets.size - 1
    convergence = check_fit_convergence(pcov, residuals=residuals, dof=dof)

    return SigmaRecoveryResult(
        injected_sigma_mas=float("nan"),
        recovered_sigma_mas=float(popt[0] * scale),
        convergence=convergence,
    )


@dataclass(frozen=True)
class PipelineResult:
    monte_carlo: MonteCarloRunResult
    offset_sweep: list[ThroughputSweepPoint]
    wavelength_sweep: list[ThroughputSweepPoint]
    failed_shutter_heatmap: np.ndarray
    throughput_bootstrap: BootstrapResult
    warnings: list[str] = field(default_factory=list)


def run_pipeline(
    config: AnalysisConfig,
    n_trials: int,
    geometry: MSAGeometry | None = None,
    psf_model: PSFModel | None = None,
    seed: int | None = None,
) -> PipelineResult:
    """Run the full Monte Carlo NIRSpec MSA throughput sandbox pipeline.

    Composes: `monte_carlo.run_monte_carlo` (main trial ensemble),
    `throughput.throughput_vs_offset_sweep` / `throughput_vs_wavelength_sweep`
    (deterministic diagnostic sweeps), `monte_carlo.failed_shutter_grid`
    (illustrative operability heatmap) and `uncertainty.bootstrap_statistic`
    (Monte Carlo placement uncertainty on the mean throughput).

    Raises InsufficientDataError if `n_trials` is zero or invalid (propagated
    from `monte_carlo.generate_trials`), rather than silently returning an
    empty/degenerate result.
    """
    if n_trials <= 0:
        raise InsufficientDataError(f"run_pipeline requires n_trials > 0, got {n_trials}")

    geometry = geometry or MSAGeometry()
    psf_model = psf_model or PSFModel()
    run_seed = seed if seed is not None else config.execution.seed
    mc_cfg = config.monte_carlo

    warnings: list[str] = []

    mc_result = run_monte_carlo(
        n_trials=n_trials,
        centering_sigma_mas=mc_cfg.centering_sigma_mas,
        wavelength_min_um=mc_cfg.wavelength_min_um,
        wavelength_max_um=mc_cfg.wavelength_max_um,
        operability_fraction=mc_cfg.operability_fraction,
        geometry=geometry,
        psf_model=psf_model,
        seed=run_seed,
    )

    if mc_result.fraction_shutter_closed > 0.5:
        warnings.append(
            f"more than half of trials drew a closed shutter (fraction_shutter_closed="
            f"{mc_result.fraction_shutter_closed:.3f}); operability_fraction may be misconfigured"
        )

    fiducial_wavelength_um = float(np.mean([mc_cfg.wavelength_min_um, mc_cfg.wavelength_max_um]))
    offset_range = np.linspace(-150.0, 150.0, 25)
    offset_sweep = throughput_vs_offset_sweep(offset_range, fiducial_wavelength_um, geometry, psf_model)

    wavelength_range = np.linspace(mc_cfg.wavelength_min_um, mc_cfg.wavelength_max_um, 25)
    wavelength_sweep = throughput_vs_wavelength_sweep(
        wavelength_range, mc_cfg.centering_sigma_mas, geometry, psf_model
    )

    try:
        heatmap = failed_shutter_grid(30, 15, mc_cfg.operability_fraction, seed=run_seed + 1)
    except InsufficientDataError as exc:
        warnings.append(f"failed_shutter_grid skipped: {exc}")
        heatmap = np.zeros((0, 0), dtype=bool)

    try:
        throughput_bootstrap = bootstrap_statistic(
            mc_result.throughput,
            statistic=lambda a: float(np.mean(a)),
            n_resamples=config.validation.bootstrap_resamples,
            seed=run_seed,
            confidence_level=config.validation.confidence_level,
        )
    except InsufficientDataError as exc:
        warnings.append(f"bootstrap skipped: {exc}")
        throughput_bootstrap = BootstrapResult(
            estimate=mc_result.mean_throughput, ci_low=float("nan"), ci_high=float("nan"),
            n_resamples=0, confidence_level=config.validation.confidence_level,
        )

    if n_trials < config.validation.minimum_sample_size:
        warnings.append(
            f"n_trials={n_trials} is below the configured minimum_sample_size="
            f"{config.validation.minimum_sample_size}; summary statistics may be unstable"
        )

    return PipelineResult(
        monte_carlo=mc_result,
        offset_sweep=offset_sweep,
        wavelength_sweep=wavelength_sweep,
        failed_shutter_heatmap=heatmap,
        throughput_bootstrap=throughput_bootstrap,
        warnings=warnings,
    )


__all__ = [
    "Summary",
    "validate_numeric",
    "robust_summary",
    "demo_series",
    "SigmaRecoveryResult",
    "recover_effective_sigma",
    "PipelineResult",
    "run_pipeline",
]

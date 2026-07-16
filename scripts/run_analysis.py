"""Run the NIRSpec MSA throughput Monte Carlo sandbox: --demo (small trial
count, for CI/smoke) or the full pipeline (trial count from
config/analysis.yml -- `monte_carlo.demo_trials` or `monte_carlo.production_trials`).

Peak memory is measured with the stdlib `tracemalloc` (Python-level
allocations), consistent with the sibling projects' benchmark methodology.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import tracemalloc
from pathlib import Path

from jwst_nirspec_msa_throughput_sandbox import __version__
from jwst_nirspec_msa_throughput_sandbox.config import load_config
from jwst_nirspec_msa_throughput_sandbox.core import run_pipeline
from jwst_nirspec_msa_throughput_sandbox.geometry import MSAGeometry
from jwst_nirspec_msa_throughput_sandbox.logging_utils import get_logger
from jwst_nirspec_msa_throughput_sandbox.provenance import get_git_commit, sha256_config
from jwst_nirspec_msa_throughput_sandbox.psf import PSFModel
from jwst_nirspec_msa_throughput_sandbox.results_io import Metric, write_summary

LOGGER = get_logger(__name__)


def _write_benchmark(path: Path, label: str, wall_time_s: float, peak_memory_mib: float, dataset_size: int) -> None:
    payload = {
        "label": label,
        "wall_time_seconds": wall_time_s,
        "peak_memory_mib": peak_memory_mib,
        "peak_memory_method": "tracemalloc (Python-level allocations, not full process RSS)",
        "dataset_size": dataset_size,
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "package_version": __version__,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    existing.append(payload)
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def run(config_path: Path, results_dir: Path, n_trials: int, run_label: str) -> None:
    config = load_config(config_path)
    geometry = MSAGeometry()
    psf_model = PSFModel()

    tracemalloc.start()
    start = time.perf_counter()

    result = run_pipeline(config, n_trials=n_trials, geometry=geometry, psf_model=psf_model)

    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    mc = result.monte_carlo
    metrics = [
        Metric(name="mean_throughput", estimate=mc.mean_throughput, units="dimensionless", sample_size=mc.n_trials,
               uncertainty_low=result.throughput_bootstrap.ci_low, uncertainty_high=result.throughput_bootstrap.ci_high),
        Metric(name="median_throughput", estimate=mc.median_throughput, units="dimensionless", sample_size=mc.n_trials),
        Metric(name="fraction_shutter_closed", estimate=mc.fraction_shutter_closed, units="dimensionless", sample_size=mc.n_trials),
        Metric(name="mean_throughput_open_only", estimate=mc.mean_throughput_open_only, units="dimensionless", sample_size=mc.n_trials),
    ]
    for point in result.offset_sweep:
        metrics.append(Metric(
            name=f"throughput_vs_offset_mas_{point.parameter_value:.1f}", estimate=point.mean_throughput,
            units="dimensionless", sample_size=point.sample_size,
        ))
    for point in result.wavelength_sweep:
        metrics.append(Metric(
            name=f"throughput_vs_wavelength_um_{point.parameter_value:.3f}", estimate=point.mean_throughput,
            units="dimensionless", sample_size=point.sample_size,
        ))
    if result.failed_shutter_heatmap.size:
        metrics.append(Metric(
            name="failed_shutter_heatmap_operable_fraction",
            estimate=float(result.failed_shutter_heatmap.mean()),
            units="dimensionless", sample_size=int(result.failed_shutter_heatmap.size),
        ))

    provenance = {
        "config_sha256": sha256_config(config_path),
        "git_commit": get_git_commit(Path(__file__).resolve().parents[1]),
        "package_version": __version__,
        "n_trials": mc.n_trials,
        "run_label": run_label,
        "seed": config.execution.seed,
    }

    results_dir.mkdir(exist_ok=True)
    payload = write_summary(
        results_dir / "summary.json",
        project=config.project.title,
        data_kind="synthetic_monte_carlo",
        metrics=metrics,
        provenance=provenance,
        warnings=result.warnings,
    )
    (results_dir / "warnings.json").write_text(json.dumps(result.warnings, indent=2), encoding="utf-8")
    _write_benchmark(results_dir / "benchmarks.json", run_label, elapsed, peak / (1024 * 1024), mc.n_trials)
    print(f"Wrote {results_dir / 'summary.json'} ({len(metrics)} metrics, {len(result.warnings)} warnings, "
          f"n_trials={mc.n_trials}, wall_time={elapsed:.3f}s)")
    print(json.dumps({k: payload[k] for k in ("project", "data_kind")}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run at config monte_carlo.demo_trials (small, fast)")
    parser.add_argument("--config", type=Path, default=Path("config/analysis.yml"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--n-trials", type=int, default=None, help="Override trial count explicitly")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.n_trials is not None:
        n_trials, label = args.n_trials, "custom"
    elif args.demo:
        n_trials, label = config.monte_carlo.demo_trials, "demo"
    else:
        n_trials, label = config.monte_carlo.production_trials, "production"

    run(args.config, args.results_dir, n_trials, label)


if __name__ == "__main__":
    main()

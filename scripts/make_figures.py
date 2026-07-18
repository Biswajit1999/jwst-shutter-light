"""Generate the 4 required figures (docs/FIGURE_AND_UI_SPEC.md) as SVG + 300 dpi
PNG, each with a sidecar JSON recording git commit, config hash, sample size
and units.

--demo builds figures at config monte_carlo.demo_trials (small, fast). The
production path (no --demo) runs at monte_carlo.production_trials. Both paths
run the identical Monte Carlo model in src/jwst_nirspec_msa_throughput_sandbox
-- only the trial count differs. All figures are synthetic Monte Carlo
results (`data_kind = synthetic_monte_carlo`), never real telemetry.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scienceplots  # noqa: F401

from jwst_nirspec_msa_throughput_sandbox import __version__
from jwst_nirspec_msa_throughput_sandbox.config import load_config
from jwst_nirspec_msa_throughput_sandbox.core import run_pipeline
from jwst_nirspec_msa_throughput_sandbox.geometry import MSAGeometry, shutter_grid_centers
from jwst_nirspec_msa_throughput_sandbox.provenance import get_git_commit, sha256_config
from jwst_nirspec_msa_throughput_sandbox.psf import PSFModel

plt.style.use(["science", "no-latex"])


def _sidecar(path: Path, *, data_kind: str, sample_size: int, units: str, config_path: Path, extra: dict | None = None) -> None:
    payload = {
        "figure": path.stem,
        "data_kind": data_kind,
        "sample_size": sample_size,
        "units": units,
        "git_commit": get_git_commit(Path(__file__).resolve().parents[1]),
        "config_sha256": sha256_config(config_path) if config_path.is_file() else None,
        "package_version": __version__,
    }
    if extra:
        payload.update(extra)
    path.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _save(fig, out_dir: Path, name: str) -> Path:
    svg_path = out_dir / f"{name}.svg"
    png_path = out_dir / f"{name}.png"
    fig.savefig(svg_path)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    return png_path


def make_figures(out_dir: Path, config_path: Path, n_trials: int, run_label: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)
    geometry = MSAGeometry()
    psf_model = PSFModel()
    data_kind = "synthetic_monte_carlo"

    result = run_pipeline(config, n_trials=n_trials, geometry=geometry, psf_model=psf_model)
    mc = result.monte_carlo

    # 1. MSA geometry schematic: a small illustrative shutter sub-grid with
    # pitch/open-area annotated (real verified constants, illustrative subset
    # of the true 365x171-per-quadrant array).
    n_x, n_y = 8, 6
    xs, ys = shutter_grid_centers(geometry, n_x, n_y)
    fig, ax = plt.subplots(figsize=(8, 5))
    for xc, yc in zip(xs.ravel(), ys.ravel()):
        outer = plt.Rectangle(
            (xc - geometry.pitch_x_mas / 2, yc - geometry.pitch_y_mas / 2),
            geometry.pitch_x_mas, geometry.pitch_y_mas,
            fill=False, edgecolor="0.6", linewidth=0.8,
        )
        inner = plt.Rectangle(
            (xc - geometry.open_width_mas / 2, yc - geometry.open_height_mas / 2),
            geometry.open_width_mas, geometry.open_height_mas,
            fill=True, facecolor="tab:blue", alpha=0.5, edgecolor="tab:blue",
        )
        ax.add_patch(outer)
        ax.add_patch(inner)
    ax.set_xlim(xs.min() - geometry.pitch_x_mas, xs.max() + geometry.pitch_x_mas)
    ax.set_ylim(ys.min() - geometry.pitch_y_mas, ys.max() + geometry.pitch_y_mas)
    ax.set_aspect("equal")
    ax.set_xlabel("Dispersion direction offset (mas)")
    ax.set_ylabel("Spatial direction offset (mas)")
    ax.set_title(
        f"NIRSpec MSA shutter geometry (illustrative {n_x}x{n_y} sub-grid of {geometry.total_shutters} total)\n"
        f"pitch {geometry.pitch_x_mas:.0f}x{geometry.pitch_y_mas:.0f} mas, open aperture "
        f"{geometry.open_width_mas:.0f}x{geometry.open_height_mas:.0f} mas "
        "(Ferruit et al. 2022, verified)"
    )
    path = _save(fig, out_dir, "fig01_msa_geometry")
    _sidecar(path, data_kind="verified_instrument_parameters", sample_size=n_x * n_y, units="milliarcsec", config_path=config_path)

    # 2. throughput vs centering offset
    offsets = np.array([p.parameter_value for p in result.offset_sweep])
    tvals = np.array([p.mean_throughput for p in result.offset_sweep])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(offsets, tvals, "-o", color="tab:blue")
    ax.axvline(0, color="black", lw=0.5, ls=":")
    ax.set_xlabel("Target-centering offset, dispersion direction (mas)")
    ax.set_ylabel("Geometric slit throughput")
    ax.set_title(
        f"Throughput vs centering offset — {run_label.upper()} MONTE CARLO (n={n_trials} trials in main ensemble)\n"
        f"fixed wavelength {np.mean([config.monte_carlo.wavelength_min_um, config.monte_carlo.wavelength_max_um]):.2f} um, all shutters open"
    )
    ax.set_ylim(-0.02, 1.02)
    path = _save(fig, out_dir, "fig02_throughput_vs_offset")
    _sidecar(path, data_kind=data_kind, sample_size=len(offsets), units="dimensionless throughput vs mas", config_path=config_path,
             extra={"n_trials_main_ensemble": n_trials})

    # 3. throughput vs wavelength
    wavelengths = np.array([p.parameter_value for p in result.wavelength_sweep])
    tvals_w = np.array([p.mean_throughput for p in result.wavelength_sweep])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(wavelengths, tvals_w, "-o", color="tab:red")
    ax.axvline(2.46, color="0.5", ls="--", lw=1, label="diffraction-limit onset (2.46 um, verified)")
    ax.set_xlabel("Wavelength (um)")
    ax.set_ylabel("Geometric slit throughput")
    ax.set_title(
        f"Throughput vs wavelength — {run_label.upper()} MONTE CARLO\n"
        f"fixed centering offset = centering_sigma_mas ({config.monte_carlo.centering_sigma_mas:.0f} mas), all shutters open"
    )
    ax.set_ylim(-0.02, 1.02)
    ax.legend()
    path = _save(fig, out_dir, "fig03_wavelength_loss")
    _sidecar(path, data_kind=data_kind, sample_size=len(wavelengths), units="dimensionless throughput vs micron", config_path=config_path)

    # 4. failed-shutter heatmap (illustrative synthetic realization at the
    # verified aggregate operability fraction; NOT a real per-shutter map)
    heatmap = result.failed_shutter_heatmap
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if heatmap.size:
        im = ax.imshow(heatmap, cmap="Greens", vmin=0, vmax=1, aspect="auto", origin="lower")
        fig.colorbar(im, ax=ax, label="Operable (1) / failed-closed (0)")
    ax.set_xlabel("Shutter column (illustrative sub-grid)")
    ax.set_ylabel("Shutter row (illustrative sub-grid)")
    operable_fraction = float(heatmap.mean()) if heatmap.size else float("nan")
    ax.set_title(
        f"Synthetic illustrative shutter-operability realization "
        f"(independent Bernoulli draws @ verified aggregate {config.monte_carlo.operability_fraction:.1%}, "
        f"realized {operable_fraction:.1%})\nNOT a real MSA operability map — see docs/ASSUMPTIONS_AND_LIMITATIONS.md"
    )
    path = _save(fig, out_dir, "fig04_failed_shutter_heatmap")
    _sidecar(path, data_kind="synthetic_illustrative", sample_size=int(heatmap.size), units="boolean operable mask", config_path=config_path)

    print(f"Wrote 4 figures (SVG+PNG+JSON) to {out_dir} at n_trials={n_trials} ({run_label})")
    print(f"  mean_throughput={mc.mean_throughput:.4f} median={mc.median_throughput:.4f} "
          f"fraction_shutter_closed={mc.fraction_shutter_closed:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=Path("figures"))
    parser.add_argument("--config", type=Path, default=Path("config/analysis.yml"))
    parser.add_argument("--n-trials", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    if args.n_trials is not None:
        n_trials, label = args.n_trials, "custom"
    elif args.demo:
        n_trials, label = config.monte_carlo.demo_trials, "demo"
    else:
        n_trials, label = config.monte_carlo.production_trials, "production"

    make_figures(args.out_dir, args.config, n_trials, label)


if __name__ == "__main__":
    main()

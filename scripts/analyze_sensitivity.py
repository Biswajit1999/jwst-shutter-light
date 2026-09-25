"""Run the predeclared centering and random command-failure sensitivity grid."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from jwst_nirspec_msa_throughput_sandbox.config import load_config
from jwst_nirspec_msa_throughput_sandbox.geometry import MSAGeometry
from jwst_nirspec_msa_throughput_sandbox.monte_carlo import run_monte_carlo
from jwst_nirspec_msa_throughput_sandbox.psf import PSFModel

CENTERING_SIGMA_MAS = (10.0, 20.0, 25.0, 100.0)
COMMAND_FAILURE_FRACTIONS = (0.0, 0.01, 0.02, 0.03, 0.04)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "config" / "analysis.yml")
    rows: list[dict[str, float | int]] = []
    geometry = MSAGeometry()
    psf = PSFModel()

    for sigma in CENTERING_SIGMA_MAS:
        for failure in COMMAND_FAILURE_FRACTIONS:
            result = run_monte_carlo(
                n_trials=config.monte_carlo.production_trials,
                centering_sigma_mas=sigma,
                wavelength_min_um=config.monte_carlo.wavelength_min_um,
                wavelength_max_um=config.monte_carlo.wavelength_max_um,
                command_success_probability=1.0 - failure,
                geometry=geometry,
                psf_model=psf,
                seed=config.execution.seed,
            )
            rows.append(
                {
                    "centering_sigma_mas": sigma,
                    "command_failure_fraction": failure,
                    "n_trials": result.n_trials,
                    "mean_geometric_throughput_given_success": result.mean_geometric_throughput,
                    "mean_effective_throughput": result.mean_effective_throughput,
                }
            )

    output = root / "results"
    output.mkdir(exist_ok=True)
    csv_path = output / "sensitivity_designs.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "design_count": len(rows),
        "centering_sigma_mas": list(CENTERING_SIGMA_MAS),
        "command_failure_fractions": list(COMMAND_FAILURE_FRACTIONS),
        "primary_design": {
            "centering_sigma_mas": 20.0,
            "command_failure_fraction": 0.04,
        },
        "conditional_geometric_throughput_range": [
            min(float(row["mean_geometric_throughput_given_success"]) for row in rows),
            max(float(row["mean_geometric_throughput_given_success"]) for row in rows),
        ],
        "effective_throughput_range": [
            min(float(row["mean_effective_throughput"]) for row in rows),
            max(float(row["mean_effective_throughput"]) for row in rows),
        ],
        "claim_boundary": (
            "Synthetic Gaussian-PSF sensitivity scenarios, not predictions for a specific "
            "planned MOS target, MPT configuration, exposure, or calibrated spectrum."
        ),
    }
    (output / "sensitivity.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(rows)} sensitivity designs to {csv_path}")


if __name__ == "__main__":
    main()

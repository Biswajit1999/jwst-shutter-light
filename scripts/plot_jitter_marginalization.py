"""Reproduce the conditional MSA jitter-correlation diagnostic PNG."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from jwst_nirspec_msa_throughput_sandbox.jitter_marginalization import correlated_jitter_mean

plt.switch_backend("Agg")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/jitter_correlation.png"))
    args = parser.parse_args()
    rho = np.linspace(-0.9, 0.9, 19)
    fig, ax = plt.subplots(figsize=(7.5, 4.7))
    for order in (16, 32, 80):
        y = [correlated_jitter_mean(35, 80, jitter_sigma_x=35,
             jitter_sigma_y=100, rho=float(r), order=order) for r in rho]
        ax.plot(rho, y, marker="." if order == 80 else None, label=f"GH order {order}")
    ax.set(xlabel="Assumed acquisition-error correlation ρ",
           ylabel="Mean geometric slit transmission",
           title="Synthetic NIRSpec MSA stress test (not a calibrated path loss)")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()

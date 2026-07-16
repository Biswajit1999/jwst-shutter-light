"""Verify (re-check) the already-recorded official-parameter provenance manifest.

Per docs/DATASET_PLAN.md, this project's mode is "official instrument
parameters + synthetic Monte Carlo" -- there is no archive download step.
Parameter verification against real sources (JDox / arXiv / NASA) was
performed via WebFetch during the implementation session and recorded in
`data/manifest.csv` and `data/provenance.yml`. This script re-checks that
manifest for internal consistency (all required columns present, no blank
source URLs, sha256 present) and prints a verification report -- it performs
no network calls at run time and downloads/modifies nothing.

The `--i-have-authorization` flag is kept only for CLI-pattern consistency
with the sibling archive-download projects; it carries no actual risk here
since nothing destructive or costly happens regardless.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from jwst_nirspec_msa_throughput_sandbox.exceptions import ProvenanceError
from jwst_nirspec_msa_throughput_sandbox.logging_utils import get_logger
from jwst_nirspec_msa_throughput_sandbox.provenance import read_manifest

LOGGER = get_logger(__name__)

EXPECTED_PRODUCT_IDS = (
    "shutter_pitch_mas",
    "shutter_open_area_mas",
    "msa_array_layout",
    "shutter_operability_fraction",
    "nirspec_wavelength_range_um",
    "psf_fwhm_anchor_2p5um",
    "jwst_mirror_diameter_m",
    "msa_target_acquisition_accuracy_mas",
)


def verify_manifest(manifest_path: Path) -> list[str]:
    """Return a list of human-readable issues; empty list means the manifest is consistent."""
    rows = read_manifest(manifest_path)
    issues: list[str] = []
    found_ids = {row["product_id"] for row in rows}

    missing = set(EXPECTED_PRODUCT_IDS) - found_ids
    if missing:
        issues.append(f"missing expected parameter rows: {sorted(missing)}")

    for row in rows:
        if not row["source_url"].startswith(("http://", "https://")):
            issues.append(f"{row['product_id']}: source_url does not look like a URL: {row['source_url']!r}")
        if not row["sha256"] or row["sha256"] == "TODO_VERIFY":
            issues.append(f"{row['product_id']}: sha256 not recorded (TODO_VERIFY)")
        if not row["retrieved_utc"]:
            issues.append(f"{row['product_id']}: retrieved_utc is blank")

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.csv"))
    parser.add_argument(
        "--i-have-authorization",
        action="store_true",
        help="No-op flag kept for CLI-pattern consistency; this script performs no network access.",
    )
    args = parser.parse_args()

    try:
        issues = verify_manifest(args.manifest)
    except ProvenanceError as exc:
        raise SystemExit(f"Cannot verify manifest: {exc}") from exc

    if issues:
        for issue in issues:
            LOGGER.warning(issue)
        raise SystemExit(f"Manifest verification found {len(issues)} issue(s); see warnings above.")

    print(f"Manifest OK: {len(EXPECTED_PRODUCT_IDS)} verified instrument parameters recorded in {args.manifest}")


if __name__ == "__main__":
    main()

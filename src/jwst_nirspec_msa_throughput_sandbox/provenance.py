"""Provenance recording.

For this project (data_mode = "official instrument parameters + synthetic
Monte Carlo"), `data/manifest.csv` does not record downloaded archive
products — it records the SOURCE of each verified physical instrument
parameter used in the model. The manifest schema is reused as-is
(`product_id, source, source_url, retrieved_utc, sha256, file_size_bytes,
selection_reason, licence_or_terms`) with the following field reinterpretation,
documented here per docs/VALIDATION_CONTRACT.md's requirement to document any adaptation:

- `product_id`   -> the parameter name (e.g. "shutter_pitch_mas")
- `source`       -> short citation key (e.g. "Ferruit et al. 2022")
- `source_url`   -> the exact JDox page or arXiv/DOI URL verified via WebFetch
- `retrieved_utc`-> when the parameter was verified in this implementation session
- `sha256`       -> sha256 of the parameter's literal string value (not a file),
                     so the column is still populated and independently
                     recomputable, rather than left blank
- `file_size_bytes` -> 0 (no file downloaded)
- `selection_reason` -> what the parameter is used for in the model
- `licence_or_terms` -> the source's stated re-use terms (arXiv/A&A open
                     access, or "public JWST User Documentation")
"""
from __future__ import annotations

import csv
import subprocess
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

from jwst_nirspec_msa_throughput_sandbox.exceptions import ProvenanceError

MANIFEST_COLUMNS = (
    "product_id",
    "source",
    "source_url",
    "retrieved_utc",
    "sha256",
    "file_size_bytes",
    "selection_reason",
    "licence_or_terms",
)


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def sha256_config(config_path: str | Path) -> str:
    return sha256_file(config_path)


def get_git_commit(repo_dir: str | Path) -> str:
    """Return the short commit hash for repo_dir, or 'LOCAL_UNCOMMITTED' if unavailable.

    Read-only (`git rev-parse` never mutates repository state). Never raises: a
    missing git binary or an uninitialised/non-git directory are both expected
    states for this local-implementation workflow (this project directory is
    not a git repository).
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "LOCAL_UNCOMMITTED"
    if result.returncode != 0:
        return "LOCAL_UNCOMMITTED"
    return result.stdout.strip() or "LOCAL_UNCOMMITTED"


@dataclass(frozen=True)
class ManifestRow:
    product_id: str
    source: str
    source_url: str
    retrieved_utc: str
    sha256: str
    file_size_bytes: int
    selection_reason: str
    licence_or_terms: str


def append_manifest_row(manifest_path: str | Path, row: ManifestRow) -> None:
    path = Path(manifest_path)
    row_dict = asdict(row)
    missing = [c for c in MANIFEST_COLUMNS if c not in row_dict]
    if missing:
        raise ProvenanceError(f"manifest row missing required columns: {missing}")

    file_exists = path.is_file() and path.stat().st_size > 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MANIFEST_COLUMNS))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)


def read_manifest(manifest_path: str | Path) -> list[dict[str, str]]:
    path = Path(manifest_path)
    if not path.is_file():
        raise ProvenanceError(f"manifest file not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    for row in rows:
        missing = [c for c in MANIFEST_COLUMNS if c not in row]
        if missing:
            raise ProvenanceError(f"manifest row missing required columns: {missing}")
    return rows


__all__ = [
    "MANIFEST_COLUMNS",
    "ManifestRow",
    "append_manifest_row",
    "read_manifest",
    "get_git_commit",
    "sha256_bytes",
    "sha256_config",
    "sha256_file",
    "sha256_text",
]

class ProjectError(RuntimeError):
    """Base exception for actionable project failures."""


class DataSchemaError(ProjectError):
    """Raised when an input product (config, manifest, parameter table) does not match the documented schema."""


class ProvenanceError(ProjectError):
    """Raised when required provenance metadata are absent or inconsistent."""


class ArchiveAccessError(ProjectError):
    """Raised when an archive/documentation query cannot be completed or verified.

    Unused in the normal run path for this project (no archive downloads are
    performed — see docs/DATASET_PLAN.md, mode = "official instrument
    parameters + synthetic Monte Carlo"), but kept defined for consistency
    with the sibling projects' exception hierarchy and for
    scripts/fetch_data.py's parameter-verification error paths.
    """


class ConvergenceError(ProjectError):
    """Raised when a numerical fit or iterative method fails to converge."""


class InsufficientDataError(ProjectError):
    """Raised when a sample (e.g. zero Monte Carlo trials) is too small or too degenerate to report a metric."""

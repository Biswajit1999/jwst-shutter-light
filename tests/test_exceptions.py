from __future__ import annotations

from jwst_nirspec_msa_throughput_sandbox.exceptions import (
    ArchiveAccessError,
    ConvergenceError,
    DataSchemaError,
    InsufficientDataError,
    ProjectError,
    ProvenanceError,
)


def test_exception_hierarchy():
    for exc_cls in (DataSchemaError, ProvenanceError, ArchiveAccessError, ConvergenceError, InsufficientDataError):
        assert issubclass(exc_cls, ProjectError)
        assert issubclass(exc_cls, RuntimeError)


def test_exceptions_carry_message():
    try:
        raise InsufficientDataError("no trials")
    except ProjectError as exc:
        assert "no trials" in str(exc)

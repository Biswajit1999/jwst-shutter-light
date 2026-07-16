from __future__ import annotations

import numpy as np
import pytest
from scipy.optimize import curve_fit

from jwst_nirspec_msa_throughput_sandbox.exceptions import ConvergenceError, InsufficientDataError
from jwst_nirspec_msa_throughput_sandbox.uncertainty import bootstrap_statistic, check_fit_convergence


def test_bootstrap_statistic_reproducible_with_seed():
    data = np.random.default_rng(0).normal(size=200)
    r1 = bootstrap_statistic(data, np.mean, n_resamples=1000, seed=20260713)
    r2 = bootstrap_statistic(data, np.mean, n_resamples=1000, seed=20260713)
    assert r1.ci_low == pytest.approx(r2.ci_low)
    assert r1.ci_high == pytest.approx(r2.ci_high)
    assert r1.n_resamples == 1000


def test_bootstrap_statistic_ci_contains_estimate():
    data = np.random.default_rng(1).normal(loc=5.0, scale=1.0, size=500)
    result = bootstrap_statistic(data, np.mean, n_resamples=1000, seed=20260713)
    assert result.ci_low <= result.estimate <= result.ci_high


def test_bootstrap_statistic_rejects_too_few_samples():
    with pytest.raises(InsufficientDataError):
        bootstrap_statistic(np.array([1.0]), np.mean, n_resamples=100, seed=1)


def test_bootstrap_statistic_rejects_bad_confidence_level():
    data = np.arange(10.0)
    with pytest.raises(ValueError):
        bootstrap_statistic(data, np.mean, n_resamples=100, seed=1, confidence_level=1.5)


def test_check_fit_convergence_well_conditioned():
    def line(x, a, b):
        return a * x + b

    x = np.linspace(0, 1, 50)
    y = 2.0 * x + 1.0 + np.random.default_rng(0).normal(scale=0.01, size=50)
    popt, pcov = curve_fit(line, x, y)
    residuals = y - line(x, *popt)
    result = check_fit_convergence(pcov, residuals=residuals, dof=len(x) - 2)
    assert result.converged is True
    assert result.covariance_condition_number > 0
    assert result.reduced_chi_square is not None


def test_check_fit_convergence_rejects_non_finite_covariance():
    pcov = np.array([[np.nan, 0.0], [0.0, 1.0]])
    with pytest.raises(ConvergenceError):
        check_fit_convergence(pcov)


def test_check_fit_convergence_rejects_ill_conditioned():
    pcov = np.array([[1e20, 0.0], [0.0, 1e-20]])
    with pytest.raises(ConvergenceError):
        check_fit_convergence(pcov, max_condition_number=1e10)


def test_check_fit_convergence_rejects_non_square():
    with pytest.raises(ConvergenceError):
        check_fit_convergence(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))


def test_check_fit_convergence_rejects_non_positive_dof():
    pcov = np.eye(2)
    with pytest.raises(ConvergenceError):
        check_fit_convergence(pcov, residuals=np.array([0.1, 0.2]), dof=0)

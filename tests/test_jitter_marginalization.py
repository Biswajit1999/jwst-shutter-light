"""Independent limiting cases and seeded synthetic injection tests."""
import numpy as np
import pytest

from jwst_nirspec_msa_throughput_sandbox.jitter_marginalization import (
    analytic_jitter_mean, correlated_jitter_mean, diagnostic_report,
    geometric_transmission, local_sensitivities,
)


def test_zero_jitter_equals_direct_aperture():
    expected = float(geometric_transmission(12, -8))
    assert analytic_jitter_mean(12, -8, jitter_sigma_x=0, jitter_sigma_y=0) == pytest.approx(expected)


def test_analytic_marginal_matches_seeded_monte_carlo():
    rng = np.random.default_rng(304)
    x = rng.normal(20, 25, 150_000)
    y = rng.normal(-10, 15, 150_000)
    mc = float(np.mean(geometric_transmission(x, y)))
    exact = analytic_jitter_mean(20, -10, jitter_sigma_x=25, jitter_sigma_y=15)
    assert mc == pytest.approx(exact, abs=0.002)


def test_uncorrelated_quadrature_converges_to_closed_form():
    expected = analytic_jitter_mean(35, 15, jitter_sigma_x=35, jitter_sigma_y=25)
    actual = correlated_jitter_mean(35, 15, jitter_sigma_x=35, jitter_sigma_y=25, rho=0, order=32)
    assert actual == pytest.approx(expected, abs=1e-10)


def test_correlated_quadrature_matches_seeded_mc():
    rng = np.random.default_rng(24)
    cov = np.array([[35**2, 0.7 * 35 * 25], [0.7 * 35 * 25, 25**2]])
    offsets = rng.multivariate_normal([35, 15], cov, 180_000)
    mc = float(np.mean(geometric_transmission(offsets[:, 0], offsets[:, 1])))
    quad = correlated_jitter_mean(35, 15, jitter_sigma_x=35, jitter_sigma_y=25,
                                  rho=0.7, order=32)
    assert mc == pytest.approx(quad, abs=0.002)


def test_correlation_changes_conditional_transmission():
    lo = correlated_jitter_mean(35, 80, jitter_sigma_x=35, jitter_sigma_y=100, rho=-0.8, order=32)
    hi = correlated_jitter_mean(35, 80, jitter_sigma_x=35, jitter_sigma_y=100, rho=0.8, order=32)
    assert abs(lo - hi) > 1e-4
    assert 0 <= lo <= 1 and 0 <= hi <= 1


def test_local_sensitivity_sign_and_step_convergence():
    fine = local_sensitivities(step_mas=0.05)
    coarse = local_sensitivities(step_mas=0.2)
    assert fine["d_mean_d_offset_per_mas"] < 0
    assert fine["d_mean_d_jitter_per_mas"] < 0
    for key in fine:
        assert fine[key] == pytest.approx(coarse[key], abs=1e-6)


def test_invalid_covariance_and_dimensions_rejected():
    with pytest.raises(ValueError):
        correlated_jitter_mean(0, 0, jitter_sigma_x=20, jitter_sigma_y=20, rho=1.01)
    with pytest.raises(ValueError):
        analytic_jitter_mean(jitter_sigma_x=-1)
    with pytest.raises(ValueError):
        geometric_transmission(0, 0, width=0)
    with pytest.raises(ValueError):
        correlated_jitter_mean(0, 0, jitter_sigma_x=20, jitter_sigma_y=20, rho=0, order=1)


def test_diagnostic_grid_has_converged_high_order():
    report = diagnostic_report()
    assert all(abs(item["order_64_to_80_delta"]) < 1e-7 for item in report["correlation_sweep"])

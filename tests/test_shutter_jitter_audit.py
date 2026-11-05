import unittest
from math import erf, sqrt
from research.shutter_jitter_audit import (
    axis_fraction, rectangular_throughput, jitter_marginal,
    correlated_jitter_quadrature, offset_sensitivity)


class TestShutterJitter(unittest.TestCase):
    def test_centered_erf_limit(self):
        self.assertAlmostEqual(axis_fraction(2, 1), erf(1/sqrt(2)))

    def test_symmetry(self):
        self.assertAlmostEqual(axis_fraction(1, .2, .1), axis_fraction(1, .2, -.1))

    def test_offset_reduces_throughput(self):
        self.assertGreater(rectangular_throughput(1, 1, .2, .2),
                           rectangular_throughput(1, 1, .2, .2, .3))

    def test_zero_jitter(self):
        self.assertAlmostEqual(jitter_marginal(1, 1, .2, .2, 0, 0),
                               rectangular_throughput(1, 1, .2, .2))

    def test_quadrature_independent_matches_analytic(self):
        q = correlated_jitter_quadrature(1, .8, .3, .25, .1, .1, 0, order=28)
        a = jitter_marginal(1, .8, .3, .25, .1, .1)
        self.assertAlmostEqual(q, a, delta=2e-7)

    def test_correlation_sign_at_center(self):
        a = correlated_jitter_quadrature(1, .8, .3, .25, .1, .1, .5)
        b = correlated_jitter_quadrature(1, .8, .3, .25, .1, .1, -.5)
        self.assertAlmostEqual(a, b, delta=1e-8)

    def test_centered_curvature_negative(self):
        result = offset_sensitivity(1, 1, .2, .2)
        self.assertLess(result["x_curvature"], 0)
        self.assertLess(result["y_curvature"], 0)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            axis_fraction(1, 0)
        with self.assertRaises(ValueError):
            correlated_jitter_quadrature(1, 1, .2, .2, .1, .1, 1)


if __name__ == "__main__":
    unittest.main()

"""Conditional Gaussian PSF transmission through a rectangular open shutter.

Not a calibrated JWST/NIRSpec path-loss model. Angular/length units must agree.
"""
from math import erf, sqrt, pi
import numpy as np
from numpy.polynomial.hermite import hermgauss


def axis_fraction(width, sigma, offset=0.0):
    """Integral of normalized 1-D Gaussian across [-width/2, width/2]."""
    if width <= 0 or sigma <= 0 or not np.isfinite([width, sigma, offset]).all():
        raise ValueError("Positive width/sigma and finite offset required")
    return .5*(erf((width/2-offset)/(sqrt(2)*sigma)) -
               erf((-width/2-offset)/(sqrt(2)*sigma)))


def rectangular_throughput(width, height, sigma_x, sigma_y, dx=0., dy=0.):
    """Separable geometric throughput for an operable commanded-open shutter."""
    return axis_fraction(width, sigma_x, dx)*axis_fraction(height, sigma_y, dy)


def jitter_marginal(width, height, sigma_x, sigma_y, jitter_x, jitter_y,
                    mean_x=0., mean_y=0.):
    """Exact mean throughput for independent Gaussian pointing jitter."""
    if jitter_x < 0 or jitter_y < 0:
        raise ValueError("Jitter standard deviations must be nonnegative")
    return rectangular_throughput(width, height,
                                  np.hypot(sigma_x, jitter_x),
                                  np.hypot(sigma_y, jitter_y), mean_x, mean_y)


def correlated_jitter_quadrature(width, height, sigma_x, sigma_y,
                                  jitter_x, jitter_y, rho, mean_x=0., mean_y=0.,
                                  order=18):
    """2-D Gauss-Hermite expectation for correlated Gaussian acquisition offsets."""
    if not -1 < rho < 1 or jitter_x < 0 or jitter_y < 0 or order < 3:
        raise ValueError("Require |rho|<1, nonnegative jitter and order>=3")
    nodes, weights = hermgauss(order)
    total = 0.
    for i, x in enumerate(nodes):
        dx = mean_x + sqrt(2)*jitter_x*x
        for j, y in enumerate(nodes):
            dy = mean_y + sqrt(2)*jitter_y*(rho*x+sqrt(1-rho*rho)*y)
            total += weights[i]*weights[j]*rectangular_throughput(
                width, height, sigma_x, sigma_y, dx, dy)
    return float(total/pi)


def offset_sensitivity(width, height, sigma_x, sigma_y, step=0.01):
    """Central finite-difference throughput curvature at perfect centering."""
    if step <= 0:
        raise ValueError("step must be positive")
    t0 = rectangular_throughput(width, height, sigma_x, sigma_y)
    tx = rectangular_throughput(width, height, sigma_x, sigma_y, step, 0)
    ty = rectangular_throughput(width, height, sigma_x, sigma_y, 0, step)
    return {"centered": t0, "x_curvature": 2*(tx-t0)/step**2,
            "y_curvature": 2*(ty-t0)/step**2}

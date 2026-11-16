# Conditional shutter acquisition-jitter audit — 16 November 2026

Two distinct diagnostics: exact marginalization of independent Gaussian pointing jitter into Gaussian PSF widths; and correlated two-axis jitter expectation by deterministic Gauss-Hermite quadrature. Rectangular geometric aperture, separable Gaussian PSF, stationary Gaussian pointing offsets and **successfully opened shutter** are assumed. Neither is calibrated JWST/NIRSpec path-loss correction, and neither uses the separate operability scenario.

Widths, PSF sigma, offsets and jitter sigma must use the same angular units. Correlation |rho|<1; quadrature convergence must be checked when using narrow apertures or large jitter. The illustrative values in the tests are synthetic, not measured. Run `python -m pytest -q` from this directory and `python make_diagnostic.py` to generate a synthetic sensitivity figure.

This complements, rather than changes, the repository's 20,000-trial Monte Carlo results. AI-assisted implementation is disclosed. No restricted data or observational products were changed.

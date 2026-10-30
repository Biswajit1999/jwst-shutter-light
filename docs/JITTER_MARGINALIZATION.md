# Conditional NIRSpec MSA pointing-error robustness (30 October 2026)

Research issue: #1. This analysis adds three independent checks to the existing Gaussian-PSF micro-shutter sandbox. It does not change the headline estimator, current source data, or official STScI path-loss calibration.

## Methods

1. **Analytic acquisition-jitter marginalization.** The model assumes a separable Gaussian PSF with axis widths `sigma_psf,x/y` and independent Gaussian acquisition errors with mean offsets `mu_x/y` and RMS `sigma_j,x/y`. Gaussian convolution replaces each PSF variance by `sigma_psf^2 + sigma_j^2`. The rectangular aperture integral is then evaluated with normal CDFs. This gives the *expectation* over a declared pointing-error distribution, not a confidence interval or a measurement of a particular target.
2. **Correlated two-axis pointing errors.** A covariance matrix with correlation `rho` is eigendecomposed and integrated with tensor-product Gauss-Hermite quadrature. Compare orders 16, 32, 64, and 80, and use an independent seeded Monte Carlo check. For large spatial-axis errors, order 16 is visibly insufficient; do not interpret an unconverged quadrature as a physical effect.
3. **Local sensitivity derivatives.** Central differences estimate derivatives of mean geometric transmission with respect to dispersion-axis systematic offset and pointing RMS, both in units of per mas. Repeat at different steps to check truncation error.

## Inputs and provenance

The geometric aperture is **199 mas × 461 mas**, from the repository's `geometry.py` / Ferruit et al. (2022). The **80 mas FWHM at 2.5 μm** is from the existing `psf.py` / Jakobsen et al. (2022). The adopted 20–100 mas acquisition RMS values and 35/80 mas stress-test offsets are **hypothetical**, not measured JWST jitter. A 100 mas spatial RMS is deliberately exaggerated to expose correlation sensitivity. No external observations or new archive products were used.

## Reproduction

```bash
python -m pip install -e '.[dev]'
python -m pytest -q tests/test_jitter_marginalization.py
python -m jwst_nirspec_msa_throughput_sandbox.jitter_marginalization --output results/jitter_marginalization.json
python scripts/plot_jitter_marginalization.py --output results/jitter_correlation.png
```

The existing `pytest -q` and `ruff check src tests scripts` remain mandatory before merging. `results/` is a generated artifact directory, not a data source. All tests are controlled synthetic and analytic limits. In particular, static shutter operability must **not** be multiplied into the conditional geometric throughput; the separate random non-opening scenario remains governed by the existing repository audit. No detector throughput, true asymmetric PSF, wavefront error, MPT target placement, or measured acquisition covariance is modelled.

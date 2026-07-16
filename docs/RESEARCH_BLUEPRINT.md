# Research Blueprint

## Technical title

JWST/NIRSpec Micro-Shutter Throughput Loss Sandbox

## Category

Astrophysics instrumentation / modelling

## Bounded scientific question

How do target-centering error, wavelength-dependent PSF width and shutter operability alter simplified NIRSpec MSA throughput?

## Gap statement

An instrument-physics QA sandbox; not a replacement for the JWST pipeline or official path-loss corrections.

## First-release scope

The first release must be completable as a focused 4–6 hour implementation pass after data access is working. It must deliver one reproducible analysis pipeline, one deterministic example/smoke dataset, tests, 4–6 figures, a concise TeX report and a deployable research webpage.

## Validation and uncertainty

- Monte Carlo placement uncertainty
- throughput bounds
- wavelength sensitivity
- operability-mask sensitivity

## Required figures

1. MSA geometry
2. throughput vs offset
3. wavelength loss
4. failed-shutter heatmap

## Reusable scientific modules

- `geometry.py`
- `psf.py`
- `throughput.py`
- `monte_carlo.py`
- `plotting.py`
- `provenance.py`

## Explicit exclusions

- No novelty claim beyond the bounded dataset/question/method combination.
- No causal claim from descriptive catalogue correlations.
- No hidden manual data editing.
- No unsupported precision beyond the input uncertainties.
- No production-pipeline replacement claim.

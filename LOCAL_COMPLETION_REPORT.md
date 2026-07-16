# Local Completion Report — JWST/NIRSpec Micro-Shutter Throughput Loss Sandbox

Author: Biswajit Jana. This report documents a local implementation pass
(project 8 of the 30-project pack, `BUILD_FIRST` priority 9.0/10). No git operations
were performed. Nothing has been published.

## 1. Environment

- New dedicated conda env `jwst-nirspec-msa-throughput-sandbox` (Python 3.11),
  pinned to this project's own `pyproject.toml`: numpy==1.26.4, scipy==1.13.1,
  pandas==2.2.2, matplotlib==3.9.0, pyyaml==6.0.1, astropy==6.1.0 (no
  astroquery/photutils — no archive access needed for this project); dev:
  pytest==8.2.2, pytest-cov==5.0.0, ruff==0.5.5, mypy==1.10.1, types-PyYAML
  (added this session, along with a `[tool.mypy]` override block for scipy).
- No local LaTeX toolchain.

## 2. Files created or changed

Foundation, data layer (`scripts/fetch_data.py` — verifies instrument-parameter
manifest, no network download since this project's data mode is
verified-parameters + Monte Carlo, not archive access), scientific modules
(`geometry.py`, `psf.py`, `throughput.py`, `monte_carlo.py`, `core.py`,
`uncertainty.py`), 11 test files (76 tests), figures/report (`scripts/make_figures.py`,
`reports/report.tex` — Results section filled in this session with real production
numbers, `reports/references.bib`), and the web dashboard (already fixed by an
earlier pass: `eslint.config.js`, `recharts` removed, `App.jsx`, `project.json`).
This session's changes: fixed a CSV-quoting bug in `data/manifest.csv`, fixed a
real mypy type error in `geometry.shutter_grid_centers`, added `types-PyYAML` +
mypy overrides to `pyproject.toml`, ran the full production Monte Carlo and
regenerated figures, filled in `reports/report.tex` Results, wrote this report
and `_PROJECT_LOG.md`.

## 3. Exact commands run (in order)

```bash
python -m pip install -e ".[dev]"
pytest -q                                  # 76 passed
ruff check src tests scripts               # All checks passed
mypy src                                   # Success: no issues found in 13 source files
python scripts/run_analysis.py --demo      # n_trials=200
python scripts/run_analysis.py             # n_trials=20000 (production)
python scripts/make_figures.py             # production-scale figures
python scripts/sync_web_assets.py
cd web-react && npm install && npm run lint && npm run build
```

## 4. Test / lint / build results

- **pytest**: 76 tests passed, 0 failed.
- **ruff**: clean on `src tests scripts`.
- **mypy**: clean on `src` (0 errors, 13 source files) after adding
  `types-PyYAML` and a `[[tool.mypy.overrides]]` block for `scipy.*` to
  `pyproject.toml`, and fixing one real type error (below).
- **web-react**: `npm run lint` and `npm run build` both clean (the
  `eslint.config.js` fix and `recharts` removal had already been applied by an
  earlier pass in this session).

### Bugs found and fixed during implementation

1. **Real bug, found only against the committed manifest**: `data/manifest.csv`
   had unquoted commas inside citation strings in the `source` column (e.g.
   `Ferruit et al. 2022 (A&A, arXiv:2202.03306) Sec 2.2`), which split into two
   CSV fields and shifted every subsequent column for 7 of 8 rows — caught by
   `test_real_manifest_is_readable_and_complete` asserting `source_url` starts
   with `http` (it didn't, because the shifted `source_url` column actually
   held part of the citation string). Fixed by re-parsing and re-writing the
   file with correct CSV quoting via Python's `csv` module (`QUOTE_MINIMAL`).
2. `geometry.shutter_grid_centers` was type-annotated to return
   `tuple[np.ndarray, np.ndarray]` but returned `np.meshgrid(xs, ys)` directly,
   which is a `list`, not a `tuple` — mypy caught this; fixed by unpacking and
   returning an explicit tuple.

## 5. Instrument parameters verified

No real archive data was downloaded — this project's data mode is "official
instrument parameters + synthetic Monte Carlo" per the pack manifest. 8
physical instrument parameters were verified via `WebFetch` against real
public sources and recorded in `data/manifest.csv` with source URLs, retrieval
timestamps and content hashes:

- Shutter pitch, open-aperture dimensions, MSA array layout, NIRSpec
  wavelength range, target-acquisition accuracy — Ferruit et al. (2022, A&A,
  arXiv:2202.03306).
- In-flight shutter operability fraction (82.5%) — Rawle et al. (2022, SPIE,
  arXiv:2208.04673).
- PSF FWHM anchor (80 mas at 2.5 μm), diffraction-limit onset (2.46 μm) —
  Jakobsen et al. (2022, A&A 661 A80, arXiv:2202.03305).
- JWST primary mirror diameter (6.5 m) — NASA JWST Spacecraft Overview
  (science.nasa.gov); the official JDox page was attempted first but returns
  only a client-rendered single-page-app shell to WebFetch with no extractable
  body text, so the NASA overview page was used as the verified alternative
  primary source instead.

Two items are marked `TODO_VERIFY` rather than fabricated: quantitative
sub-diffraction-limit PSF broadening below 2.46 μm, and the spatial
(non-independent) structure of real shutter failures.

## 6. Validation and uncertainty outcomes

- **Analytic-limit validation**: numerical transmission matches the
  independently-derived closed-form erf expression to <1e-9 relative
  precision at zero offset.
- **Injection recovery**: a known effective PSF sigma (55 mas) injected into
  the noise-free forward model and recovered via a normalized fit to <0.1%
  relative error. **This gate passed.**
- **Null control**: zero centering error + all shutters open + large aperture
  drives throughput to 1.0 within 1e-6.
- **Failure-mode tests**: zero trials raises `InsufficientDataError`;
  non-finite/malformed input raises `DataSchemaError`; ill-conditioned fit
  covariance raises `ConvergenceError`.
- **Production Monte Carlo result** (20,000 trials): mean geometric slit
  throughput 0.7795 (95% bootstrap CI [0.7743, 0.7845]), median 0.9512.
  17.85% of trials draw a closed shutter (contributing zero throughput);
  conditional on an open shutter, mean throughput is 0.9488 — i.e. centering
  error and PSF width alone cost ~5% on average, while the aggregate
  operability fraction dominates the overall mean. Offset sweep: throughput
  >0.98 within ±15 mas, falling to ~0.10 by ±150 mas. Wavelength sweep:
  near-unity below the verified 2.46 μm diffraction-limit onset, declining to
  ~0.82 at the 5.3 μm red edge.

## 7. Remaining TODOs / unresolved risks

- `reports/report.tex` could not be compiled to PDF locally (no LaTeX
  toolchain); structural completeness was checked, not a rendered PDF.
- Two verified-parameter gaps remain `TODO_VERIFY`: sub-diffraction-limit PSF
  broadening curve, and real (spatially-correlated) shutter failure structure.
- PSF modelled as circularly-symmetric Gaussian, not the true NIRSpec
  Airy/diffraction pattern with wings; pure λ/D scaling applied across the
  full 0.6–5.3 μm range though the anchor only directly confirms
  Strehl>0.8 above 2.46 μm — short-wavelength slit losses are likely somewhat
  underestimated.
- Field-averaged shutter geometry used; true values vary ~1–4% across the
  field of view due to optical distortion, not modelled.

## 8. Claims safe for a public README

- "A bounded, physically-grounded Monte Carlo sandbox modelling simplified
  NIRSpec MSA geometric slit-loss throughput, with all instrument constants
  traced to verified public sources and validated against an analytic-limit
  test and a known-parameter injection-recovery gate before production use."
- "At the production trial count (20,000 trials), mean geometric slit
  throughput is 0.78, driven primarily by the 82.5% aggregate shutter
  operability fraction; conditional on an open shutter, centering error and
  PSF width alone cost only ~5% of throughput on average."
- "76 automated tests including an analytic-limit check, an
  injection-recovery validation gate, a null control, and failure-mode tests;
  ruff- and mypy-clean."
- "A bounded instrument-physics sandbox; not a replacement for the JWST
  pipeline or an official path-loss correction."

## 9. Claims that must NOT be made

- Do not claim this reproduces the true NIRSpec PSF — it is a
  circularly-symmetric Gaussian approximation, not the real Airy/diffraction
  pattern.
- Do not claim the short-wavelength (<2.46 μm) throughput values are
  precisely calibrated — the diffraction-limited scaling law is applied
  there without a verified sub-diffraction-limit broadening curve
  (TODO_VERIFY), and true short-wavelength losses are likely somewhat higher
  than modelled.
- Do not claim the shutter-failure heatmap represents real MSA operability —
  it is a synthetic illustrative realization of independent Bernoulli draws
  at the verified aggregate fraction, not a real spatial failure map.
- Do not claim this is an official or pipeline-equivalent throughput/path-loss
  correction.

## 10. Manual review checklist for Biswajit

- [ ] Compile `reports/report.tex` locally/Overleaf and read the PDF end-to-end.
- [ ] Search for a verified sub-diffraction-limit PSF broadening curve to
      resolve the short-wavelength TODO_VERIFY item.
- [ ] Search for a verified spatially-correlated shutter-failure map/model to
      resolve the second TODO_VERIFY item.
- [ ] Review `npm audit` output and decide whether to bump pinned frontend
      tooling.
- [ ] Follow `MANUAL_GITHUB_ONE_BY_ONE.md` for the actual repository creation
      and push — none of that was done in this session.

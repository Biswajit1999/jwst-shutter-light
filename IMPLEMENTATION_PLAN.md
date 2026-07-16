# Implementation Plan — JWST/NIRSpec Micro-Shutter Throughput Loss Sandbox

Author: Biswajit Jana. Local implementation pass, project from the
30-project pack (`BUILD_FIRST`, priority 9.0/10). No git operations performed.

## 0. Data mode clarification

Per `docs/DATASET_PLAN.md`, this project's mode is **official instrument
parameters + synthetic Monte Carlo** — a physically-grounded simulation, not
an archive-download audit. There is no real-data download/authorization step.
`data/manifest.csv` is repurposed to record the *source* of each verified
physical parameter (JDox page / arXiv paper) rather than a downloaded file
checksum. All Monte Carlo output is labelled `data_kind:
"synthetic_monte_carlo"` and must never be presented as real telemetry.

## 1. Literature and parameter verification (via WebFetch/WebSearch, this session)

| Citation | Verified? | Detail |
|---|---|---|
| Jakobsen et al. 2022, NIRSpec overview | VERIFIED | A&A 661, A80 (2022), DOI 10.1051/0004-6361/202142663, arXiv:2202.03305. Full author list confirmed via WebFetch of the arXiv abstract page. |
| Ferruit et al. 2022, NIRSpec MOS mode | VERIFIED | A&A, DOI 10.1051/0004-6361/202142673, arXiv:2202.03306. Full text confirmed via aanda.org HTML (open access). |
| Giardino et al. 2022, NIRSpec optical throughput/sensitivity | VERIFIED | SPIE Proc. (2022), arXiv:2208.04876. Abstract confirmed via WebFetch. Used qualitatively only (not a numeric parameter source used in the model). |
| Rawle et al. 2022, In-flight performance of the NIRSpec MSA | VERIFIED (added; not in original seed list, needed for in-flight operability) | SPIE Proc. (2022), arXiv:2208.04673. Abstract confirmed via WebFetch. |
| Bechtold et al. 2024, NIRSpec MSA operability after two years | VERIFIED metadata only (title/authors/venue); numeric operability content NOT independently extracted (PDF/HTML body inaccessible to WebFetch) | arXiv:2408.15940, SPIE Proc. 13092-38 (2024). Cited for context only; not a numeric source in the model. |
| STScI JWST pipeline documentation | Generic reference, not a single citable page — cited narratively in report where relevant, not as a specific numbered parameter source. | |
| STScI NIRSpec MSA documentation (JDox) | JDox pages return only client-rendered navigation shells to WebFetch (JS-rendered SPA) — content NOT independently extracted from JDox directly in this session. All specific numeric parameters below trace to the peer-reviewed arXiv/A&A papers instead, which is a stronger citation than JDox for a public report. JDox MSA/operability/target-acquisition page URLs are still recorded in the manifest as corroborating (not primary) sources found via WebSearch synapses. | |

## 2. Verified physical parameters used in the model

All verified via WebFetch of the primary source in this session (see
`data/manifest.csv` for the full table with URLs and `retrieved_utc`).

1. **Shutter pitch**: 105 um x 204 um (dispersion x spatial), on-sky average
   projection 268 mas x 530 mas (varies 266-270 x 520-539 mas across the FOV
   due to distortion). Source: Ferruit et al. 2022, Sec 2.2.
2. **Shutter open area**: 78 um x 178 um physical; on-sky ~199 mas x 461 mas
   (commonly rounded to 0.20" x 0.46"). Source: Ferruit et al. 2022, Sec 2.2.
3. **Array layout**: 4 quadrants, each 365 x 171 individually addressable
   shutters => 249,660 shutters total. Source: Ferruit et al. 2022, Sec 2.2.
4. **Shutter operability (in-flight)**: 82.5% of the unvignetted shutter
   population usable for science. Source: Rawle et al. 2022 (arXiv:2208.04673),
   abstract. Cross-check: Ferruit et al. 2022 Sec 2.4 reports ~14% of all
   shutters not operational from combined pre-launch ground-test failure
   modes (86% operable) — consistent order of magnitude with the in-flight
   figure; the in-flight 82.5% figure is used as the primary model parameter
   since it is the most directly relevant (post-commissioning) measurement.
5. **NIRSpec wavelength range**: 0.6-5.3 um. Source: Ferruit et al. 2022.
6. **PSF FWHM anchor**: 80 mas FWHM in the NIRSpec slit plane at 2.5 um;
   diffraction-limited (Strehl ratio > 0.8) at wavelengths above 2.46 um.
   Source: Jakobsen et al. 2022, NIRSpec overview paper.
7. **JWST primary mirror diameter**: 6.5 m (effective aperture). Standard
   public JWST observatory specification (JDox "JWST Telescope" /
   NASA/STScI observatory documentation); cross-checked against the 80
   mas/2.5 um anchor above: lambda/D at 2.5 um with D=6.5 m gives 0.0793" =
   79.3 mas, matching the literature anchor to <1% — confirms the model
   uses a essentially-pure diffraction-limited (FWHM ~ lambda/D) scaling law,
   not an independently invented constant.
8. **Target-acquisition / centering accuracy**: MOS-mode target acquisition
   (TA) is required to be accurate to <25 mas; the MSA Target Acquisition
   (MSATA) procedure can achieve ~20 mas; without MSATA, blind guide-star
   pointing is ~100 mas (1-sigma, per axis). Source: Ferruit et al. 2022,
   Sec 4.2. Used as the physically-grounded range for the centering-error
   Monte Carlo sweep (0-100 mas per axis, with 20-25 mas as the fiducial
   "successful MSATA" default).

### TODO_VERIFY items (flagged, not fabricated)

- **Sub-diffraction-limit PSF broadening below 2.46 um**: the literature
  anchor confirms the PSF is diffraction-limited (Strehl>0.8) only *above*
  2.46 um. Below that, the true PSF is somewhat broader than the pure
  lambda/D law predicts, but no verified quantitative Strehl-vs-wavelength
  curve was found in the time available for this pass. `psf.py` therefore
  applies the pure diffraction-limited lambda/D law across the *entire*
  0.6-5.3 um range as a documented, flagged simplification — this likely
  slightly *underestimates* short-wavelength slit losses. Marked
  `TODO_VERIFY` in `psf.py` docstring and `docs/ASSUMPTIONS_AND_LIMITATIONS.md`.
- **Spatial structure of shutter failures** (e.g. shorted rows/columns
  described qualitatively in Ferruit et al. 2022 Sec 2.4): no real per-shutter
  operability reference file was consulted (would require a CRDS/MAST
  download, out of scope for this parameter-verification pass). The
  failed-shutter heatmap therefore uses independent per-shutter Bernoulli
  draws at the verified *aggregate* 82.5% operability fraction, explicitly
  labelled as a synthetic illustrative realization, not a real MSA operability
  map.

## 3. File-level tasks

### Foundation (Phase 2)
- `src/jwst_nirspec_msa_throughput_sandbox/config.py` — port from sibling, rename package.
- `exceptions.py` — extend stub with ProvenanceError, ArchiveAccessError (unused but kept for consistency), ConvergenceError, InsufficientDataError.
- `logging_utils.py` — port near-verbatim.
- `provenance.py` — extend stub sha256 helper with manifest row read/write + get_git_commit (never raises).
- `results_io.py` — new: Metric dataclass + write_summary.

### Data/parameter layer (Phase 3)
- `data/manifest.csv` — 8 rows, one per verified parameter, `product_id` = parameter name, `source_url` = verified URL, `selection_reason` = what it's used for.
- `data/provenance.yml` — update `source_products` with the same 8 entries.
- `scripts/fetch_data.py` — repurposed to a `verify_parameters.py`-style script that re-prints/re-checks the manifest (no network calls needed at run time since verification already happened via WebFetch this session); keeps `--i-have-authorization` flag for CLI pattern consistency (no actual risk since nothing destructive/costly happens).
- `src/.../synthetic.py` — new: core Monte Carlo trial generator (centering offsets, wavelength draws, shutter operability draws).

### Scientific modules (Phase 4)
- `geometry.py` — MSA geometry constants + rectangular-aperture Gaussian-transmission model.
- `psf.py` — wavelength-dependent diffraction-limited PSF FWHM/sigma.
- `throughput.py` — per-trial throughput combining geometry+psf+operability.
- `monte_carlo.py` — trial orchestration, sweeps (offset, wavelength, operability heatmap), summary stats.
- `uncertainty.py` — bootstrap_statistic + check_fit_convergence (separate).
- `plotting.py` — extend with a generic save helper (kept minimal; scripts/make_figures.py holds the actual figure code, matching sibling pattern).
- `core.py` — `run_pipeline` orchestrator with exception handling -> warnings.

### Validation/QA (Phase 5)
- Analytic-limit validation: at zero offset, throughput must match the closed-form 2D-Gaussian-through-rectangular-aperture erf formula.
- Injection recovery: fit the effective centering sigma back out of a throughput-vs-offset sweep, recover the injected value within tolerance.
- Null control: zero centering error + all shutters operable + shutter much larger than PSF -> throughput -> 1.
- Failure modes: zero trials -> InsufficientDataError; non-finite inputs -> DataSchemaError; ill-conditioned fit -> ConvergenceError.
- Benchmarks via tracemalloc + perf_counter.

### Figures + report (Phase 6)
1. `fig01_msa_geometry` — shutter grid schematic with pitch/open-area annotated.
2. `fig02_throughput_vs_offset` — throughput vs centering offset (varied across a real range) at fixed wavelength.
3. `fig03_wavelength_loss` — throughput vs wavelength (varied 0.6-5.3 um) at fixed offset.
4. `fig04_failed_shutter_heatmap` — synthetic operability heatmap over a shutter grid.
5. `report.tex` + `references.bib`.

### React dashboard (Phase 7)
- Fix `eslint.config.js` (`react/jsx-uses-vars`, `react/jsx-uses-react`).
- Remove `recharts` from `package.json`.
- Rewrite `App.jsx` from the `hst-wfc3ir-ramp-linearity-audit` template; "SYNTHETIC DEMO vs REAL DATA" badge -> "SMALL-TRIAL DEMO vs FULL MONTE CARLO RESULTS".
- Rewrite `public/project.json`.
- `scripts/sync_web_assets.py` — new, copies results/figures/manifest into web-react/public.

### Production run (Phase 8)
- Full Monte Carlo run at production trial count (>=10,000 trials per docs/BENCHMARK_PLAN.md-style scale), regenerate figures, update report.tex with real numbers.

## 4. Environment

Dedicated conda env `jwst-nirspec-msa-throughput-sandbox` (Python 3.11),
independent of sibling projects' environments, per task instructions.

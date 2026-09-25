# JWST/NIRSpec Micro-Shutter Throughput Loss Sandbox

![Cover](docs/cover.png)

> **Curation:** `BUILD_FIRST` · Priority 9.0/10 · official instrument parameters + synthetic Monte Carlo

## Scientific question

How do target-centering error, wavelength-dependent PSF width and shutter operability alter simplified NIRSpec MSA throughput?

## What this repository contributes

An instrument-physics QA sandbox; not a replacement for the JWST pipeline or official path-loss corrections.

## Key result

**Correction in progress:** the former 0.7795 headline is retired. It multiplied conditional geometric slit transmission by a 2022 aggregate operability fraction, even though APT/MPT uses a position-specific operability map to plan targets into viable shutters. Static operability constrains assignment and multiplexing; it is not an independent photon-loss draw after planning. Official STScI documentation now also distinguishes a separate random non-opening rate of up to 4% for shutters otherwise classified as operable. See [SCIENTIFIC_AUDIT.md](SCIENTIFIC_AUDIT.md) for the evidence, consequence, and corrected analysis contract.

## Reproducing this result

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -q
python scripts/run_analysis.py --demo
python scripts/make_figures.py --demo
```

The demo path above uses a small trial count for a fast smoke test. The production Monte Carlo result quoted above is `python scripts/run_analysis.py` (no `--demo`), which uses the full 20,000-trial configuration in `config/analysis.yml`.

For the web dashboard:

```bash
cd web-react
npm install
npm run dev
```

## Research documentation

- `CURATION_STATUS.md`
- `docs/RESEARCH_BLUEPRINT.md`
- `docs/DATASET_PLAN.md`
- `docs/LITERATURE_SEEDS.md`
- `docs/VALIDATION_CONTRACT.md`
- `docs/FIGURE_AND_UI_SPEC.md`

## Reproducibility and FAIR practice

This project uses verified official instrument parameters rather than downloaded archive products (documented explicitly, not a substitute presented as archive data). Derived results record the software commit and configuration hash.

## Limitations

- An instrument-physics QA sandbox using official published parameters and a Monte Carlo forward model; not a replacement for the JWST pipeline or official path-loss corrections, and not a fit to real observed spectra.
- Shutter-open/closed and centering-error distributions are simplified, documented assumptions, not measured from real exposures.
- Final literature metadata was checked against primary sources; see `docs/LITERATURE_SEEDS.md` for any items still marked `VERIFICATION_PENDING`.

## Author

Biswajit Jana

## Licence

BSD-3-Clause for original code. Instrument parameter sources retain their original terms.

## Research Quality Upgrade

See [RESEARCH_QUALITY.md](RESEARCH_QUALITY.md) for the validation layer, reference anchors, equations and research boundaries added to this repository.

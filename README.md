# JWST/NIRSpec Micro-Shutter Throughput Loss Sandbox

> **Curation:** `BUILD_FIRST` · Priority 9.0/10 · official instrument parameters + synthetic Monte Carlo

## Scientific question

How do target-centering error, wavelength-dependent PSF width and shutter operability alter simplified NIRSpec MSA throughput?

## What this repository contributes

An instrument-physics QA sandbox; not a replacement for the JWST pipeline or official path-loss corrections.

## Current state

This is a research-project implementation blueprint. The repository contains a scientific contract, data/provenance templates, starter Python package, tests, a TeX report skeleton and a React/Tailwind research-page starter. Example values are synthetic and must never be presented as mission results.

## Start here

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -q
python scripts/run_analysis.py --demo
python scripts/make_figures.py --demo
```

For the web interface:

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

All real inputs require product IDs, retrieval times, checksums, source terms and deterministic selection manifests. Derived results must record the software commit and configuration hash.

## Limitations

- The initial code is a scaffold, not a completed scientific result.
- Archive schemas and data rights must be verified before download or redistribution.
- Final literature metadata must be checked against primary sources.
- Public claims must remain narrower than the evidence.

## Author

Biswajit Jana

## Licence

BSD-3-Clause for original code. Mission/archive products retain their original terms.

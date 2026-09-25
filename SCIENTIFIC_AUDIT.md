# Scientific audit: operability is not throughput

Date: 2026-09-25  
Status: original headline retired; corrected estimator in progress

## Finding

The published mean of 0.7795 multiplied two different quantities:

1. geometric flux transmission for a source already assigned to an open shutter; and
2. the 2022 aggregate fraction of shutters classified as usable for science.

That product is not a conditional spectroscopic throughput. NIRSpec MOS planning uses a position-specific operability reference file in APT/MPT to place targets in viable shutters. Static failed-closed, vignetted, short-masked, and failed-open regions primarily constrain target assignment and multiplexing; they are not independent Bernoulli photon losses applied after a target has been planned.

The old 82.5% aggregate is also not a timeless detector constant. Official STScI documentation, updated with April 2026 knowledge, reports 24,024 vignetted shutters, 17,878 highly likely failed-closed shutters among unvignetted shutters, 22 failed-open shutters in unvignetted regions, and a separate random failure mode in which up to 4% of shutters otherwise classified as operable may remain closed when commanded.

## Consequence

The 0.7795 headline and its bootstrap interval are retired. The existing simulation remains useful only after separating its estimands:

- **Conditional geometric throughput:** flux fraction through a shutter, conditional on a planned shutter opening.
- **Command-success sensitivity:** a separate 0–4% random non-opening scenario for otherwise operable shutters.
- **Planning availability:** position-specific feasibility and multiplexing governed by the current MSA operability map; an aggregate percentage cannot reproduce it.
- **Contamination risk:** failed-open shutters affect neighboring planning regions and spectral contamination, not the target's geometric slit transmission.

## Corrected analysis contract

The next generated release will:

1. report conditional geometric throughput as the primary measurement;
2. sweep target-acquisition scatter, wavelength, field geometry, and 0–4% random command failure separately;
3. remove the client-side confidence-level extrapolator;
4. publish every scenario and preserve the old result only as an explicitly invalidated historical artifact;
5. avoid calling Monte Carlo sampling error a physical uncertainty interval when model-form uncertainty dominates.

## Authoritative sources

- [STScI: NIRSpec MSA Shutter Operability](https://jwst-docs.stsci.edu/jwst-near-infrared-spectrograph/nirspec-operations/nirspec-mos-operations/nirspec-msa-shutter-operability)
- [STScI: NIRSpec Micro-Shutter Assembly](https://jwst-docs.stsci.edu/jwst-near-infrared-spectrograph/nirspec-instrumentation/nirspec-micro-shutter-assembly)
- [STScI: NIRSpec MOS Known Issues](https://jwst-docs.stsci.edu/known-issues/nirspec-known-issues/nirspec-mos-known-issues)

This audit distinguishes a software-estimator correction from new instrument characterization. It does not supersede APT/MPT, CRDS operability reference files, or the JWST calibration pipeline.

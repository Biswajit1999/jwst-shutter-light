# Assumptions and limitations

## Estimand boundary

The primary estimand is geometric slit throughput conditional on a planned shutter opening successfully. Static failed-closed, failed-open, short-masked, and vignetted shutters affect position-specific target assignment and multiplexing; they are not independent photon-loss terms and are not multiplied into the primary throughput estimate.

A second, explicitly separate estimand applies an independent 0–4% random non-opening scenario to otherwise operable shutters. This is a sensitivity boundary based on current STScI documentation, not a calibrated forecast for a particular MSA configuration or epoch.

## Assumptions

- Target-centering offsets are independent zero-mean Gaussian draws per axis.
- The PSF is a circular Gaussian calibrated to 80 mas FWHM at 2.5 microns and scaled as lambda/D.
- Shutter pitch and open area use field-averaged values.
- The random non-opening scenario is independent of position, wavelength, and centering error.

## Limitations

- A Gaussian PSF omits Airy structure, diffraction spikes, aberrations, and wavelength-dependent wings.
- Pure lambda/D scaling below the verified diffraction-limited regime can understate short-wavelength slit losses.
- Field distortion changes projected shutter dimensions by roughly 1–4% across the field.
- The model excludes optical-train transmission, detector quantum efficiency, grating efficiency, source morphology, spectral trace geometry, and official path-loss calibration.
- Every result is synthetic Monte Carlo output. No NIRSpec science exposure or target-specific MPT configuration is analysed.
- The 0–4% command-failure scenario does not reproduce the real spatial or temporal structure of shutter failures.

These restrictions make the project an instrument-physics QA sandbox, not an observing-time calculator or a replacement for STScI planning and calibration software.

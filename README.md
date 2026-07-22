# SND@LHC Birks' Law — MuFilter QDC Study

This repository records the implementation and detector-level validation of Birks' law quenching in the SND@LHC MuFilter scintillator simulation. The current comparison uses digitized Upstream MuFilter (US) QDC from:

1. newly produced MC with Birks' law enabled (`Birks MC`),
2. the existing MC sample without the new correction (`No-Birks MC`), and
3. 2023 CERN H8 test-beam data (`Data`).

The repository contains implementation references, production scripts, analysis code, selected validation outputs, and notes needed to continue the study. Generated batch logs and disposable intermediate outputs are intentionally not tracked.

## 1. Research questions

The project addresses the following questions:

- Does the new Birks implementation run correctly through simulation and digitization?
- Does quenching reduce the simulated US QDC in the expected direction?
- Does the corrected MC response move closer to test-beam data?
- Which part of the remaining Data–MC discrepancy can reasonably be attributed to Birks parameters rather than the wider detector-response model?

The current observable is not the Geant4 step-level light yield. It is QDC from `Digi_MuFilterHits` after digitization. Therefore it includes the effects of light collection, attenuation, SiPM response, gain, saturation, masking, thresholds, calibration, noise, and the digitization model in addition to Birks quenching.

## 2. Birks model and implementation

The implemented form is

```math
E_{\mathrm{vis}}=
\frac{E_{\mathrm{dep}}}
{1+k_1(dE/dx)_{\mathrm{mass}}+k_2(dE/dx)_{\mathrm{mass}}^2},
```

with

```math
(dE/dx)_{\mathrm{mass}}=
\frac{E_{\mathrm{dep}}/\mathrm{MeV}}
{(\Delta x/\mathrm{cm})\rho}.
```

Current provisional settings:

- `k1 = 0.02002 g/(MeV cm^2)`
- `k2 = 0`
- correction applied only to charged particles
- guards for non-positive deposited energy, step length, material density, and denominator
- for `|q| > 1`, `k1` is multiplied by `7.2/12.6`

These values were adapted from the ATLAS TileCal implementation. They have not yet been fitted or validated as the final parameters for the SND MuFilter scintillator.

The actual source used for MC production must be identified by its sndsw commit and recorded before a final physics result is produced. Files under `birks_variants/` are implementation drafts and should not be treated as production code unless explicitly documented.

## 3. Beam samples

| Energy | Particle | Data run | Data tree |
|---|---|---:|---|
| 100 GeV | $\pi^+$ | `100630` | `rawConv` |
| 300 GeV | $\pi^-$ | `100639` | `rawConv` |

The current `analysis/analyze_qdc_final.py` uses:

- Birks MC: `/eos/user/y/ykim/project_birkslaw/birks_samples_15k/...`
- No-Birks 100 GeV MC: `/eos/experiment/sndlhc/MonteCarlo/testbeam2023/2mmRangeCut/100GeV_211/...`
- No-Birks 300 GeV MC: `/eos/experiment/sndlhc/MonteCarlo/testbeam2023/2mmRangeCut/300GeV_-211/...`
- Data 100 GeV: `/eos/experiment/sndlhc/convertedData/commissioning/testbeam_June2023_H8/run_100630/...`
- Data 300 GeV: `/eos/experiment/sndlhc/convertedData/commissioning/testbeam_June2023_H8/run_100639/...`

Before running the analysis, verify the EOS directories and the number of valid digitized ROOT files in every batch.

## 4. Analysis observable

### 4.1 Event-level total US QDC

For each selected event, the analysis sums all valid positive large-SiPM QDC signals in the Upstream MuFilter:

```math
Q_{\mathrm{US}}^{\mathrm{event}}=
\sum_{\substack{\mathrm{all\ US\ hits}\\
\mathrm{unmasked\ large\text{-}SiPM\ channels}\\
QDC>0}} QDC.
```

The signal call is:

```python
signals = hit.GetAllSignals(
    mask=True,
    positive=True,
    use_small_sipms=False,
)
```

- `system == 2` restricts the observable to the Upstream MuFilter.
- `mask=True` excludes channels marked unusable by the detector configuration.
- `positive=True` keeps signals with positive QDC; this is unrelated to the particle charge.
- `use_small_sipms=False` keeps one sensor class and avoids combining uncalibrated large- and small-SiPM responses.
- Bar 4/5 requirements are event-selection conditions. After selection, valid signals from all US bars contribute to the total.

### 4.2 Channel response

The analysis also compares the mean positive QDC by channel in bars 4 and 5 of US1–US3:

- US1, US2, US3 correspond to planes 0, 1, and 2.
- channels: `0, 1, 3, 4, 6, 7, 8, 9, 11, 12, 14, 15`
- error bars represent the standard error of the mean, not the event-distribution standard deviation.

## 5. Current selection

`analysis/analyze_qdc_final.py` currently applies the same baseline selection to Data, Birks MC, and No-Birks MC:

1. `len(Digi_ScifiHits) > min_scifi_hits` (currently 200),
2. at least one positive large-SiPM signal in bar 4 or 5 of each of US1, US2, and US3.

Earlier studies investigated event-header fast-filter flags, including the combination `SciFi && SciFi_Total && US_Total`, commonly associated with `0x2c000000` in the inspected files. That flag selection is not part of the current analysis code. It must not be described as the current selection unless it is reintroduced and validated.

## 6. Command-line options

```text
--max-events
```

Maximum number of selected events retained per sample. This is not a limit on scanned input entries. Using `--max-events 15000` retains the first 15,000 passing entries and can create file-order bias.

```text
--max-scanned-events
```

Maximum number of input entries scanned per sample. Use `-1` for all entries.

```text
--file-check-events
```

Entries read per Data file for the separate file-level cut-flow check. This causes an additional pass over Data. Use a small value for quick diagnostic runs.

```text
--min-scifi-hits
```

Requires the number of `Digi_ScifiHits` to be greater than this value. The current baseline is 200.

## 7. Preserved results

- `analysis/results_archive/baseline_100events/`
  Initial 100 selected-event validation.

- `analysis/results_archive/production_15k/`
  Results using the 15k Birks MC production and the SciFi multiplicity requirement. Data sampling and selection must still be validated before these are treated as final physics results.

- `analysis/results_archive/biased_first15k/`
  Diagnostic output based on the first 15,000 passing events in file order. It has known sampling bias and must not be used as a final result.

Intermediate plots, ROOT products, caches, and HTCondor logs are not tracked. A preserved result should include its summary CSV, essential plots, exact command/configuration, input provenance, and sampling seed where applicable.

## 8. Previous small-sample validation

The following values are historical results from the approximately 100-event Birks samples. They confirm the direction of the implementation effect but are not a precision validation.

| Energy | Sample | Selected | Mean total US QDC | Median | Std. dev. |
|---|---|---:|---:|---:|---:|
| 100 GeV | Birks MC | 98 | 10,717.55 | 9,990.87 | 6,727.19 |
| 100 GeV | No-Birks MC | 100 | 13,139.69 | 11,462.55 | 7,072.66 |
| 100 GeV | Data | 100 | 4,117.94 | 4,534.97 | 3,062.84 |
| 300 GeV | Birks MC | 100 | 34,201.32 | 33,646.11 | 17,534.73 |
| 300 GeV | No-Birks MC | 100 | 37,791.17 | 34,879.06 | 17,555.79 |
| 300 GeV | Data | 100 | 11,632.53 | 11,794.44 | 4,224.16 |

Mean reduction after enabling Birks quenching in this small, unpaired sample:

- 100 GeV: approximately 18.4%
- 300 GeV: approximately 9.5%

Birks MC/Data mean ratios were approximately 2.60 and 2.94 at 100 and 300 GeV, respectively. Birks quenching moved the MC response in the Data direction, but a substantial absolute-scale discrepancy remained.

## 9. Known sampling issue

The previous command using `--max-events 15000` did not select a uniform random subset of all passing Data events. It stopped after collecting the first 15,000 passing entries from the ordered file list. The resulting sample may be dominated by particular files, run segments, beam conditions, or calibration periods.

A final representative sample should use reservoir sampling over all passing entries, with a fixed seed and recorded provenance. The stored payload must preserve enough information to produce both total-QDC and channel-response plots from the same sampled events. At minimum, record:

- source filename or file index,
- tree entry,
- run/event identifier when available,
- selection version,
- sampling method and random seed.

## 10. Repository structure

```text
project_birkslaw/
├── analysis/               QDC analysis code, memo, and selected outputs
│   └── results_archive/    preserved baseline and diagnostic results
├── birkslawSND/            SND MuFilter implementation/reference files
├── birks_variants/         draft implementation alternatives
├── codesfromATLAS/         ATLAS reference excerpts/source material
├── condor/                 MC production, digitization, and submission scripts
└── runtime_test/            small local runtime-test fixtures
```

Key production files under `condor/` include:

- `run_birks_15k.sh`
- `birks_15k.sub`
- `make_birks_jobs_15k.sh`
- `run_digitization.sh`
- `digitization.sub`

## 11. Reproducibility requirements

Every production or final analysis result should record:

- sndsw commit and SND software release,
- exact production `MuFilter.cxx` and, if modified, `MuFilter.h`,
- Birks constants and unit convention,
- geometry and digitization configuration,
- primary particle, energy, position, event count, `PGrunID`, and random seed,
- input file list and successful/failed batches,
- analysis code commit,
- selection definition and cut values,
- sampling method, seed, and selected-entry provenance.

## 12. Recommended next steps

1. Identify and tag the exact sndsw commit and MuFilter source used for the 15k production.
2. Build a production manifest containing batch, seed or `PGrunID`, output path, file validity, and event count.
3. Implement reproducible reservoir sampling for Data and save selected-entry provenance.
4. Produce Birks ON/OFF paired MC with the same primary conditions, random seeds, geometry, and digitization settings.
5. Compare mean, median, truncated mean, uncertainty from bootstrap resampling, tail fractions, and channel/plane/bar response.
6. Validate Data–MC consistency for gain, attenuation, masking, noise, thresholds, and large-/small-SiPM saturation.
7. Only after these controls, perform a scan or fit of `k1` and, if justified by sensitivity, `k2`.

## 13. Current interpretation

The implementation runs through simulation and digitization and reduces the simulated total US QDC in the expected direction. The historical small-sample comparison moved MC toward Data, but the remaining absolute-scale difference is large and the current large-sample comparison has unresolved Data-sampling and detector-response systematics.

At this stage the results demonstrate an implementation effect. They do not yet constitute a final measurement of SND MuFilter Birks parameters or proof that Birks quenching alone explains the Data–MC discrepancy.

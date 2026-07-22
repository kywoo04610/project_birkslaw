# 15k Birks MC production provenance

This directory preserves the exact Birks-enabled `MuFilter.cxx` snapshot and patch used for the SND@LHC 15k-event-per-energy MC production.

## Production scope

| Sample | PDG ID | Energy | Batches | Events per batch | Expected events | PGrunID range |
|---|---:|---:|---:|---:|---:|---:|
| `piPlus_100GeV_15k` | 211 | 100 GeV | 150 | 100 | 15,000 | 12000–12149 |
| `piMinus_300GeV_15k` | -211 | 300 GeV | 150 | 100 | 15,000 | 32000–32149 |

The job definitions are retained in `condor/birks_jobs_15k.txt`. Twelve jobs were listed for retry in `condor/birks_jobs_15k_retry.txt`:

- 100 GeV: batches 46, 73, 133, 144, and 145
- 300 GeV: batches 59, 115, 131, 143, 146, 147, and 148

The retry list records resubmission history; it does not by itself prove the final validity of the corresponding EOS outputs.

## Software environment

| Item | Recorded value |
|---|---|
| SND setup | `/cvmfs/sndlhc.cern.ch/SNDLHC-2025/Oct7/setUp.sh` |
| alienv package | `sndsw/latest-master-release` |
| local installation | `sndsw/master-local1` |
| sndsw upstream | `https://github.com/SND-LHC/sndsw.git` |
| sndsw base commit | `7fc62ce7c271653ba3974eaf19541a562fc8d953` |
| ROOT | `6.36.04` |
| Python | `3.9.25` |

The production was not made from the unmodified upstream commit alone. The base commit had a local, uncommitted modification to `shipLHC/MuFilter.cxx`. No modification to `MuFilter.h` was reported by Git.

## Exact implementation snapshot

`MuFilter.cxx` in this directory is an exact copy of the working source used to build the local installation.

| Artifact | SHA-256 |
|---|---|
| `MuFilter.cxx` | `d05928aec6e97d76fd4c31a5418278a36bfe32043a6a0e0172388e1a04dce997` |
| compiled `MuFilter.cxx.o` | `a21ef1e342b7fa50eca07b5d86bc896cb6a172eb4bc722ff468b9d1ddfb08208` |
| linked `libshipLHC.so.0.0.0` | `0bca6f5550bf83c82263f8e66c3170c0118222a72f7d4e638be6ee845b33156a` |

`MuFilter.patch` records the change relative to sndsw commit `7fc62ce7c271653ba3974eaf19541a562fc8d953`.

The source snapshot in `production/15k/MuFilter.cxx` is the canonical record for this production. The older file `birkslawSND/MuFilter.cxx` has a different hash and must not be used as the 15k production snapshot.

## Compilation and link evidence

Recorded timestamps in Europe/Zurich local time:

| Artifact | Timestamp | Size |
|---|---|---:|
| working and installed `MuFilter.cxx` | 2026-07-20 14:07:21 +0200 | 33,022 bytes |
| `MuFilter.cxx.o` | 2026-07-20 14:10:10 +0200 | 2,874,272 bytes |
| `libshipLHC.so.0.0.0` | 2026-07-20 14:10:13 +0200 | 7,328,256 bytes |

The object was compiled after the modified source and the shared library was linked three seconds after the object. The string `BirksLaw` was found in both the object and the final shared library. Together these observations provide direct evidence that the Birks-enabled source was compiled and linked into the production library.

## Birks configuration

The implementation applies a step-level correction in the active MuFilter scintillator volume:

```math
E_{\mathrm{vis}} =
\frac{E_{\mathrm{dep}}}
{1+k_1(dE/dx)_{\mathrm{mass}}+k_2(dE/dx)_{\mathrm{mass}}^2}.
```

Recorded settings:

- `k1 = 0.02002 g/(MeV cm^2)`
- `k2 = 0`
- charged particles only
- `k1 -> k1 * 7.2/12.6` when `|q| > 1`
- guards for non-positive energy deposit, step length, density, and denominator
- mass stopping power calculated from VMC energy deposit, step length, and current material density
- corrected energy accumulated in `fELoss` for every Monte Carlo step

These parameters are provisional ATLAS TileCal-inspired values, not fitted SND MuFilter constants.

## Simulation and digitization configuration

Each job ran 100 events with the following Particle Gun configuration:

```text
--PG
--Estart <energy>
--Eend <energy>
--EVx -38
--EVy 44
--EVz 310
-n 100
--HX
--PGrunID <run ID>
```

Simulation used `shipLHC/run_simSND.py`. Digitization used `shipLHC/run_digiSND.py` with `-cpp`.

Output base:

```text
/eos/user/y/ykim/project_birkslaw/birks_samples_15k
```

Expected digitized filenames:

- 100 GeV: `sndLHC.PG_211-TGeant4_digCPP.root`
- 300 GeV: `sndLHC.PG_-211-TGeant4_digCPP.root`

## EOS validation

The source, binary, and EOS production dataset were validated. The following checks were completed:

1. Verify that all 150 batch directories exist for each energy.
2. Verify every digitized ROOT file is readable and non-empty.
3. Verify the expected tree (`cbmsim`), branch (`Digi_MuFilterHits`), and event count in every file.
4. Record missing, corrupt, duplicate, and retried batches.
5. File size and modification time were recorded for every final digitized ROOT file; per-file SHA-256 was not calculated.
6. Confirm that the total valid event count is 15,000 for each energy.

EOS validation completed successfully on 2026-07-22 at 12:19:11 UTC. All 300 digitized ROOT files passed, containing 30,000 total events. Detailed results are stored under `eos_validation/`.

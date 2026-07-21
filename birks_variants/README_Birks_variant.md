# Birks-law implementation drafts for MuFilter

## Status

These files are draft implementations prepared for review.

- Not complied
- Not validated with simulation
- Original `MuFilter.cxx` and `MuFilter.h` remain unchanged
- Both variants use the same Birks calculation
- The variants differ only in code organization

## Physics model

The implementation follows the current ATLAS-style Birks correction:

E_vis = {E_dep}/{1 + k_1*[dE/dx] + k_2*[dE/dx]^2}

The initial parameter values are

k_1 = 0.02002 [g/(MeV * cm^2)]
k_2 = 0

For particles with (|q|>1), the ATLAS correction
k_1 -> k_1 * (7.2/12.6)

is included.

These choices are provisional and require confirmation.

## Common behavior

Both variants:

1. Apply the correction to each Monte Carlo step before accumulating 'fELoss'
2. Use `gMC->Edep()` as the step energy deposit.
3. Use `gMC->TrackStep` as the step length.
4. Use `gMC->TrackCharge()` to identify charged particles.
5. Use `gMC->CurrentMaterial()` to obtain the material density.
6. Return the original energy deposit for neutral particles.
7. Return the original energy deposit when the step length is zero.
8. Return the corrected energy in the original simulation energy unit.

The original accumulation

```cpp
fELoss += gMC->Edep();

is replaced by

fELoss += BirksLaw();

```
in version A, or by the corresponding local-helper call in version B.


## Version A: private member function
Files:
`MuFilter_versionA.cxx`
`MuFilter_versionA.h`

Changes to the header:
```cpp
private:
    Double_t BirksLaw() const;

```
Changes to the source:
1. Added #include <cmath>

2. Implemented
```cpp
Double_t MuFilter::BirksLaw() const
```
3. Replaced the raw step-energy accumulation with
```cpp
fELoss += BirksLaw();
```

Advantages
1. Birks correction is explicitly part of the `MuFilter` class.
2. The function is visible in the class interface.
3. Future detector-specific configuration may be easier to add.

Disadvantages
1. Requires modification of both `MuFilter.h` and `MuFilter.cxx`.


## Version B: file-local helper function
File:
`MuFilter_versionB.cxx`

`MuFilter.h` remains unchanged.

Implementation

Version B defines `BirksLaw()` inside an anonymous namespace in `MuFilter_versionB.cxx`.

```cpp
namespace
{
Double_t BirksLaw()
{
    // Birks-law implementation
}
} // namespace
```

Because the function has internal linkage and is available only within this source file, no declaration or modification is required in `MuFilter.h`.

Inside `MuFilter::ProcessHits()`, the original per-step energy accumulation
```cpp
fELoss += gMC->Edep();
```
was replaced with
```cpp
fELoss += BirksLaw();
```
The correction is therefore evaluated separately for every Monte Carlo step inside
the active scintillator volume before the corrected visible energy is accumulated in `fELoss`.

## Guards and conditions
The function returns the uncorrected energy deposit when:
    the deposited energy is zero or negative;
    the particle is neutral;
    the Monte Carlo step length is zero or negative;
    the current material density is zero or negative; or
    the calculated Birks denominator is zero or negative.

For a valide charged-particle step, the mass stopping power is calculated as

[dE/dx]_mass = E_dep / [steplength * density]

The corrected visible energy is calculated using

E_vis = E_dep / {1 + k_1(dE/dx)_mass + k_2[(dE/dx)_mass]^2}.


## Difference from version A

Version A implements `BirksLaw()` as a private member function of `MuFilter`
and therefore requires changes to both MuFilter.cxx and MuFilter.h.

Version B implements `BirksLaw()` as a file-local free function and therefore
requires a change only to `MuFilter.cxx`.

Advantages
1. Only `MuFilter.cxx` is modified.
2. The implementation is local to the source file.
3. This is the smallest code change.

Disadvantages
1. The function is not formally part of the `MuFilter` class.
2. Future configuration through class members may require restructuring.
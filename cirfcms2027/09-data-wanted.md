# Data wanted — what Amit can chase that this environment cannot reach

This session can only use web **search**. Publisher sites, doi.org, and even
nvlpubs.nist.gov are refused by the egress proxy, so full texts and datasets
have to be fetched from outside. Everything below is something a library login,
a VPN, or an email would get in minutes.

Ordered by how much it would improve the paper.

---

## Tier 1 — biggest effect

### 1. The NIST overhang thermography dataset

**Why it matters more than anything else here.** Our geometry claim is that fault
severity follows how much solid metal sits beneath the track. NIST built an
artefact specifically to test that, and published the data.

    Molnar, Heigel & Whitenton (2021), "In Situ Thermography During Laser Powder
    Bed Fusion of a Nickel Superalloy 625 Artifact with Various Overhangs and
    Supports", J. Research of NIST, DOI 10.6028/jres.126.005
    Dataset: data.nist.gov, mds2-2112
    Paper:   nvlpubs.nist.gov/nistpubs/jres/126/jres.126.005.pdf
    Also:    PMC11249204

Overhang angles from 5 to 85 degrees in 10 degree steps, IN625, commercial
machine, and the process deliberately held constant so geometry effects are
isolated from scan-strategy effects. It reports radiant temperature, cooling
rate and **melt pool length** per layer, and ships MATLAB scripts.

**This is not a citation, it is the measurement.** With it, the geometry profile
stops being asserted and becomes fitted. It is also the same class of
measurement (melt pool length) that our Route B result turns on.

**What to get:** the PDF, and the dataset if the PDF looks usable.

### 2. ~~Renishaw LaserVIEW — where in the beam path?~~ **CLOSED — not obtainable**

Could not be established from public documentation and Amit could not obtain it
through other channels. **Resolved by taking the conservative reading**: the
photodiode is assumed to sit downstream of the plume, making it another
melt-pool observable rather than a direct power measurement. That is the
assumption which does *not* flatter the analysis.

Superseded in any case by a policy decision: **the paper names no commercial
products.** Configurations are described by their contents (A through E), which
makes the claim more general — it holds for any machine anyone builds, not for a
named product — and removes the dependence on vendor details that rest on
secondary literature.

The design recommendation survives intact and needs no verification: a suite
adding a direct measurement of delivered laser power, sampled upstream of the
process zone, separates power from gas at 84 degrees.

### 3. In-process noise figures for a coaxial photodiode and a two-colour pyrometer

The accepted abstract says noise comes from published sensor characterisations.
Only one figure proved citable (melt pool width, 2.3% relative, Weaver 2024), so
noise is swept as a ratio instead and the deviation is declared.

Finding real figures would let the abstract stand as written. What is needed is
**in-process** noise - repeatability of the signal during a build - not
calibration accuracy. NIST AMS 100-35 was read in full and is calibration, not
noise.

Worth asking anyone who operates a monitored machine: what is the
pass-to-pass scatter on the photodiode trace at nominally identical conditions?
That single number would do it.

---

## Tier 2 — closes the two remaining profiles

### 4. Galvo tracking error at direction changes (the speed profile)

Claim: scan speed error is worst where the laser turns, so it loads onto short
vectors.

Where to look: scanner vendor specs from **Scanlab** or **Raylase** quoting
settling time or tracking error; or LPBF papers on porosity and overheating at
**vector ends and turnarounds**, which are well documented. Either gives the
shape; the vendor spec gives a magnitude.

### 5. Layer-to-layer periodicity from recoating (the layer profile)

Claim: a recoater short-feed affects a whole layer, so severity alternates
between layers.

Where to look: papers reporting **layer-periodic** variation in melt pool
monitoring signals, or recoater-induced defects recurring with layer index.
Bugatti & Colosimo (Addit. Manuf. Letters 2022) is adjacent - a recoater-mounted
scanner - and its references may lead there.

---

## Tier 3 — already partly covered

### 6. Laser power drift (the power profile)

Partly closed from vendor specifications: industrial fibre lasers quote **1-3%
long-term power instability over 2-8 hours**, which is the slow-drift shape we
assume. Definitions vary (rms vs peak-to-peak, 2 vs 4 vs 8 hour windows), so a
single clean citation at LPBF power levels would be better than the mixed set
found by search.

### 7. Gas flow gradient (the gas profile) — the one that already has support

Raj et al., *J. Manufacturing Processes* 89:24-38 (2023). Coaxial melt pool area
and intensity on IN718, spatial variation attributed to the angled beam
interacting with shield gas flow. Same alloy, same sensor pair.

Only the abstract has been read. **The full text would confirm the direction and
possibly give a magnitude**, which would upgrade this from "corroborated" to
"fitted" - and it is also the closest prior work, so the positioning paragraph
in the introduction depends on reading it properly.

---

## Separately: four literature rows read only from abstracts

From the 18-row extraction table, these decide novelty positioning and the
accuracy comparison, and none has been read in full:

    Guo et al. 2019            the motivation citation
    k-NN parameter estimation  DOI 10.1007/s00170-025-15591-y
    Raj et al. 2023            the closest prior art (also item 7)
    RAISE-LPBF benchmark       arXiv 2409.12475 - confirm the frame counts

The RAISE-LPBF frame counts (8 vs 32) came from a fragmentary snippet and carry
a **[PROVISIONAL]** flag in the draft. They are the only direct literature
confirmation of the central mechanism, so they are worth confirming.

---

## What would help most of all, and does not exist

A dataset with **deliberately induced machine faults** - runs with a known power
deficit, a known short-fed layer, degraded gas - and the sensor traces recorded.
That would let every coupling constant and every profile be fitted instead of
asserted.

Searching has not found one. Its absence is why this is a modelling paper, and
it is worth saying so in the discussion: the field has benchmark data for
*process parameters* and none for *machine faults*.

If anyone at a partner lab would run even a handful of deliberately faulted
single tracks, that would be a follow-on paper rather than a footnote.

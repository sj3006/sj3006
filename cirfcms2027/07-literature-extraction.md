# Literature extraction: does the field classify outcomes or causes?

The paper's central framing is that in-situ LPBF monitoring research classifies
**outcomes** - keyhole porosity, lack of fusion, balling, density, roughness -
while the question of whether a sensor suite can separate the **causes** that
produced them has not been asked. That claim has to be backed by a table, not
an assertion, so this is the table.

Each row records what the work takes as input, what it produces as output, which
class that output belongs to, and whether it anywhere analyses whether two
different causes can be told apart.

## Verification status - read this before citing anything here

Outbound network access in this environment permits search only: `doi.org` is
blocked by policy and the publisher hosts do not resolve. **Rows marked (A) were
read from search-result abstracts and metadata, not from the full text.** Four
papers have been read in full and are marked (F); those are the ones from the
uploaded PDFs. Before submission every row used in the paper must be checked
against the actual article - the classification in the "class" column is the
part most at risk, because an abstract can easily omit an identifiability
discussion buried in a discussion section.

## The table

| # | Work | Input | Output | Class | Cause separation analysed? | Ver |
|---|---|---|---|---|---|---|
| 1 | Guo et al., *Additive Manufacturing* 28:600-609, 2019 | in-situ high-speed high-energy X-ray imaging | melt pool dimension and volume at **constant** energy density | cause-level physics | No, but demonstrates that VED is an incomplete metric because power and speed act separately through absorption | A |
| 2 | k-NN parameter estimation, *Int. J. Adv. Manuf. Technol.*, 2025, DOI 10.1007/s00170-025-15591-y | melt pool images (NIST data) | **energy density class**, 91.4% 5-fold CV | cause, but **lumped** | No | A |
| 3 | Raj et al., *J. Manufacturing Processes* 89:24-38, 2023 | coaxial MPM: CMOS area + photodiode intensity, IN718, GE Concept Laser M2 | ML surrogate predicting **spatial variation** in area and intensity, attributed to beam/shield-gas interaction | nuisance correction | No | A |
| 4 | Owen et al., *Trans. American Nuclear Society*, 2023 | coaxial in-situ melt pool signals | spatial features | feature engineering | No | A |
| 5 | Scime & Beuth, *Additive Manufacturing*, 2019 | high-speed visible camera | keyholing porosity, balling | outcome | No | A |
| 6 | RAISE-LPBF benchmark, arXiv 2409.12475 | on-axis video, 316L | reconstructed laser power and speed | cause, separate | Regression accuracy only, no identifiability analysis | A |
| 7 | Akbari et al. (MeltpoolNet), *Additive Manufacturing* 55:102817, 2022 | published melt pool geometry across alloys | melt pool mode / defect class | outcome | No | A |
| 8 | ThermoPore, arXiv 2404.16882 | thermal images | part porosity | outcome | No | A |
| 9 | CMU, arXiv 2310.05289 | acoustic + photodiode, wavelet scalograms | melt pool visual characteristics, lack-of-fusion, R2 >= 0.8 | outcome | No | A |
| 10 | Predicting mechanical properties from coaxial MPM, OSTI 2000647 | coaxial MPM signals | mechanical properties | outcome | No | A |
| 11 | Liu et al., *Additive Manufacturing*, 2022 | infrared camera, post-recoat heat-up, 1-D model | **local powder layer thickness and thermal conductivity** | cause, separate | No; and it needs added hardware | A |
| 12 | Bugatti & Colosimo, *Additive Manufacturing Letters*, 2022 | recoater-mounted optical scanner | surface topography anomalies, contamination < 100 um | outcome; added hardware | No | A |
| 13 | Brenner et al., *Progress in Additive Manufacturing*, 2023 | simulation of recoater crashes | stripe irregularities in the powder bed | outcome | No | A |
| 14 | Photodiode MPM + ML for off-size Ti6Al4V, *Inventions* 9(4):87, 2024 | photodiode MPM | tailored process parameters | forward optimisation | No | A |
| 15 | Weaver et al., *Integrating Materials and Manufacturing Innovation* 13:363-379, 2024 | cross-sectional microscopy, AM-Bench single tracks | melt pool width and depth vs VED; depth tracks VED, width does not | cause-level physics | No, but is direct evidence that width carries information depth does not | F |
| 16 | Honarmandi et al., *Additive Manufacturing* 47:102300, 2021 | Bayesian calibration of Eagar-Tsai with keyhole correction | calibrated absorptivity, conductivity, heat capacity | cause, separate | **Reports parameter correlations of 0.93-0.96** - the only entry that confronts confounding, and it does so in calibration, not diagnosis | F |
| 17 | NIST AMS 100-35, Lane et al., 2020 | thermal calibration of an in-situ system | calibration RMSE 4.934 degrees C | instrumentation | No | F |
| 18 | *Additive Manufacturing* multi-laser load balancing, 2023 + US 12,257,627 | - | productivity scheduling | unrelated, recorded to close a rejected candidate | A |

## What the table shows

**Outcome classification dominates.** Rows 5, 7, 8, 9, 10, 12, 13 all map signals
to a defect or a property. This is the mature part of the field.

**Cause estimation exists but takes three forms, none of them this paper's.**
Row 2 predicts the *lumped* group, energy density, which is what you fall back on
precisely when the components are confounded. Row 6 regresses power and speed
separately from video and reports accuracy without ever asking whether the two
are separable in principle. Row 11 infers layer thickness, but needs an extra
infrared camera.

**Row 1 is the motivation and it is strong.** Guo et al. show experimentally that
at constant energy density the melt pool varies by orders of magnitude, because
power and speed change absorption differently. So the field already knows the
lumped metric is incomplete. Yet row 2, six years later, is still predicting the
lumped class. Nobody closed the loop by asking what a given sensor suite can
separate in principle. That is a three-citation motivation chain and it is the
cleanest statement of the gap found so far:

> energy density is an incomplete metric (Guo 2019), state-of-the-art in-situ
> parameter estimation nonetheless predicts energy density class (2025), and no
> work asks whether the individual causes are separable from a given sensor
> suite at all.

**Row 16 is the one honest confrontation with confounding in the literature**, and
it is in *calibration*: Honarmandi et al. report 0.93-0.96 correlations between
fitted absorptivity, conductivity and heat capacity. Same mathematical pathology,
different purpose. It should be cited as the precedent for taking the problem
seriously, and as the reason the paper's own calibration carries that caveat.

## Row 3 is the closest prior art and needs careful positioning

Raj et al. 2023 observe significant **spatial variation** in coaxial melt pool
area and intensity on IN718, on a production machine, with the same sensor pair
this work models, and attribute it to the interaction of the angled beam with
the shield gas flow. They then build ML surrogates to **predict and compensate**
that variation.

Two things follow, one helpful and one demanding.

**Helpful: one of the five asserted modulation profiles now has independent
experimental corroboration.** The gas profile - severity varying along the flow
direction - was the weakest of the five hand-written claims, and here is a
published IN718 coaxial-MPM study attributing observed spatial signal variation
to exactly that mechanism. It should be cited at the point where the profile is
asserted, and the paper should say plainly that the other four do not yet have
equivalent support.

**Demanding: the distinction must be stated explicitly and early**, because a
reviewer who knows this paper will otherwise see Route A as a relabelling of it.
The distinction is real and it is a matter of what the variation is *for*:

- Raj et al.: spatial variation is a **systematic nuisance**. Model it, subtract
  it, recover a cleaner signal for control.
- This work: spatial variation is **the information that breaks a structural
  confound**. Power and gas have exactly parallel instantaneous signatures - the
  ratio of their Jacobian columns is 1/c_gas in every sensor - so no amount of
  instantaneous signal cleaning can separate them. Their spatial signatures
  differ, and that is what makes them separable at all.

Put bluntly: they remove the thing this paper uses. That is a clean, defensible
and quotable separation, and it is stronger for citing them prominently rather
than burying them.

## Still to do

- Reach the full text of rows 1, 2, 3 and 6 at minimum. Rows 2 and 3 decide
  novelty positioning; row 1 is the motivation; row 6 is the nearest
  cause-estimation work.
- Two more searches that have not been run: shielding-gas flow monitoring as a
  diagnostic signal, and structural-analysis FDI applied to any additive process
  (the latter was covered in the novelty check and came back empty, but it
  belongs in this table as an explicit null row).

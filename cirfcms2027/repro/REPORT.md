# Reproduction report

`230` claims checked, `230` reproduced, `0` not.

Every row is a number the paper prints. **paper** is what it prints,
**code** is what this repository computes, and a row passes only if the
computed value rounds to the printed one (see `claims.py` for the
tolerance rule and the exceptions for stated bounds).

`kind` is `computed` for a number this repository derives from the
forward model, `source` for a measurement or reported fit taken from a
cited work - not recomputable here, so what is checked is that the
paper and the code carry the same figure - and `convention` for a
threshold or unit this work chose.

## Section 3.1

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `cal.width-mape` | 11.7 % | 11.6611 | computed | Mean absolute percentage error on melt pool width over the seven AM-Bench single-track conditions, after fitting four effective parameters. |
| ok | `cal.depth-mape` | 13.1 % | 13.0607 | computed | The same, on depth. |
| ok | `cal.n-conditions` | seven | 7 | computed | Number of AM-Bench bare-plate single-track conditions fitted. |
| ok | `cal.baseline-power` | 285 W | 285 | source | The benchmark's own baseline laser power, at which all results are evaluated. *(source: Weaver et al. (2024) Table 4, case 0)* |
| ok | `cal.baseline-speed` | 960 mm/s | 960 | source | Baseline scan speed. *(source: Weaver et al. (2024) Table 4, case 0)* |
| ok | `cal.baseline-spot` | 67 um | 67 | source | Baseline D4-sigma spot diameter. *(source: Weaver et al. (2024) Table 4, case 0)* |
| ok | `cal.baseline-width-err` | -15.5 % | -15.5393 | computed | The model's signed width error at the baseline condition: it under-predicts. |
| ok | `cal.baseline-depth-err` | +1.7 % | 1.71835 | computed | The model's signed depth error at the baseline condition. This is why depth is the channel the profile inversions of Section 3.5 run through. |
| ok | `cal.U-width` | 6.2 um | 6.2 | source | Expanded measurement uncertainty (k = 2) on the baseline width, from the benchmark's own metrology budget. *(source: Weaver et al. (2024) Table 4, case 0)* |
| ok | `cal.U-depth` | 14.1 um | 14.1 | source | The same, on depth. *(source: Weaver et al. (2024) Table 4, case 0)* |
| ok | `cal.all-under` | all seven conditions | 7 | computed | Width is under-predicted at every condition, not scattered about zero: the one-sided bias of a conduction solution with no mechanism that widens a pool. |
| ok | `cal.aspect-lo` | 0.72 | 0.722653 | computed | Smallest measured depth-to-width ratio of the seven tracks. Honarmandi's keyholing criterion is depth >= width / 1.5, i.e. 0.667, so every condition is keyholing. |
| ok | `cal.aspect-hi` | 2.14 | 2.13936 | computed | Largest measured depth-to-width ratio. |
| ok | `cal.n-keyholing` | all seven cases keyhole | 7 | computed | Conditions meeting the keyholing criterion, applied to the measured dimensions so it does not depend on the model being corrected. |
| ok | `cal.conduction-depth` | 23.6 % | 23.6268 | computed | Depth error of a pure conduction fit with the same three free parameters over the same bounds - the like-for-like comparison that makes the keyhole term necessary rather than cosmetic. |
| ok | `cal.conduction-width` | 8.5 % | 8.53851 | computed | Width error of that same conduction-only fit: essentially unchanged, so the keyhole term buys depth without costing width. |
| ok | `cal.keyhole-criterion` | the criterion's 0.67 | 0.666667 | convention | Honarmandi's keyholing criterion restated as a depth-to-width ratio: depth >= width / 1.5. Applied to the measured dimensions, so it does not depend on the model being corrected. |
| ok | `cal.step` | h = 0.002 | 0.002 | convention | The central-difference step at which every Jacobian in the paper is evaluated. |
| ok | `cal.step-change-002` | 39.3 % | 39.3452 | computed | Largest relative change in any Jacobian entry between h = 0.04 and h = 0.02: the derivative has not converged at those steps. |
| ok | `cal.step-change-0005` | below 0.3 % | 0.252802 | computed | The same between h = 0.01 and h = 0.005, by which point it has. |

## Section 3.2

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `fault.geometry-unit` | 100 K | 100 | convention | The geometry fault is a local preheat rise, one unit being 100 K. |
| ok | `fault.absorptivity-coupling` | -0.230 | -0.230245 | computed | d(ln A)/d(ln t) for a powder bed whose absorptivity saturates with depth, negated because the fault is positive for a thinner layer. Derived, not chosen. |
| ok | `fault.trapp-ratio` | approximately two | 2 | source | Powder-to-solid absorptivity ratio measured calorimetrically in situ. *(source: Trapp et al. (2017), Applied Materials Today 9)* |
| ok | `fault.trapp-wavelength` | 1070 nm | 1070 | source | Wavelength of that measurement. *(source: Trapp et al. (2017))* |
| ok | `fault.implied-solid-absorptivity` | 0.258 | 0.258311 | computed | Bare-solid absorptivity implied by dividing the fitted effective value by the powder enhancement. It lands inside the 0.25-0.35 published for nickel alloys near 1 um, which the calibration was not built to do. |
| ok | `fault.enthalpy-coupling` | +0.186 | 0.185837 | computed | The effective-power coupling of a layer-thickness change, phi/(1-phi), from the share of absorbed energy spent melting the powder itself. |
| ok | `fault.phi` | 15.7 % | 15.6714 | computed | That share: melting the nominal layer consumes 15.7 % of the absorbed energy per unit track length. |
| ok | `fault.net-product` | -0.044 | -0.044 | computed | The two derived channels act on the same product (absorptivity x power) and nearly cancel there. What is left is the unmeasured conductivity channel, which is therefore the one thing that distinguishes a thin layer from a weak laser at an instant. |
| ok | `fault.power-layer-no-conductivity` | 0.00 deg | 3.15781e-05 | computed | With the conductivity channel removed, the layer fault acts only through the absorbed-power product and joins the power/gas degeneracy exactly. |
| ok | `fault.layer-gas-no-conductivity` | 0.00 deg | 0.000141551 | computed | The same for the layer/gas pair. |

## Section 3.4

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `measure.floor` | 10 deg | 10 | convention | The practical separation floor adopted as a convention throughout. |
| ok | `measure.rank-tol` | 1e-6 | 1e-06 | convention | A singular value below this fraction of the largest counts as no direction at all. |

## Section 3.5

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `ctx.n-segments` | N = 84 | 84 | computed | Segments in the default synthetic build plan: six layers of fourteen scan vectors. |
| ok | `ctx.n-observables` | 15 observables | 15 | computed | Three sensors times five regression coefficients each, in place of three instantaneous readings. |
| ok | `ctx.root-diag-lo` | 0.109 | 0.109109 | computed | Smallest of the five sqrt[(G'G)^-1]_jj factors by which fitting 84 segments to five regressors reduces each coefficient's noise. |
| ok | `ctx.root-diag-hi` | 0.136 | 0.13604 | computed | Largest of those factors. |
| ok | `ctx.noise-reduction` | a seven- to ninefold | 9.16515 | computed | The reciprocal of the smallest factor. The reduction runs from about sevenfold to about ninefold across the five coefficients. |
| ok | `ctx.cross-flow` | 4.3 m/s | 4.3 | source | Argon cross-flow speed over the benchmark pads. *(source: Weaver et al. (2024))* |
| ok | `ctx.pad-mean` | 27.2 % | -27.1774 | source | Mean depth reduction on pad tracks scanned parallel to the gas flow against anti-parallel ones, over four cross-sections. *(source: Weaver et al. (2024) Table 5, Y-pad; computed from the twelve depths recorded in weaver_pads.py)* |
| ok | `ctx.pad-sd-lo` | 4 um | 3.9 | source | Smallest standard deviation across the twelve Table 5 rows. The effect is about 50 um against a scatter of about 10 um. *(source: Weaver et al. (2024) Table 5)* |
| ok | `ctx.pad-sd-hi` | 11 um | 10.7 | source | Largest of those standard deviations. *(source: Weaver et al. (2024) Table 5)* |
| ok | `ctx.control-lo` | 2.4 % | -2.41 | source | The perpendicular control pad's smaller depth change, which is what makes the parallel effect attributable to the gas rather than to scan reversal. *(source: Weaver et al. (2024) Table 5)* |
| ok | `ctx.control-hi` | 4.7 % | -4.71 | source | Its larger one. *(source: Weaver et al. (2024) Table 5)* |
| ok | `ctx.f-gas-control` | 0.046 | 0.0461342 | computed | Gas-fault severity implied by the control pad's depth change, inverted through the model's depth channel. |
| ok | `ctx.f-gas-parallel` | 0.404 | 0.40389 | computed | The same for the parallel-track mean. |
| ok | `ctx.swing` | 8.8x | 8.75468 | computed | Ratio of those two: the gas channel's effective severity swings this much inside a single healthy build, from scan direction alone. |
| ok | `ctx.asserted-swing` | 6.05x | 6.04965 | computed | The swing of the gas profile this work assumes, exp(2c) at c = 0.90. |
| ok | `ctx.measured-contrast` | 1.08 | 1.08479 | computed | The measured swing in contrast units, ln(swing)/2, which is what makes it comparable with the asserted profile. |
| ok | `ctx.asserted-contrast` | 0.90 | 0.9 | convention | The asserted gas contrast. |
| ok | `ctx.understatement` | 20 % | 20.5327 | computed | By how much the one profile that can be checked against measurement is understated - in the direction that costs this analysis nothing. |

## Section 3.6

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `noise.weaver-width-pct` | 2.3 % | 2.27439 | source | The only citable in-process-adjacent figure found: a relative width uncertainty from a cross-sectional metrology budget - which is not in-process noise, which is why the figures are derived instead. *(source: Weaver et al. (2024), 3.1 um on 136.3 um)* |
| ok | `noise.wien` | 1.333 | 1.33261 | computed | /d ln R / d ln T/ for a two-colour ratio at 750/950 nm in the Wien limit: (c2/T)(1/lambda2 - 1/lambda1). The inversion divides by this, so closely spaced bands amplify noise. |
| ok | `noise.peak-T` | 3031 K | 3030.64 | computed | The model's peak melt pool temperature, at which that sensitivity is evaluated. |
| ok | `noise.pyrometer` | 1.061 | 1.06123 | computed | The pyrometer's relative noise in units of the photodiode's: sqrt(2) from two independent channels, divided by the ratio's temperature sensitivity. A two-colour pyrometer is a noisier relative instrument than the photodiode it is built from. |
| ok | `noise.planck` | 10.52 | 10.5204 | computed | d ln L / d ln T at 850 nm and the liquidus, 1609 K. Planck is steep there, which is why an intensity threshold localises an edge well. |
| ok | `noise.isotherm-shift` | 0.095 % | 0.0950539 | computed | How far a 1 % radiance error displaces the apparent liquidus isotherm, in temperature. |
| ok | `noise.camera` | 0.142 | 0.142188 | computed | The camera's relative noise, from propagating that isotherm shift through the model's own dimension solver. |
| ok | `noise.photodiode` | 1 | 1 | computed | The photodiode reading is a band-integrated radiometric power, so its relative noise is the shared fractional radiometric noise itself. It serves as the unit, and only ratios enter the whitening. |
| ok | `noise.camera-factor` | a factor of seven | 7.03293 | computed | How much more precise the camera is than the photodiode, in relative terms. |

## Section 4.1

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `val.guo-depth` | 2.37x | 2.37214 | computed | Span of melt pool depth across the constant-energy-density sweep. Guo et al. report orders of magnitude, so this is a partial pass: the existence, direction and regime transition reproduce, the magnitude does not. |
| ok | `val.guo-length` | 2.53x | 2.53068 | computed | Span of melt pool length over the conduction-regime rows of the same sweep, so the keyhole jump cannot flatter it. Length carries the variation that width and depth do not. |
| ok | `val.guo-width` | 1.11x | 1.10603 | computed | Span of width over those rows. |
| ok | `val.n-melted` | 27 melted conditions | 27 | computed | Conditions in the primary energy-density grid that produced a melt pool. |
| ok | `val.r-width` | +0.20 | 0.201129 | computed | Log-log correlation of width with volumetric energy density on that grid. |
| ok | `val.r-depth` | +0.77 | 0.76677 | computed | The same for depth: depth tracks energy density, width does not, which is the structure the benchmark reports. |
| ok | `val.r-width-hi` | +0.68 | 0.677329 | computed | Largest value width's correlation takes across the five grids. It runs right across zero, so the correlation is a property of the sampled region rather than of the model - which is why the paper reports exponents instead. |
| ok | `val.r-width-lo` | -0.22 | -0.223307 | computed | Its smallest value. |
| ok | `val.r2-floor` | R2 >= 0.94 | 0.947072 | computed | Worst coefficient of determination of a (P, v, d) power-law fit to width or depth over all five grids. The exponents are stable where the correlation is not. |
| ok | `val.cos-depth-lo` | 0.64 | 0.641672 | computed | Smallest cosine between depth's fitted exponents and the (1, -1, -2) ray a pure function of energy density must lie along. |
| ok | `val.cos-depth-hi` | 0.74 | 0.735696 | computed | Its largest. |
| ok | `val.cos-width-lo` | -0.11 | -0.107244 | computed | Smallest cosine for width - essentially orthogonal to the ray on every grid, because width and depth depend on spot size with opposite signs and spot size is the one variable a volumetric density folds away. |
| ok | `val.cos-width-hi` | 0.00 | 0.00229203 | computed | Its largest. |

## Section 4.2

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `conf.ratio-pd` | -0.99999 | -0.999991 | computed | Ratio of the power and gas Jacobian columns at the photodiode. The two faults act only on the product (effective absorptivity x power), in which the temperature rise is linear, so the columns are the same vector. |
| ok | `conf.ratio-cam` | -1.00000 | -1 | computed | The same at the camera. |
| ok | `conf.ratio-pyr` | -0.99993 | -0.999932 | computed | The same at the pyrometer. |
| ok | `conf.ratio-spread` | 7e-5 | 7.05938e-05 | computed | Spread of those three, which is finite-difference error on an exact identity rather than physics. |
| ok | `conf.identity` | eight significant figures | 0 | computed | Largest relative difference between the nominal readings and those under a simultaneous power fault f and gas fault ln(1+f), over f from 2 % to 20 %. The two cancel exactly: the readings are bit-identical in double precision, so the paper's 'eight significant figures' understates it. |
| ok | `conf.angle` | 0.00 deg | 0.000110011 | computed | The pairwise angle between the whitened power and gas columns. Zero by algebra, not by noise. |
| ok | `conf.sweep-max` | 0.00 deg | 0.000110011 | computed | The largest that angle reaches over every coupling constant swept across its plausible range: the degeneracy is not an artefact of a chosen constant. |

## Section 4.3

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `melt.corr-pd-cam` | 0.99960 | 0.999596 | computed | Correlation between the photodiode's and the camera's response patterns across the five faults, from the normalised sensor Gram matrix. Row scalings cancel in the normalisation, so this is the one result here that does not depend on the derived noise figures. |
| ok | `melt.corr-pd-pyr` | 0.99508 | 0.995084 | computed | The same for photodiode and pyrometer. |
| ok | `melt.corr-cam-pyr` | 0.99477 | 0.994768 | computed | The same for camera and pyrometer. |
| ok | `melt.sv1` | 13.14 | 13.1396 | computed | Largest singular value of the whitened Jacobian: the suite's response along its dominant direction, in noise widths. |
| ok | `melt.sv2` | 0.0638 | 0.063757 | computed | The second. |
| ok | `melt.sv3` | 0.00513 | 0.00512907 | computed | The third. |
| ok | `melt.energy` | 99.998 % | 99.9976 | computed | Share of the suite's squared response lying along that one direction. |
| ok | `melt.rank` | Three of the five fault directions | 3 | computed | Effective rank of the whitened Jacobian: how many fault directions are observable at all. |
| ok | `melt.unobserved` | two are not observed at all | 2 | computed | The remaining directions, spanning the power-gas combination. |
| ok | `melt.cond` | 2562 | 2561.78 | computed | Condition number: the weakest observed direction responds this many times less than the strongest. |
| ok | `melt.seven-rank` | does not raise the attained rank | 3 | computed | Rank with all seven candidate observables fitted. Seven instruments leave power and gas exactly as confounded as one. |
| ok | `melt.seven-sv1` | 23.7 | 23.7056 | computed | First singular value of the seven-row whitened Jacobian. |
| ok | `melt.seven-sv2` | 9.74 | 9.74334 | computed | The second. |
| ok | `melt.seven-sv3` | 6.0e-2 | 0.0601123 | computed | The third. |
| ok | `melt.seven-sv4` | 5.0e-6 | 4.96707e-06 | computed | The fourth, which is below the rank threshold. |
| ok | `melt.seven-sv5` | 1.4e-6 | 1.42628e-06 | computed | The fifth. |
| ok | `melt.seven-sv4-ratio` | 2e-7 | 2.09532e-07 | computed | The fourth singular value as a fraction of the leading one: two orders below the threshold adopted here, so four directions are formally present but only three are measurements. |
| ok | `melt.channel-bound` | rank 4 | 4 | convention | The structural bound. Everything the model knows funnels into four physical channels - absorbed power, scan speed, effective conductivity and preheat - so no instrument reading only the melt pool can exceed it, however many are fitted. |

## Section 4.4

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `ctx.rank` | rank rises from 3 to 5 | 5 | computed | Rank of the enlarged observation: all five fault directions become observable. |
| ok | `ctx.worst` | 24.90 deg | 24.9008 | computed | The worst pair over a build, against 0.00 per segment. This is the paper's headline number and the pair is power/speed. |
| ok | `ctx.power-gas` | 29.34 deg | 29.3403 | computed | Power against gas over a build: the pair that is exactly confounded instantaneously. |
| ok | `ctx.cond` | falls from 2562 to 50 | 49.7638 | computed | Condition number of the enlarged observation. |
| ok | `ctx.cleared` | all ten pairs clearing | 10 | computed | Pairs clearing the 10-degree floor over a build. |
| ok | `ctx.inst-cleared` | against none per segment | 0 | computed | Pairs clearing it per segment. |
| ok | `ctl.shared-rank` | rank 3 | 3 | computed | Rank when all five faults are given one identical profile. The enlarged matrix still has 15 rows, so the gain is not dimensionality: proportional columns of B make it inherit the instantaneous column directions. |
| ok | `ctl.shared-cond` | condition number 2562 | 2561.78 | computed | Its condition number - the instantaneous value exactly. |
| ok | `ctl.shared-worst` | 0.00 deg | 0.000110008 | computed | Its worst pair: the instantaneous result returns exactly. |
| ok | `sec.rank5` | rank 5 at every magnitude | 1 | computed | Whether replacing every derivative by a secant through the full nonlinear chain still gives rank 5, at every magnitude tested in both signs. |
| ok | `sec.mag-lo` | 0.2 % | 0.2 | computed | Smallest fault magnitude at which the secant check is run. |
| ok | `sec.mag-hi` | 20 % | 20 | computed | Largest. |
| ok | `sec.binding-lo` | 12.82 deg | 12.8215 | computed | Smallest value the baseline binding pair (power/speed) takes across those magnitudes, at +20 %. So the derivative limit is not strictly conservative. |
| ok | `sec.binding-hi` | 37.95 deg | 37.9461 | computed | Its largest, at -20 %. |
| ok | `sec.cond-lo` | 47 | 47.4713 | computed | Smallest condition number over those magnitudes. |
| ok | `sec.cond-hi` | 62 | 62.1412 | computed | Largest. |
| ok | `sec.margin` | 1.3x | 1.28215 | computed | How far the +20 % case clears the floor. |
| ok | `sec.exact` | 0.04 deg | 0.040811 | computed | Largest angle disagreement between the interpolated response curves and recomputing the full model at every one of the 84 segments. |

## Section 4.5

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `rob.n-at-25` | five of ten pairs | 5 | computed | Pairs clearing the floor at or below a quarter of the asserted profile strength. |
| ok | `rob.hardest` | 45 % | 0.45089 | computed | The strength the hardest pair, power/speed, needs. A machine whose patterns are half as strong still resolves every pair. |
| ok | `rob.n-perm` | all 120 permutations | 120 | computed | Ways of reassigning which fault follows which build variable. |
| ok | `rob.perm-rank5` | survives every one | 120 | computed | Assignments that still give rank 5. |
| ok | `rob.perm-cleared` | survives every one | 120 | computed | Assignments in which all ten pairs still clear the floor. |
| ok | `rob.perm-lo` | 16.2 deg | 16.2261 | computed | Smallest the worst pair becomes over those 120 assignments. It does not matter which fault follows which variable, only that they differ - but the headline does move, by up to about nine degrees. |
| ok | `rob.perm-hi` | 30.1 deg | 30.1255 | computed | Its largest. |
| ok | `rob.noise-sets` | all four noise sets | 4 | computed | Noise assumptions swept: the derived set, a gain-dominated pyrometer, a perimeter-averaged camera, and equal noise on every channel. |
| ok | `rob.noise-spread` | under half a degree | 0.0838217 | computed | How far the headline moves across those four sets. |
| ok | `rob.coupling-spread` | the full range of the unmeasured conductivity coupling | 0 | computed | How far the headline moves across every coupling constant swept over its plausible range. |
| ok | `rob.N12` | 11.23 deg | 11.2312 | computed | The worst pair with only twelve segments: the regression has barely enough to fit five regressors. |
| ok | `rob.N30` | 22.90 deg | 22.8974 | computed | With thirty. |
| ok | `rob.N84` | flat thereafter | 24.9008 | computed | With the default 84. |
| ok | `rob.N288` | flat thereafter | 24.9405 | computed | With 288: flat, so segment count stops binding well before the default plan. |
| ok | `rob.collapse` | collapses that pair to its instantaneous angle | 3.313e-09 | computed | Largest disagreement between a forced-equal pair's angle and its instantaneous angle, over all ten pairs. Forcing two profiles equal returns that pair exactly to where it was per segment. |
| ok | `rob.mildest` | 4.63 deg | 4.63038 | computed | The mildest instantaneous angle, which is still below the floor - so no pair of faults may share a spatial signature. |
| ok | `rob.support-tolerance` | roughly 84 % | 0.841662 | computed | How much of the layer profile may be driven by part support, rather than by the recoater cycle assumed here, before layer/geometry falls below the floor. Liu et al. measure layer-thickness variation following support, so this is the relevant failure. |
| ok | `rob.support-at-80` | 12.07 deg | 12.0744 | computed | The layer/geometry angle at 80 % support-driven. |
| ok | `rob.drift-never` | never brings power/layer below it | 0 | computed | Whether mixing the power fault's build-drift driver into the layer profile ever takes power/layer below the floor. It does not: every profile is normalised to unit mean, so two faults sharing a driver give (1, a) and (1, b), which are non-proportional wherever the contrasts differ. |

## Section 4.6

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `cfg.A-rank` | rank 1 | 1 | computed | Rank of a single coaxial photodiode. |
| ok | `cfg.B-rank` | rank 2 | 2 | computed | Rank of photodiode plus pool imaging. |
| ok | `cfg.C-rank` | rank 2 | 2 | computed | Rank of two photodiodes in separate bands. |
| ok | `cfg.D-rank` | rank 3 | 3 | computed | Rank of the research reference, which adds pyrometry. |
| ok | `cfg.E-rank` | rank 3 | 3 | computed | Rank of two photodiodes plus upstream power monitoring. |
| ok | `cfg.A-power-gas` | 0.00 deg | 0 | computed | Power against gas for configuration A. |
| ok | `cfg.B-power-gas` | 0.00 deg | 0.000108872 | computed | The same for B. |
| ok | `cfg.C-power-gas` | 0.00 deg | 0.000110826 | computed | For C. |
| ok | `cfg.D-power-gas` | 0.00 deg | 0.000110011 | computed | For D. No configuration built solely from melt-pool observables separates the pair, whatever its sensor count. |
| ok | `cfg.E-power-gas` | 84.02 deg | 84.0158 | computed | For E, which samples delivered laser power upstream of the process zone and so sees the laser output without the plume attenuation. |
| ok | `cfg.E-cleared` | resolves four of ten | 4 | computed | Pairs E resolves per segment - the only class that resolves any. |
| ok | `cfg.corr-two-bands` | 0.99996 | 0.999964 | computed | Correlation between two photodiode bands of the same emitted light. B and C are separated not by class count, both empty, but by this. |
| ok | `cfg.corr-geometric` | 0.99960 | 0.999596 | computed | The same for a geometric measurement against a radiometric one. |
| ok | `cfg.class3-inst` | class 3 empty in both | 0 | computed | Structurally irreducible pairs per segment for the baseline suite. |
| ok | `cfg.class3-acc` | class 3 empty in both | 0 | computed | The same over a build. |
| ok | `cfg.class1-acc` | all ten pairs in class 1 | 10 | computed | Pairs resolvable from existing signals over a build. |

## Section 4.7

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `add.direct-rank` | raises the rank to 4 | 4 | computed | Rank after adding one idealised direct measurement of a cause. |
| ok | `add.direct-cleared` | clears exactly the four pairs | 4 | computed | Pairs it clears: the four involving that cause, no more. |
| ok | `add.geometry-rank` | raising the rank not at all | 3 | computed | Rank after adding a direct measurement of geometry - unchanged, because a unit row on geometry already lies inside the existing row space. |
| ok | `add.projection-geometry` | 1.0000 | 1 | computed | Projection of a unit row on geometry onto the row space of the three existing sensors. The suite observes preheat already and simply cannot separate the rest. |
| ok | `add.projection-lo` | 0.53 | 0.533532 | computed | Smallest such projection for the other four causes. |
| ok | `add.projection-hi` | 0.91 | 0.906193 | computed | Largest. |
| ok | `add.precision-worst` | 0.32 deg | 0.323432 | computed | The worst pair with an added gas sensor, unchanged across the whole precision sweep. Adding a row in a new direction changes the rank; making an existing row quieter does not. |
| ok | `add.precision-worst-hi` | 0.32 deg | 0.323432 | computed | The same at the other end of the sweep - it does not move. |
| ok | `add.precision-noise-hi` | 50 % | 50 | computed | Coarsest added-sensor noise swept. |
| ok | `add.precision-noise-lo` | 0.2 % | 0.2 | computed | Finest. |
| ok | `add.precision-cleared` | four of ten cleared throughout | 4 | computed | Pairs cleared, constant across that sweep. |
| ok | `add.two-rank` | rank 5 | 5 | computed | Rank with idealised direct gas and layer sensors together. |
| ok | `add.two-worst` | 0.70 deg | 0.704525 | computed | Their worst pair - neither says anything about power against speed, so build context outperforms two perfect direct measurements of the causes themselves. |
| ok | `add.two-cleared` | seven of ten | 7 | computed | Pairs they clear. |
| ok | `add.split-gain` | +23.89 deg | 23.8907 | computed | What reporting the camera's two axes separately is worth on the pair that binds the baseline accumulated result, power/speed. |
| ok | `add.split-power-speed` | 48.79 deg | 48.7915 | computed | That pair's angle after the split, against 24.90 before. |
| ok | `add.split-worst` | 25.26 deg | 25.2551 | computed | The suite's worst accumulated pair after the split. Power/speed stops binding and power/geometry takes over, so the suite's worst improves by only 0.35 degrees even though the old binding pair nearly doubles. *(note: not in the paper as drafted; the paper should say it)* |
| ok | `add.split-inst-cleared` | seven of ten | 7 | computed | Pairs the split clears per segment, from none of ten - the only change that resolves anything instantaneously. |
| ok | `add.swir-gain` | +0.01 deg | 0.00799714 | computed | What a short-wave infrared photodiode is worth on the same pair. |
| ok | `add.wide-gain` | 0.00 deg | 4.80636e-05 | computed | What a wide-band pyrometer is worth. |
| ok | `add.corr-width` | 0.779 | 0.779301 | computed | Correlation of melt pool width with the coaxial photodiode: the least correlated of the candidates, which is why splitting the camera helps. |
| ok | `add.corr-length` | 0.979 | 0.979063 | computed | The same for length, which is both more responsive and less independent. An area averages the informative axis against the uninformative one and buries it. |

## Section 5.1

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `lit.n-works` | 19 works | 19 | computed | Rows in the literature extraction table. |
| ok | `lit.year-lo` | 2019 | 2019 | computed | Earliest publication year among them. |
| ok | `lit.year-hi` | 2025 | 2025 | computed | Latest. |
| ok | `lit.n-outcome` | seven | 7 | computed | Works that map signals onto a defect, a property or a surface state. |
| ok | `lit.n-inputs` | three | 3 | computed | Works that estimate a process input from an in-situ signal. |
| ok | `lit.n-lumped` | one of those a lumped energy-density class | 1 | computed | Of those three, how many predict the lumped group rather than its components. |
| ok | `rej.reported-b` | b = 0.337 | 0.337 | source | The speed-response exponent reported for a commercial coaxial photodiode at 400 W. *(source: Reijonen (2024), Addit. Manuf. Lett. 11, 100244, Table 2)* |
| ok | `rej.power` | 400 W | 400 | source | The power at which it is quoted. *(source: Reijonen (2024))* |
| ok | `rej.speed-lo` | 400 mm/s | 400 | source | Lower end of the speed range it was fitted over. *(source: Reijonen (2024))* |
| ok | `rej.speed-hi` | 1200 mm/s | 1200 | source | Upper end. *(source: Reijonen (2024))* |
| ok | `rej.jacobian-entry` | -0.483 | -0.483469 | computed | This model's photodiode sensitivity to scan speed as a Jacobian entry - a derivative at a point, which is not the comparable quantity. |
| ok | `rej.fit-400` | 0.468 | 0.467703 | computed | The comparable quantity: the same power law fitted to this model over their speed range at their power. |
| ok | `rej.excess` | 39 % | 38.7843 | computed | By how much that is too steep. |
| ok | `rej.fit-100` | 0.51 | 0.511093 | computed | The same fit at 100 W, where they report the trend as almost non-existent. |
| ok | `rej.fit-285` | 0.44 | 0.437105 | computed | At 285 W. |
| ok | `rej.flat` | flat | 0.0739879 | computed | Total spread of the fitted exponent over 100-400 W. Theirs grows strongly with power; this model's does not, because a plume of fixed optical depth has no mechanism by which it could. |
| ok | `rej.relative-power` | +1.52 | 1.51768 | computed | This model's relative photodiode sensitivity to laser power. Reijonen report a linear fit without quoting its intercept, and relative sensitivity is aP/(aP+b), equal to one only through the origin, so this cannot be called a conflict until the intercept is known. |

## Section 5.2

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `lim.honarmandi-lo` | 0.93 | 0.93 | source | Smallest pair correlation reported between fitted absorptivity, conductivity and heat capacity during Bayesian calibration of this model family - the pathology this paper studies, appearing in its own calibration. *(source: Honarmandi et al. (2021), Addit. Manuf. 47, 102300)* |
| ok | `lim.honarmandi-hi` | 0.96 | 0.96 | source | Largest. *(source: Honarmandi et al. (2021))* |
| ok | `lim.gas-width` | -10 % | -9.96761 | computed | The width change this model gives at a gas severity of 0.4. Reijonen et al. (2020) report reduced gas flow giving loss of penetration with *increased* width, so the sign is wrong - attenuation alone shrinks everything. |
| ok | `lim.scatter-lo` | 2 deg | 2.05103 | computed | Power against gas once the gas fault is given a second channel - a spot size broadening with plume optical depth, which power does not possess - at the broadening that reverses the width sign. The paper quotes the pair as 2-3 degrees, to one figure. |
| ok | `lim.scatter-hi` | 3 deg | 3.00529 | computed | The same at a stronger broadening. Still far below the floor: the exactness is a property of the model, the inseparability is not. |
| ok | `lim.scatter-worst` | 0.32 deg | 0.323432 | computed | The suite's worst pair with that channel added - unmoved, on a different pair. No class changes and no count changes. |
| ok | `lim.geometry-inversion` | +687 K | 687.435 | computed | Preheat implied by inverting the pads' depth excess over single tracks through the geometry channel. Not credible as a measurement: a pad differs from a single track by remelting adjacent tracks as well as by preheat, so this is an upper bound with a second mechanism folded in. |
| ok | `lim.preheat-response` | +2.23 % depth per 100 K | 2.23059 | computed | What the model's preheat channel buys, which is why the geometry unit is probably understated. *(note: not quoted in the paper; supports the sentence that the unit may be small)* |

## Section Table 1

| | id | paper | code | kind | what it means |
|---|---|---|---|---|---|
| ok | `tab.inst.power_gas` | 0.00 | 0.000110011 | computed | Per-segment angle between power and gas for the baseline suite. |
| ok | `tab.inst.layer_gas` | 0.32 | 0.323324 | computed | Per-segment angle between layer and gas for the baseline suite. |
| ok | `tab.inst.power_layer` | 0.32 | 0.323432 | computed | Per-segment angle between power and layer for the baseline suite. |
| ok | `tab.inst.power_speed` | 0.70 | 0.704525 | computed | Per-segment angle between power and speed for the baseline suite. |
| ok | `tab.inst.speed_gas` | 0.70 | 0.704632 | computed | Per-segment angle between speed and gas for the baseline suite. |
| ok | `tab.inst.speed_layer` | 1.03 | 1.02796 | computed | Per-segment angle between speed and layer for the baseline suite. |
| ok | `tab.inst.speed_geometry` | 3.62 | 3.61748 | computed | Per-segment angle between speed and geometry for the baseline suite. |
| ok | `tab.inst.power_geometry` | 4.31 | 4.31092 | computed | Per-segment angle between power and geometry for the baseline suite. |
| ok | `tab.inst.gas_geometry` | 4.31 | 4.31103 | computed | Per-segment angle between gas and geometry for the baseline suite. |
| ok | `tab.inst.layer_geometry` | 4.63 | 4.63038 | computed | Per-segment angle between layer and geometry for the baseline suite. |
| ok | `tab.split.power_gas` | 0.00 | 8.46744e-05 | computed | Per-segment angle between power and gas with the camera's two axes reported separately instead of as an area. |
| ok | `tab.split.layer_gas` | 64.53 | 64.5341 | computed | Per-segment angle between layer and gas with the camera's two axes reported separately instead of as an area. |
| ok | `tab.split.power_layer` | 64.53 | 64.5341 | computed | Per-segment angle between power and layer with the camera's two axes reported separately instead of as an area. |
| ok | `tab.split.power_speed` | 43.43 | 43.4257 | computed | Per-segment angle between power and speed with the camera's two axes reported separately instead of as an area. |
| ok | `tab.split.speed_gas` | 43.43 | 43.4257 | computed | Per-segment angle between speed and gas with the camera's two axes reported separately instead of as an area. |
| ok | `tab.split.speed_layer` | 72.04 | 72.0402 | computed | Per-segment angle between speed and layer with the camera's two axes reported separately instead of as an area. |
| ok | `tab.split.speed_geometry` | 43.28 | 43.2801 | computed | Per-segment angle between speed and geometry with the camera's two axes reported separately instead of as an area. |
| ok | `tab.split.power_geometry` | 3.08 | 3.07903 | computed | Per-segment angle between power and geometry with the camera's two axes reported separately instead of as an area. |
| ok | `tab.split.gas_geometry` | 3.08 | 3.07911 | computed | Per-segment angle between gas and geometry with the camera's two axes reported separately instead of as an area. |
| ok | `tab.split.layer_geometry` | 64.81 | 64.8061 | computed | Per-segment angle between layer and geometry with the camera's two axes reported separately instead of as an area. |
| ok | `tab.acc.power_gas` | 29.34 | 29.3403 | computed | Angle between power and gas accumulated over an 84-segment build. |
| ok | `tab.acc.layer_gas` | 44.48 | 44.4793 | computed | Angle between layer and gas accumulated over an 84-segment build. |
| ok | `tab.acc.power_layer` | 36.26 | 36.263 | computed | Angle between power and layer accumulated over an 84-segment build. |
| ok | `tab.acc.power_speed` | 24.90 | 24.9008 | computed | Angle between power and speed accumulated over an 84-segment build. |
| ok | `tab.acc.speed_gas` | 35.87 | 35.8686 | computed | Angle between speed and gas accumulated over an 84-segment build. |
| ok | `tab.acc.speed_layer` | 46.16 | 46.1593 | computed | Angle between speed and layer accumulated over an 84-segment build. |
| ok | `tab.acc.speed_geometry` | 31.95 | 31.949 | computed | Angle between speed and geometry accumulated over an 84-segment build. |
| ok | `tab.acc.power_geometry` | 25.42 | 25.4231 | computed | Angle between power and geometry accumulated over an 84-segment build. |
| ok | `tab.acc.gas_geometry` | 31.39 | 31.3867 | computed | Angle between gas and geometry accumulated over an 84-segment build. |
| ok | `tab.acc.layer_geometry` | 40.54 | 40.5367 | computed | Angle between layer and geometry accumulated over an 84-segment build. |
| ok | `tab.inst-count` | 0/10 | 0 | computed | Pairs clearing the floor per segment, baseline suite. |
| ok | `tab.split-count` | 7/10 | 7 | computed | Pairs clearing it per segment with the camera split. |
| ok | `tab.acc-count` | 10/10 | 10 | computed | Pairs clearing it over a build. |

## Compute groups

| group | seconds | cached |
|---|---|---|
| `added` | 2.1 | no |
| `calibration` | 31.1 | no |
| `configs` | 2.6 | no |
| `context` | 3.1 | no |
| `couplings` | 0.3 | no |
| `couplings_sweep` | 14.7 | no |
| `discussion` | 13.5 | no |
| `meltpool` | 2.1 | no |
| `noise` | 1.1 | no |
| `noise_sets` | 0.9 | no |
| `robustness` | 5.0 | no |
| `secants` | 87.1 | no |
| `sources` | 0.0 | no |
| `validation` | 0.3 | no |
| `ved` | 6.0 | no |

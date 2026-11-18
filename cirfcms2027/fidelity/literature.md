# Literature for the fidelity paper

Each entry gives the reference, what it says that bears on this paper, and how
it was checked. "Checked" means the bibliographic details were confirmed against
the publisher's page or two independent catalogue records during this session
(2026-11-18); it does not mean the full text was read unless that is said.
Entries marked **unverified** must be checked before they go into the paper.

Keys match `../certificate/paper/refs.bib` where the reference is already there.

---

## 1. Where the question sits

**National Academies of Sciences, Engineering, and Medicine (2024).**
*Foundational Research Gaps and Future Directions for Digital Twins.*
Washington, DC: The National Academies Press. Released December 2023, dated
2024. DOI 10.17226/26894 (DOI from memory, **check**).
Argues that verification, validation and uncertainty quantification of a digital
twin should be continual rather than one-off, and should be tied to the decision
the twin supports rather than to the model in the abstract. This is the
position this paper makes quantitative for one decision, fault diagnosis: the
accuracy a twin needs depends on what it is used for, and the two uses studied
here need different things. Checked: title, publisher, date.

**ASME V&V 40-2018.** *Assessing Credibility of Computational Modeling through
Verification and Validation: Application to Medical Devices.* American Society of
Mechanical Engineers, New York, 2018.
The standard's central idea is that the credibility a model must demonstrate is
set by its *context of use* and by the risk of the decision it informs, so one
model can be credible for one use and not for another. Our partition of the
parameters into prediction-only, diagnosis-only and shared gives a concrete
mechanism for exactly that: a model validated for prediction has demonstrated
nothing about the diagnosis-only parameters. Cite as the engineering-standards
counterpart of the National Academies report. Checked: title, year, framework
summary from secondary sources; the standard itself was not read.

**Kapteyn, M. G., Pretorius, J. V. R., Willcox, K. E. (2021).** A probabilistic
graphical model foundation for enabling predictive digital twins at scale.
*Nature Computational Science* 1(5), 337–347.
A representative of the mathematical digital-twin literature; frames the twin as
a model updated from data to support decisions. Useful in the introduction to
place the work; does not treat the fidelity needed for diagnosis. Checked:
title, authors, journal, volume, pages.

## 2. Twin experiments: what "truth" and "twin" mean

**Yu, L., Fennel, K., Wang, B., Laurent, A., Thompson, K. R., Shay, L. K. (2019).**
Evaluation of nonidentical versus identical twin approaches for observation
impact assessments: an ensemble-Kalman-filter-based ocean assimilation
application for the Gulf of Mexico. *Ocean Science* 15, 1801–1814.
(The discussion-paper version used "fraternal" in place of "nonidentical".)
In data assimilation an *identical twin* experiment generates synthetic
observations from the same model used for inference; a *nonidentical* or
*fraternal* twin uses a different model. Yu et al. find that the identical twin
overestimates the value of some observations and undervalues others. This is the
established name and the established warning for what the certificate paper did
(its truth and its inference model were the same up to linearisation), and it
motivates the present paper. Checked: published title, authors, pages, and the
title change from the preprint.

## 3. Calibration does not identify physical parameters

**Kennedy, M. C., O'Hagan, A. (2001).** Bayesian calibration of computer models.
*Journal of the Royal Statistical Society: Series B* 63(3), 425–464.
DOI 10.1111/1467-9868.00294.
Introduces the model-discrepancy term: calibrating a misspecified model without
one yields parameters that compensate for the misspecification. Our calibrated
conductivity and heat capacity sit on their bounds, which is the symptom.
Checked.

**Brynjarsdóttir, J., O'Hagan, A. (2014).** Learning about physical parameters:
the importance of model discrepancy. *Inverse Problems* 30(11), 114007.
DOI 10.1088/0266-5611/30/11/114007.
Shows that a calibration which ignores discrepancy gives biased and over-confident
parameter estimates even when its predictions within the data range are good.
This is the statement that good prediction does not imply right parameters; the
present paper adds that the wrong parameters matter for diagnosis even when they
do not matter for prediction. Checked: bibliographic details and abstract.

**Gutenkunst, R. N., Waterfall, J. J., Casey, F. P., Brown, K. S., Myers, C. R.,
Sethna, J. P. (2007).** Universally sloppy parameter sensitivities in systems
biology models. *PLoS Computational Biology* 3(10), e189.
DOI 10.1371/journal.pcbi.0030189.
"Sloppy" models: the data constrain a few parameter combinations tightly and
leave the rest loose, and the authors recommend judging models by their
predictions rather than their parameters. Our validation region is a textbook
case (the data accept absorptivity from 0.30 to 0.78 and heat capacity over
almost the whole bound box). The point of the present paper is that the
recommendation holds for the predictions the data were collected for and fails
for a different use of the same model. Checked.

**Beale, E. M. L. (1960)** and **Bates, D. M., Watts, D. G. (1988),** *Nonlinear
Regression Analysis and Its Applications*, Wiley, for the F-test confidence
region used in `twins.py`. **Unverified**: the region is standard, but which
source to cite for its use with the residual variance in place of a known
measurement variance should be checked in Bates and Watts, chapter 6.

## 4. Fault diagnosis under model uncertainty

**Chen, J., Patton, R. J. (1999).** *Robust Model-Based Fault Diagnosis for
Dynamic Systems.* Kluwer Academic, Boston. (Some catalogues give December 1998.)
The standard reference for residual generation that is insensitive to modelling
error, by decoupling residuals from disturbance directions. That literature
treats model error as a disturbance to be rejected at the design stage; the
present paper asks instead how large the error may be before a given test loses
its stated coverage. Checked: title, authors, publisher.

**Krysander2008** (in `refs.bib`). Structural analysis for fault isolability.
Already cited in both earlier papers; here for the fact that isolability is a
property of the model, so a model error can create or destroy it.

**Chow1970** (in `refs.bib`). Confidence sets from tests; the certificate is one.

**Angelopoulos2023** (in `refs.bib`). Conformal prediction; the distribution-free
alternative to the certificate, relevant because it is the obvious response to a
twin whose noise model is wrong.

## 5. Mathematical tools

**Imhof, J. P. (1961).** Computing the distribution of quadratic forms in normal
variables. *Biometrika* 48(3–4), 419–426. DOI 10.1093/biomet/48.3-4.419.
The inversion formula `theory.generalised_chi2_cdf` implements for
Proposition 4. Checked.

## 6. The process and the model

**Hon2021, Weaver2024, Trapp2017** (in `refs.bib`). The keyhole correlation
(correlations 0.93 to 0.96 reported by Hon et al.), the AM-Bench melt-pool
measurements, and the absorptivity measurements. As in the earlier papers.

---

## Still to look for

* A paper in additive manufacturing that validates a melt-pool model on geometry
  and then uses it for monitoring or diagnosis, as a concrete instance of the
  practice examined here. Not yet found; searching rather than citing a guess.
* Found: **Gevers, M. (2005).** Identification for control: from the early
  achievements to the revival of experiment design. *European Journal of
  Control* 11, 335–352. DOI 10.3166/ejc.11.335-352. The control community's
  version of the idea: the model with the smallest prediction error is not the
  model best for designing a controller, so identification should be shaped by
  the intended use. The closest precedent in another field for "fidelity for the
  task". Checked: title, journal, volume, pages, DOI.

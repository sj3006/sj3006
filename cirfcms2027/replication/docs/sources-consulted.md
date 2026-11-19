# Public sources consulted

Every web search and web fetch made while this work was carried out, as far as
the session record allows, with what each was for and the links it returned.
Nothing was downloaded into the repository from these sources: the only
outside numbers the code uses are the published measurements listed, with
article, table and module, in `measured-inputs.md`. Search results were used to
find and check bibliographic details; each reference that went into a paper is
listed with how it was checked in `../fidelity/literature.md` (fidelity paper),
`../certificate/paper/refs.bib` (certificate paper, header comment) and
`../07-literature-extraction.md` (conference paper's literature census).

## Coverage of this record

The table below is extracted mechanically from the session transcript that
is still on disk, which begins on 2026-11-15; the raw extraction is
`web-lookups-2026-11.json`. Work before that date was done in earlier sessions
whose transcripts are not available. Its searches are described, though not
listed link by link, in `../06-literature-landscape.md` (about twenty novelty
searches during planning), `../07-literature-extraction.md` (the nineteen
studies extracted for the outcome-versus-cause census) and `../09-data-wanted.md`
(what could not be reached: publisher sites, doi.org and nvlpubs.nist.gov were
refused by the session's network proxy, so full texts were not opened).

Two fetches in this record failed for the same reason, and are marked so.

## Lookups, 2026-11-15 to 2026-11-18

| # | date (UTC) | tool | query or address | purpose | outcome |
|---|---|---|---|---|---|
| 1 | 2026-11-15 20:01 | WebSearch | Angelopoulos Bates gentle introduction conformal prediction distribution-free uncertainty quantification | certificate paper: Angelopoulos2023 (conformal prediction) | 10 links returned |
| 2 | 2026-11-15 20:01 | WebSearch | Chow 1970 optimum character recognition reject option IEEE Transactions Information Theory | certificate paper: Chow1970 (reject option) | 10 links returned |
| 3 | 2026-11-15 20:01 | WebSearch | large language models overconfident calibration verbalized confidence hallucination benchmark 2024 | certificate paper, related work on language-model agents | 10 links returned |
| 4 | 2026-11-15 20:01 | WebSearch | large language model agents manufacturing process monitoring digital twin review 2024 2025 | certificate paper: Chen2025 (flagged, DOI not resolvable from the session) | 10 links returned |
| 5 | 2026-11-15 20:01 | WebFetch | https://doi.org/10.1016/j.rcim.2025.102982 | certificate paper: attempt to open Chen2025; failed | failed: host outside the session's allowed network |
| 6 | 2026-11-17 15:19 | WebSearch | Grasso Colosimo "Process defects and in situ monitoring methods in metal powder bed fusion" review Measurement Science and Technology 2017 | conference and certificate papers: Grasso2017 | 10 links returned |
| 7 | 2026-11-17 15:20 | WebFetch | https://re.public.polimi.it/handle/11311/1024010 | attempt to open Grasso2017 repository copy; failed | failed: host outside the session's allowed network |
| 8 | 2026-11-17 15:20 | WebSearch | "Grasso" "Colosimo" 2017 "Measurement Science and Technology" volume 28 044005 powder bed fusion review citation | conference and certificate papers: Grasso2017 citation details | 10 links returned |
| 9 | 2026-11-17 15:29 | WebSearch | Shevchik Wasmer acoustic emission in situ quality monitoring additive manufacturing spectral convolutional neural networks Additive Manufacturing 2018 | conference paper: introduction reference requested by the authors | 10 links returned |
| 10 | 2026-11-17 15:29 | WebSearch | Hooper "Melt pool temperature and cooling rates in laser powder bed fusion" Additive Manufacturing 2018 two-colour imaging pyrometry volume pages | conference paper: introduction reference requested by the authors | 10 links returned |
| 11 | 2026-11-17 15:29 | WebSearch | two-colour pyrometry LPBF porosity defect detection classification in-situ monitoring machine learning study | conference paper: introduction reference requested by the authors | 10 links returned |
| 12 | 2026-11-18 21:30 | WebSearch | Imhof 1961 "Computing the distribution of quadratic forms in normal variables" Biometrika volume pages | fidelity paper: Imhof1961 | 10 links returned |
| 13 | 2026-11-18 21:30 | WebSearch | National Academies 2023 "Foundational Research Gaps and Future Directions for Digital Twins" verification validation uncertainty quantification | fidelity paper: NASEM2024 | 10 links returned |
| 14 | 2026-11-18 21:30 | WebSearch | Chen Patton "Robust Model-Based Fault Diagnosis for Dynamic Systems" 1999 Kluwer book modelling uncertainty | fidelity paper: ChenPatton1999 | 10 links returned |
| 15 | 2026-11-18 21:30 | WebSearch | "identical twin experiment" data assimilation definition observing system simulation experiment model error fraternal twin | fidelity paper: twin-experiment terminology | 10 links returned |
| 16 | 2026-11-18 21:31 | WebSearch | Ocean Science 2019 volume 15 page 1801 "fraternal versus identical twin" authors title Gulf of Mexico | fidelity paper: Yu2019 | 10 links returned |
| 17 | 2026-11-18 21:31 | WebSearch | ASME V&V 40-2018 "Assessing Credibility of Computational Modeling through Verification and Validation" context of use model risk | fidelity paper: ASMEVV40 | 10 links returned |
| 18 | 2026-11-18 21:32 | WebSearch | Brynjarsdóttir O'Hagan 2014 "Learning about physical parameters: the importance of model discrepancy" Inverse Problems 30 114007 | fidelity paper: Brynjarsdottir2014 | 10 links returned |
| 19 | 2026-11-18 21:32 | WebSearch | Gutenkunst 2007 "Universally sloppy parameter sensitivities in systems biology models" PLoS Computational Biology 3(10) e189 | fidelity paper: Gutenkunst2007 | 10 links returned |
| 20 | 2026-11-18 21:32 | WebSearch | Kennedy O'Hagan 2001 "Bayesian calibration of computer models" Journal of the Royal Statistical Society Series B 63 425-464 | fidelity paper: Kennedy2001 | 10 links returned |
| 21 | 2026-11-18 21:32 | WebSearch | Kapteyn Pretorius Willcox 2021 "probabilistic graphical model foundation for enabling predictive digital twins at scale" Nature Computational Science | fidelity paper: Kapteyn2021 | 10 links returned |
| 22 | 2026-11-18 21:33 | WebSearch | Gevers identification for control survey "From the identification of models to the identification of control" OR "Identification for control: from the early achievements to the revival of experiment design" | fidelity paper: Gevers2005 | 10 links returned |

## Links returned by each search

**1. Angelopoulos Bates gentle introduction conformal prediction distribution-free uncertainty quantification**

- [A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification](https://aitopics.org/doc/arxivorg:537187EC)
- [Conformal Prediction: A Gentle Introduction](https://bohrium.dp.tech/paper/arxiv/1203.5422)
- [arxiv.org](https://arxiv.org/abs/2107.07511v4)
- [arxiv.org](https://arxiv.org/abs/2107.07511v6)
- [License: arXiv.org perpetual non-exclusive license](https://arxiv.org/html/2107.07511v6)
- [gentle intro](https://people.eecs.berkeley.edu/~angelopoulos/blog/posts/gentle-intro)
- [www.emergentmind.com](https://www.emergentmind.com/papers/2107.07511.md)
- [ar5iv.labs.arxiv.org](https://ar5iv.labs.arxiv.org/html/2107.07511)
- [A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification](https://tldr.takara.ai/p/2107.07511)
- [A Gentle Introduction to Conformal Prediction and Distribution-Free](https://fugumt.com/fugumt/paper_check/2107.07511v1_enmode)

**2. Chow 1970 optimum character recognition reject option IEEE Transactions Information Theory**

- [• DocumentCode](https://search.isc.ac/inventory/49/913313.htm)
- [DocumentCode :](https://manuscript.isc.ac/Inventory/49/913313.htm)
- [58ba4fd7 b463 41e2 a3f1 3fcae0784853](https://cs.reviewer.ly/app/publication/58ba4fd7-b463-41e2-a3f1-3fcae0784853)
- [On optimum recognition error and reject tradeoff](https://scilit.net/publications/658ce4ef3a82419c5e0f8499ced57d4f)
- [EP 0320663 A3 19911023 - METHOD AND APPARATUS FOR CHARACTER RECOGNITION SYSTEMS](https://data.epo.org/gpi/EP0320663A3)
- [1977 agrawala machinerecognitionofpatterns](https://gwern.net/docs/ai/1977-agrawala-machinerecognitionofpatterns.djvu)
- [DocumentCode :](https://manuscript.isc.ac/Inventory/49/1352898.htm)
- [An optimum character recognition system using decision functions](https://scilit.com/publications/e1726a2116ab2811242bee58d03ca7df)
- [Application of optimum error-reject functions (Corresp.)](https://www.bohrium.com/paper-details/application-of-optimum-error-reject-functions-corresp/812352847822716928-2561)
- [1957 chow](https://www.Gwern.net/doc/ai/highleyman/1957-chow.pdf)

**3. large language models overconfident calibration verbalized confidence hallucination benchmark 2024**

- [Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs](https://arxiv.org/pdf/2306.13063)
- [ConfidenceBench: Evaluating Confidence Calibration](https://www.alphaxiv.org/abs/2607.20526.md)
- [ConfidenceBench: Evaluating Confidence Calibration in Large Language Models](https://www.alphaxiv.org/abs/2607.20526)
- [2024.trustnlp 1.13](https://aclanthology.org/2024.trustnlp-1.13.pdf)
- [arxiv.org](https://arxiv.org/abs/2405.02917v1)
- [arxiv.org](https://arxiv.org/html/2306.13063v2)
- [alphaxiv.org](https://alphaxiv.org/overview/2412.14737v1)
- [api.emergentmind.com](https://api.emergentmind.com/papers/2405.02917)
- [Overconfidence is Key: Verbalized Uncertainty Evaluation in Large Language and Vision-Language Models](https://arxiv.org/html/2405.02917v1)
- [Overconfidence is Key: Verbalized Uncertainty Evaluation in Large Language and Vision-Language Models](https://ar5iv.labs.arxiv.org/html/2405.02917)

**4. large language model agents manufacturing process monitoring digital twin review 2024 2025**

- [(Literature Review) Leveraging LLM Agents and Digital Twins for Fault Handling in Process Plants](https://www.themoonlight.io/review/leveraging-llm-agents-and-digital-twins-for-fault-handling-in-process-plants)
- [publications.aston.ac.uk](https://publications.aston.ac.uk/id/eprint/47252)
- [integrating large language model and digital twins in the context](https://research.aston.ac.uk/en/publications/integrating-large-language-model-and-digital-twins-in-the-context/)
- [inc.kmutt.ac.th](https://inc.kmutt.ac.th/download/capstone_design_projects/2568/20.pdf)
- [aisel.aisnet.org](https://aisel.aisnet.org/acis2025/226)
- [s42524 026 5273 5](https://journal.hep.com.cn/fem/EN/PDF/10.1007/s42524-026-5273-5)
- [(Literature Review) Leveraging LLM Agents and Digital Twins for Fault Handling in Process Plants](https://www.themoonlight.io/en/review/leveraging-llm-agents-and-digital-twins-for-fault-handling-in-process-plants)
- [Leveraging Large Language Models for Enhanced Digital Twin Modeling:](https://arxiv.org/html/2503.02167v1)
- [July 31, 2025](https://falkor.com/blog/the-new-intelligence-layer-transforming-the-chemical-industry-agentic-ai-meets-digital-twins)
- [synapsesocial.com](https://synapsesocial.com/papers/W4415334576)

**6. Grasso Colosimo "Process defects and in situ monitoring methods in metal powder bed fusion" review Measurement Science and Technology 2017**

- [Grasso colosimo Review PBF revised 3](https://re.public.polimi.it/bitstream/11311/1024010/7/Grasso_colosimo_Review_PBF_revised_3.pdf)
- [In-situ measurement and monitoring methods for metal powder bed fusion: an updated review. (15th July 2021)](https://eld.bl.uk/catalog/100139286632_0x000001)
- [re.public.polimi.it](https://re.public.polimi.it/handle/11311/1024010)
- [re.public.polimi.it](https://re.public.polimi.it/handle/11311/1178140)
- [re.public.polimi.it](https://re.public.polimi.it/handle/11311/1149643)
- [re.public.polimi.it](https://re.public.polimi.it/handle/11311/1196614)
- [A%20review%20of%20the%20current%20state of the art%20on%20in%20situ%20monitoring%20in%20electron%20beam%20powder%20bed%20fusion](https://re.public.polimi.it/retrieve/7fe3de7d-8b0c-4f79-90d9-e2391dd464df/A%20review%20of%20the%20current%20state-of-the-art%20on%20in%20situ%20monitoring%20in%20electron%20beam%20powder%20bed%20fusion.pdf)
- [Process defects and in situ monitoring methods in metal powder bed fusion: a review](https://vufind-test.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c365t-5c434ee4a82f1572981219b00e9cae97692f7f8964403b9a7aa9a487b38dac593)
- [Process defects and in situ monitoring methods in metal powder bed fusion: a review](https://vufind-test.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c365t-5c434ee4a82f1572981219b00e9cae97692f7f8964403b9a7aa9a487b38dac593/Details)
- [Process defects and in situ monitoring methods in metal powder bed fusion: a review](https://vufind-test.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c365t-5c434ee4a82f1572981219b00e9cae97692f7f8964403b9a7aa9a487b38dac593/UserComments)

**8. "Grasso" "Colosimo" 2017 "Measurement Science and Technology" volume 28 044005 powder bed fusion review citation**

- [Process defects and in situ monitoring methods in metal powder bed fusion: a review](https://vufind-test.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c365t-5c434ee4a82f1572981219b00e9cae97692f7f8964403b9a7aa9a487b38dac593/Details)
- [Process defects and in situ monitoring methods in metal powder bed fusion: a review](https://vufind-test.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c365t-5c434ee4a82f1572981219b00e9cae97692f7f8964403b9a7aa9a487b38dac593)
- [Process defects and in situ monitoring methods in metal powder bed fusion: a review](https://vufind-test.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c365t-5c434ee4a82f1572981219b00e9cae97692f7f8964403b9a7aa9a487b38dac593/UserComments)
- [0In situ%20measurement%20and%20monitoring%20methods%20for%20metal%20powder%20bed%20fusion%20%E2%80%93%20an%20updated%20review](https://re.public.polimi.it/bitstream/11311/1178140/1/0In-situ%20measurement%20and%20monitoring%20methods%20for%20metal%20powder%20bed%20fusion%20%E2%80%93%20an%20updated%20review.pdf)
- [www.euspen.eu](https://www.euspen.eu/knowledge-base/ICE18362.pdf)
- [re.public.polimi.it](https://re.public.polimi.it/handle/11311/1178140)
- [grasso euspen january2017 openaccess](https://nottingham.ac.uk/research/groups/advanced-manufacturing-technology-research-group/documents/manufacturing-metrology-team/qcam-17/grasso-euspen-january2017-openaccess.pdf)
- [re.public.polimi.it](https://re.public.polimi.it/handle/11311/1167692)
- [Grasso colosimo Review PBF revised 3](https://re.public.polimi.it/bitstream/11311/1024010/7/Grasso_colosimo_Review_PBF_revised_3.pdf)
- [IMEKO TC10 2016 049](https://imeko.org/publications/tc10-2016/IMEKO-TC10-2016-049.pdf)

**9. Shevchik Wasmer acoustic emission in situ quality monitoring additive manufacturing spectral convolutional neural networks Additive Manufacturing 2018**

- [deep learning for in situ and real time quality monitoring vjrxwlwoy9](https://typeset.io/pdf/deep-learning-for-in-situ-and-real-time-quality-monitoring-vjrxwlwoy9.pdf)
- [Tough nuts, cracked in a smart way](https://innovations-report.com/materials-sciences/tough-nuts-cracked-in-a-smart-way)
- [Tough nuts, cracked in a smart way](https://innovations-report.com/?p=310770)
- [Artificial intelligence in quality monitoring](https://www.empa.ch/web/s604/am-quality-check)
- [2018 08 tough nuts smart](https://phys.org/news/2018-08-tough-nuts-smart.pdf)
- [Dissemin is shutting down on January 1st, 2025](https://dissem.in/p/103967901/acoustic-emission-for-in-situ-quality-monitoring-in-additive-manufacturing-using-spectral-convolutional-neural-networks)
- [idw – Informationsdienst Wissenschaft](https://idw-online.de/en/news701332)
- [Repository logo](https://infoscience.epfl.ch/entities/publication/582a5a50-69fc-4467-8991-9ed494dc2544?ln=en)
- [in situ quality monitoring in am using acoustic emission a cdk421i08s](https://typeset.io/pdf/in-situ-quality-monitoring-in-am-using-acoustic-emission-a-cdk421i08s.pdf)
- [s11665 018 3690 2](https://springerlink.bibliotecabuap.elogim.com/content/pdf/10.1007/s11665-018-3690-2.pdf)

**10. Hooper "Melt pool temperature and cooling rates in laser powder bed fusion" Additive Manufacturing 2018 two-colour imaging pyrometry volume pages**

- [Melt pool temperature and cooling rates in laser powder bed fusion](https://spiral.imperial.ac.uk/entities/publication/d7257fe5-cc02-4b26-afb8-fecbac8dcab5)
- [Melt pool temperature and cooling rates in laser powder bed fusion](https://www.scinapse.io/papers/2803999279)
- [peeref.com](https://peeref.com/works/75959017)
- [s40192 023 00291 w](https://link.springer.com/content/pdf/10.1007/s40192-023-00291-w.pdf)
- [peeref.com](https://peeref.com/works/38841088)
- [www.nist.gov](https://www.nist.gov/node/1639016)
- [cas.cz](https://katalog.lib.cas.cz/KNAV/EdsRecord/edb,142407978)
- [Back to Search Start Over](https://searchworks.jioinstitute.edu.in/articles/asx__125787778)
- [s40192 020 00170 8](https://springerlink.bibliotecabuap.elogim.com/content/pdf/10.1007/s40192-020-00170-8.pdf)
- [s40192 020 00169 1](https://springerlink.bibliotecabuap.elogim.com/content/pdf/10.1007/s40192-020-00169-1.pdf)

**11. two-colour pyrometry LPBF porosity defect detection classification in-situ monitoring machine learning study**

- [process agnostic multi metric nondestructive characterization of](https://researchwith.stevens.edu/en/publications/process-agnostic-multi-metric-nondestructive-characterization-of-/)
- [Predicting Porosity Formation in Laser Powder Bed Fusion using In-situ Data from a Two Wavelength Imaging Pyrometer](https://asm.confex.com/asm/imat2021/webprogram/Paper54289.html)
- [arxiv.org](https://arxiv.org/pdf/2404.16882v1.pdf)
- [www.arxiv.org](https://www.arxiv.org/pdf/2112.11212)
- [www.osti.gov](https://www.osti.gov/biblio/1977320)
- [Publications Details](https://www.sandia.gov/research/publications/details/linking-pyrometry-to-porosity-in-additively-manufactured-metals-2020-01-01/)
- [528924 Fulltext](https://research.chalmers.se/publication/528924/file/528924_Fulltext.pdf)
- [linking pyrometry to porosity in additively manufactured metals 2020 01 01](https://www.sandia.gov/ccr/publications/details/linking-pyrometry-to-porosity-in-additively-manufactured-metals-2020-01-01)
- [s10845 022 02039 3](https://link.springer.com/10.1007/s10845-022-02039-3)
- [## Introduction and Research Objective](https://chatpaper.com/de/paper/17361)

**12. Imhof 1961 "Computing the distribution of quadratic forms in normal variables" Biometrika volume pages**

- [access.archive-ouverte.unige.ch](https://access.archive-ouverte.unige.ch/access/metadata/4a7195a7-be6d-4605-8f1e-94ff4b638b8d/download)
- [Scientific article](https://archive-ouverte.unige.ch/unige:101766)
- [Computing the Distribution of Quadratic Forms in Normal Variables](https://katalog.lib.cas.cz/KNAV/EdsRecord/edsjsr,edsjsr.10.2307.2332763)
- [Computing the Distribution of Quadratic Forms in Normal Variables](https://www.bohrium.com/paper-details/computing-the-distribution-of-quadratic-forms-in-normal-variables/812100493718323200-861)
- [www.scilit.net](https://www.scilit.net/publications/db56388b9f8e889d43d8eb99a79858ff)
- [infoscience.epfl.ch](https://infoscience.epfl.ch/record/84834/files/860929.pdf?version=1)
- [support.nag.com](https://support.nag.com/numeric/fl/nagdoc_fl26/pdf/g01/g01jdf.pdf)
- [rdrr.io](https://rdrr.io/cran/CompQuadForm/man/imhof.html)
- [search.r-project.org](https://search.r-project.org/CRAN/packages/CompQuadForm/CompQuadForm.pdf)
- [mirror.linux.duke.edu](https://mirror.linux.duke.edu/pub/cran/web/packages/CompQuadForm/CompQuadForm.pdf)

**13. National Academies 2023 "Foundational Research Gaps and Future Directions for Digital Twins" verification validation uncertainty quantification**

- [Foundational Research Gaps and Future Directions for Digital Twins (2024)](https://www.nationalacademies.org/read/26894/chapter/10)
- [foundational research gaps and future directions for digital twins](https://www.nationalacademies.org/our-work/foundational-research-gaps-and-future-directions-for-digital-twins)
- [Foundational Research Gaps and Future Directions for Digital Twins (2024)](https://uwnxt.nationalacademies.org/read/26894/chapter/10)
- [9fba0a13 a36c 4c9d 9d2d 02ef81efa3c1](https://www.nationalacademies.org/cdn/materials/9fba0a13-a36c-4c9d-9d2d-02ef81efa3c1)
- [Foundational Research Gaps and Future Directions for Digital Twins (2024)](https://www.nationalacademies.org/read/26894/chapter/8)
- [unlocking the promise of digital twins](https://www.nationalacademies.org/news/unlocking-the-promise-of-digital-twins)
- [unlocking the promise of digital twins](https://www.nationalacademies.org/news/2024/06/unlocking-the-promise-of-digital-twins)
- [Foundational Research Gaps and Future Directions for Digital Twins (2024)](https://uwnxt.nationalacademies.org/read/26894/chapter/8)
- [Foundational Research Gaps and Future Directions for Digital Twins (2024)](https://uwnxt.nationalacademies.org/read/26894/chapter/12)
- [Report on Digital Twins](https://e3sm.org/?p=70480)

**14. Chen Patton "Robust Model-Based Fault Diagnosis for Dynamic Systems" 1999 Kluwer book modelling uncertainty**

- [www.schweitzer-online.de](https://www.schweitzer-online.de/en/buch/Chen/Robust-Model-Based-Fault-Diagnosis-for-Dynamic-Systems/9781461373445/A3811761/)
- [Zum Hauptinhalt springen](https://www.lehmanns.ch/shop/mathematik-informatik/827194-9780792384113-robust-model-based-fault-diagnosis-for-dynamic-systems)
- [zendy.io](https://zendy.io/title/10.1002/rnc.615)
- [Robust Model-Based Fault Diagnosis for Dynamic Systems](https://ebooks.mpdl.mpg.de/ebooks/Record/EB000625935)
- [www.schweitzer-online.de](https://www.schweitzer-online.de/en/buch/Chen/Robust-Model-Based-Fault-Diagnosis-for-Dynamic-Systems/9780792384113/A3811717/)
- [Robust model-based fault diagnosis for dynamic systems /](https://libcat.library.tamu.edu/Record/in00001494476/Description)
- [Robust Model-Based Fault Diagnosis for Dynamic Systems](https://betterread.com.au/book/robust-model-based-fault-diagnosis-for-dynamic-systems-book-9781461373445.do)
- [link.springer.com](https://link.springer.com/978-1-4613-7344-5)
- [Robust Model-Based Fault Diagnosis for Dynamic Systems /](https://libcat.library.tamu.edu/Record/in00003577017)
- [Robust Model-Based Fault Diagnosis for Dynamic Systems (electronic resource) /](https://sidalc.net/search/Record/KOHA-OAI-TEST:184148)

**15. "identical twin experiment" data assimilation definition observing system simulation experiment model error fraternal twin**

- [os 15 1801 2019](https://os.copernicus.org/articles/15/1801/2019/os-15-1801-2019.pdf)
- [Articles | Volume 15, issue 6](https://os.copernicus.org/articles/15/1801/2019/)
- [os 2019 85 AC1 supplement](https://os.copernicus.org/preprints/os-2019-85/os-2019-85-AC1-supplement.pdf)
- [os 2019 85 AR1](https://os.copernicus.org/preprints/os-2019-85/os-2019-85-AR1.pdf)
- [os 2019 85.pdf](https://os.copernicus.org/preprints/os-2019-85/os-2019-85.pdf)
- [os 2019 85 manuscript version3](https://os.copernicus.org/preprints/os-2019-85/os-2019-85-manuscript-version3.pdf)
- [www2.cesm.ucar.edu](https://www2.cesm.ucar.edu/events/wg-meetings/2014/presentations/amwg/raeder.pdf)
- [Ip14 Prive Nikki](https://cscamm.umd.edu/programs/das6/program/Posters/uploads/Ip14-Prive_Nikki.pdf)
- [2014 AMWG SEvFV](https://www.image.ucar.edu/pub/DART/2014/2014_AMWG_SEvFV.pdf)
- [evaluation of fraternal versus identical twin approaches for observation impact assessments an](https://www.aminer.cn/pub/5db926a347c8f766461b4b2d/evaluation-of-fraternal-versus-identical-twin-approaches-for-observation-impact-assessments-an)

**16. Ocean Science 2019 volume 15 page 1801 "fraternal versus identical twin" authors title Gulf of Mexico**

- [os 15 1801 2019](https://os.copernicus.org/articles/15/1801/2019/os-15-1801-2019.pdf)
- [Articles | Volume 15, issue 6](https://os.copernicus.org/articles/15/1801/2019/)
- [os 2019 85.pdf](https://os.copernicus.org/preprints/os-2019-85/os-2019-85.pdf)
- [Articles | Volume 15, issue 6](https://os.copernicus.org/articles/15/1801/2019/os-15-1801-2019-discussion.html)
- [evaluation of fraternal versus identical twin approaches for observation impact assessments an](https://www.aminer.cn/pub/5db926a347c8f766461b4b2d/evaluation-of-fraternal-versus-identical-twin-approaches-for-observation-impact-assessments-an)
- [Articles | Volume 15, issue 6](https://os.copernicus.org/articles/15/1801/2019/os-15-1801-2019-assets.html)
- [Articles | Volume 15, issue 6](https://os.copernicus.org/articles/15/1801/2019/os-15-1801-2019-relations.html)
- [Articles | Volume 15, issue 6](https://os.copernicus.org/articles/15/1801/2019/os-15-1801-2019-metrics.html)
- [Ocean Science (Dec 2019)](https://doaj.org/article/31560b8fdedd4ea8b37212d2dd44d543)
- [doaj.art 31560b8fdedd4ea8b37212d2dd44d543](https://libmast.utm.my/Record/doaj.art-31560b8fdedd4ea8b37212d2dd44d543)

**17. ASME V&V 40-2018 "Assessing Credibility of Computational Modeling through Verification and Validation" context of use model risk**

- [pmc.ncbi.nlm.nih.gov](https://pmc.ncbi.nlm.nih.gov/articles/PMC7883933)
- [www.hb.fh-muenster.de](https://www.hb.fh-muenster.de/opus4/solrsearch/index/search/searchtype/authorsearch/author/%22Quadrat%2C+Eric%22)
- [2 Pathmanathan ICCVAM CoP 2024 508](https://ntp.niehs.nih.gov/sites/default/files/2024-02/2_Pathmanathan_ICCVAM-CoP-2024_508.pdf)
- [compbiomed e seminar 31](https://hpc.ipb.ac.rs/events/compbiomed-e-seminar-31/compbiomed-e-seminar-31.pdf)
- [Bioengineering Blog: An Emerging Regulatory Framework for Medical Device Simulation](https://www.asme.org/topics-resources/content/bioengineering-blog-an-emerging-regulatory-framework-for-medical-device-simulation)
- [pmc.ncbi.nlm.nih.gov](https://pmc.ncbi.nlm.nih.gov/articles/PMC6445134/table/T2)
- [Bioengineering Blog: An Emerging Regulatory Framework for Medical Device Simulation](https://asme.org/Topics-Resources/Content/Bioengineering-Blog-An-Emerging-Regulatory-Framework-for-Medical-Device-Simulation)
- [New ASME V&V 40 Standard for Medical Devices Released](https://simutechgroup.com/asme-vv-40-standard-medical-devices/)
- [New ASME V&V 40 Standard for Medical Devices Released](https://simutechgroup.com/?p=3123)
- [Bioengineering Blog: An Emerging Regulatory Framework for Medical Device Simulation](https://contentstaging12.asme.org/Topics-Resources/Content/Bioengineering-Blog-An-Emerging-Regulatory-Framework-for-Medical-Device-Simulation)

**18. Brynjarsdóttir O'Hagan 2014 "Learning about physical parameters: the importance of model discrepancy" Inverse Problems 30 114007**

- [Jenny Brynjarsdottir and Anthony O’Hagan](https://tonyohagan.co.uk/academic/abs/simmach.html)
- [Post date: Oct 10, 2014 3:40:24 PM](https://sites.google.com/case.edu/jennybrynjarsdottir/news/publication-in-inverse-problems)
- [Published November 2014 | Version v1](https://inis.iaea.org/records/cbkr0-am688)
- [Learning about physical parameters: the importance of model discrepancy](https://vufind.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c397t-281072e83579cfc092c4713bd222cc7d2f87b3aed929ee5c36a74c7d89d8405e3)
- [arxiv.org](https://arxiv.org/pdf/2201.06463v2)
- [inverting imperfect model   warwick   february 2015](https://text.www2.warwick.ac.uk/fac/sci/maths/research/events/2014-15/nonsymposium/uccm/inverting_imperfect_model_-_warwick_-_february_2015.pdf)
- [Learning about physical parameters: the importance of model discrepancy](https://www.bohrium.com/paper-details/learning-about-physical-parameters-the-importance-of-model-discrepancy/814686399516114949-925)
- [Learning about physical parameters: the importance of model discrepancy](https://vufind-test.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c397t-281072e83579cfc092c4713bd222cc7d2f87b3aed929ee5c36a74c7d89d8405e3/UserComments)
- [4tu.nl](https://www.4tu.nl/ami/Agenda-Events/Past-events/slidestonyohagan.pdf)
- [anthony o hagan LeLQ6l](https://scite.ai/authors/anthony-o-hagan-LeLQ6l)

**19. Gutenkunst 2007 "Universally sloppy parameter sensitivities in systems biology models" PLoS Computational Biology 3(10) e189**

- [universally sloppy parameter sensitivities in systems biology mod](https://experts.arizona.edu/en/publications/universally-sloppy-parameter-sensitivities-in-systems-biology-mod/)
- [PLoS Computational Biology (Oct 2007)](https://doaj.org/article/7946c35be1c14192b260ae11c1c21d0f)
- [Quantitative Biology > Quantitative Methods](https://arxiv.org/abs/q-bio/0701039v3)
- [Quantitative Biology > Quantitative Methods](https://arxiv.org/abs/q-bio/0701039v1)
- [arxiv.org](https://arxiv.org/abs/q-bio/0701039)
- [sethna.lassp.cornell.edu](https://sethna.lassp.cornell.edu/pubPDF/SloppyEverywhere.pdf)
- [Universally sloppy parameter sensitivities in systems biology models](https://sethna.lassp.cornell.edu/node/781)
- [bibsonomy.org](https://www.bibsonomy.org/bibtex/2d7f948430df05147fd84e81ebe3ade97/peter.ralph)
- [uv.mx](https://ebusca.uv.mx/Record/pubmed-2000971/Details)
- [Sloppy systems biology: tight predictions with loose parameters](https://archive.aps.org/mar/2007/d35/13)

**20. Kennedy O'Hagan 2001 "Bayesian calibration of computer models" Journal of the Royal Statistical Society Series B 63 425-464**

- [Bayesian calibration of computer models](https://www.academia.edu/19082282/Bayesian_calibration_of_computer_models)
- [RePEc:bla:jorssb:v:63:y:2001:i:3:p:425 464](https://econpapers.repec.org/RePEc:bla:jorssb:v:63:y:2001:i:3:p:425-464)
- [University of Sheffield](https://tonyohagan.co.uk/academic/abs/calib.html)
- [IDEAS home Printed from https://ideas.repec.org/a/bla/jorssb/v63y2001i3p425-464.html](https://ideas.repec.org/a/bla/jorssb/v63y2001i3p425-464.html)
- [University of Sheffield](https://mail.tonyohagan.co.uk/academic/abs/calib.html)
- [1467 9868.00294](https://zendy.io/title/10.1111/1467-9868.00294)
- [kennedy ohagan bayesiancalibrationofcomputermodelswithdiscussion 2001](https://bibbase.org/network/publication/kennedy-ohagan-bayesiancalibrationofcomputermodelswithdiscussion-2001)
- [www.asc.ohio-state.edu](https://www.asc.ohio-state.edu/statistics/comp_exp/jour.club/kennedy01.pdf)
- [Bayesian calibration of computer models](https://academicnewsletter.sufe.edu.cn/info/442306)
- [bayesian calibration of computer models](https://www.neura.market/ai-and-ml-research-papers/bayesian-calibration-of-computer-models)

**21. Kapteyn Pretorius Willcox 2021 "probabilistic graphical model foundation for enabling predictive digital twins at scale" Nature Computational Science**

- [A probabilistic graphical model foundation for enabling predictive digital twins at scale](https://ersearch2.cvtisr.sk/vufind/SummonRecord/FETCH-LOGICAL-c468t-bc8466d44ebf2a81fb5f90a5733c27c44a8d1bb7200a90ee2b1cc24543b137033/Description)
- [A probabilistic graphical model foundation for enabling predictive digital twins at scale](https://ersearch2.cvtisr.sk/vufind/SummonRecord/FETCH-LOGICAL-c468t-bc8466d44ebf2a81fb5f90a5733c27c44a8d1bb7200a90ee2b1cc24543b137033)
- [aeroastro.mit.edu](https://aeroastro.mit.edu/?p=4615)
- [Advanced Technique for Developing Digital Twins Makes Tech Universally Applicable](https://ae.utexas.edu/?p=9180)
- [MORTECH Book of Abstracts](https://re.public.polimi.it/retrieve/d8326c53-a712-4f41-a081-2afb2274d1ca/MORTECH_Book_of_Abstracts.pdf)
- [5 michael kapteyns](https://www.bnl.gov/nysds21/files/talks/day3/5-michael-kapteyns.pdf)
- [enbis.org](https://conferences.enbis.org/event/35/contributions/451/contribution.pdf)
- [Advanced Technique for Developing Digital Twins Makes Tech Universally Applicable](https://news.utexas.edu/?p=138167)
- [arxiv.org](https://arxiv.org/abs/2012.05841v3)
- [Login / Signup](https://cs.reviewer.ly/app/publication/983c926f-2a02-4e83-9a76-6cba1a0ef9ca)

**22. Gevers identification for control survey "From the identification of models to the identification of control" OR "Identification for control: from the early achievements to the revival of experiment design"**

- [uclouvain.be](https://perso.uclouvain.be/michel.gevers/PublisMig/P78.pdf)
- [perso.uclouvain.be](https://perso.uclouvain.be/michel.gevers/PublisMig/C124.pdf)
- [uclouvain.be](https://perso.uclouvain.be/michel.gevers/PublisMig/C128.pdf)
- [system identification without lennart ljung what would have 4ehymyd15o](https://typeset.io/pdf/system-identification-without-lennart-ljung-what-would-have-4ehymyd15o.pdf)
- [Modelling Identification and Control](https://www.academia.edu/103502676/Modelling_Identification_and_Control)
- [Identification for Control: From the Early Achievements to the Revival of Experiment Design](https://researchr.org/publication/Gevers05/bibtex)
- [uclouvain.be](https://perso.uclouvain.be/michel.gevers/PublisMig/C110.pdf)
- [perso.uclouvain.be](https://perso.uclouvain.be/michel.gevers/PublisMig/jpcf.pdf)
- [Login / Signup](https://cs.reviewer.ly/app/publication/68b5c158-373e-46f7-964f-8604da0b55d0)
- [Login / Signup](https://cs.reviewer.ly/app/publication/94c31606-21df-461c-bc1f-f2fc043af7d3)


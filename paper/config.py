"""Every knob for the study, in one place.

Change values here, re-run ./paper/run_paper.sh, and every table regenerates.
Whatever this file says at the time of the run is what the paper should quote,
so keep it under version control and cite the values in the Methods section.
"""

# ---------------------------------------------------------------- data / model
SPLIT          = "random"   # "random" = row-level 80/20 (comparable to prior
                            # CMAPSS XAI work); "grouped" = engine-level, no
                            # engine on both sides. Stage 02 reports BOTH
                            # regardless; this only picks which model the
                            # explanation study runs on.
TEST_SIZE      = 0.20
SPLIT_SEED     = 42
MODEL_SEED     = 0          # GradientBoostingRegressor(random_state=...)

# ---------------------------------------------------------- explanation study
N_INSTANCES    = 8          # test instances explained, stratified across the
                            # RUL range (a single instance is not a result)
INSTANCE_SEED  = 20260905

N_PERTURB      = 5000       # LIME num_samples for one explanation
K_LIST         = (5, 8, 10) # report Jaccard at each k
K_DISPLAY      = 8          # k used for rank-occupancy tables

R              = 100        # independent repetitions per method per instance,
                            # used by BOTH the stability and the rank tables so
                            # every result in the paper rests on one sample size.
                            # 100 gives 4950 pairs per instance; the original
                            # notebook's 5 runs gave 10.
B_AGG          = 5          # WA-LIME aggregation depth
B_SWEEP        = (2, 3, 5, 10, 20)   # for the B-vs-stability curve

# Compute-matched control: plain LIME given B_AGG x N_PERTURB perturbations.
# Without this the reviewer cannot tell aggregation from extra sampling.
RUN_COMPUTE_MATCHED = True

# ------------------------------------------------------------------- outputs
OUT_DIR        = "paper_outputs"

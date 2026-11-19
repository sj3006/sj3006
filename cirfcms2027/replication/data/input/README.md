# Published measurements used by the code

No data was downloaded. The values below were transcribed from the cited
articles into the code as constants; the CSV files are exported from those
constants when the package is built, so the files and the code cannot differ.

| file | source | used for | held in |
|---|---|---|---|
| `weaver2024_table4_single_tracks.csv` | Weaver, J. S. et al. (2024), *Integrating Materials and Manufacturing Innovation* 13, 363-379, Table 4. doi:10.1007/s40192-024-00355-5 | calibration of the thermal model: seven single tracks on bare IN718, laser power, scan speed, D4-sigma spot diameter, mean melt-pool width and depth, expanded uncertainty (k = 2) | `code/src/calibrate.py`, `WEAVER_POINTS` |
| `weaver2024_table5_pads.csv` | the same article, Table 5 | external check of the gas-fault profile: melt-pool depth of a pad scanned along a 4.3 m/s argon cross-flow, anti-parallel and parallel tracks | `code/src/weaver_pads.py` |
| `measured-inputs.md` | all cited articles | every value taken from published work, with the article, table and module, and how each is used | |

Units in the CSV files: power in W, speed in m/s, lengths in micrometres.

The measurements remain subject to the terms of their source articles. A reader
checking this work should check these values against the articles first: the
verification scripts confirm that the papers and the code agree, but cannot
confirm that either agrees with the source.

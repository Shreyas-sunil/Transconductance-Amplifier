# GPDK090 / Spectre campaign (CONECCT 2027 paper)

Every number in `paper_conecct2027/` comes from the CSV files in `results/csv/`, produced by
`tia.py` on the Cadence VM (Spectre 12.1.0, GPDK090 v4.6 models `gpdk090_nmos1v` / `gpdk090_pmos1v`,
sections NN/SS/FF/SF/FS, mismatch statistics from section `stat_mis`). GPDK090 is a generic
teaching kit, not a foundry process. All runs are schematic-level with ideal R and C.

| Path | Contents |
|---|---|
| `tia.py` | Netlist generator, Spectre runner, PSF-ASCII reader and every analysis (python 2.6, no numpy) |
| `run.sh` | `sh run.sh all` on the VM; results go to `~/exchange/tia_results` |
| `results/` | Second (final) pass: `csv/` (95 files), `netlists/` (every Spectre netlist that was run), `logs/` |
| `results_pass1/` | First pass, kept for traceability (B1 not yet gain-matched, no v2/F2 local search) |
| `post/analyze.py` | Figures, `numbers_gpdk.tex` and tables for the paper |
| `post/eye.py` | Eye openings recomputed from the stored waveforms (see note below) |
| `virtuoso/build_pass2.il` | SKILL script that copies the v1 and regain schematics into v2 and B1 cells and sets the new parameters. Generated, not yet executed in Virtuoso |

## Circuits

| Name in files | Paper | What it is |
|---|---|---|
| `base2020` | 2020 TIA as drawn | M1 and M2b gates at VDD, 2.4 nH ideal spiral |
| `regain` | B1 | 2020 topology re-optimised on GPDK090 for maximum bandwidth at >= 53.8 dBohm |
| `regain_eqp` | B2 | as B1, but forced to draw >= 0.9 mA |
| `pf_v1` | F1 | proposed sizes, Mf gate tied to OUT, Mt and Ca removed |
| `pf_opt` | F2 | F1 re-optimised at the same gain and current |
| `v1` | Proposed v1 | the paper's design (Table I) |
| `v2` | Proposed v2 | v1 topology re-sized for bandwidth |

Designs found by the optimiser are in `results/csv/design_*.csv`.

## Analyses (task names in tia.py)

`regain`, `pf`, `v2` (differential evolution, then a (1+24) evolution strategy), `nominal` (DC operating
points, AC, noise, global and local loop gains with `stb`), `vtune` (tuning law and the impedance of the
gyrator network alone), `pvt` (5 sections x -40/35/125 C x 0.9/1.0/1.1 V, with a Vtune sweep inside),
`loads` (CL and CPD sweeps, feedback-network decomposition), `rc` (R +-15 %, C +-10 %), `mc` (200-run
mismatch Monte Carlo with a Vtune sweep inside), `dcc` (average photocurrent with/without the DC
cancellation loop, its loop gain, noise, and a 300 uA step), `eye` (PRBS-7 transients).

## Notes found while running

* The bandwidth is the first -3 dB crossing above 90 MHz. An earlier version searched only after the
  peak and missed dips; it was fixed before the reported runs.
* `eye.csv` written by `tia.py` assumed a non-inverting output. The proposed and follower TIAs invert,
  so `post/eye.py` rebuilds the waveforms from `eyewave_*.csv`, searches latency and polarity, and
  writes `eye_post.csv`, which the paper uses.
* Each `mc_*` run logs one SPECTRE FAIL: the first attempt includes `section=stat_mis`, which the
  model file already includes; the script then retries without it and that run is the one reported.
* `results/csv/nodes_*.csv` hold only the saved nodes (inp, outp, n).

## Reproduce

On the VM: `sh run.sh all` (about 10 minutes). Then here:

```
python3 post/eye.py results/csv
python3 post/analyze.py results/csv ../paper_conecct2027
cd ../paper_conecct2027 && pdflatex main && pdflatex main
```

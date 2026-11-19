# Transconductance-Amplifier

An inductorless, bandwidth-tunable current-mirror transimpedance amplifier (TIA) with active-inductor
feedback, designed and simulated at 1 V with the 90 nm Predictive Technology Model (BSIM4).

The starting point is the TIA of Alsheikhjader (Rafidain J. Sci. 29(1), 2020), which uses a 2.4 nH spiral
inductor from output back to input. This repository contains (1) a BSIM4 re-simulation of that circuit as
drawn, (2) a redesigned circuit in which the spiral is replaced by a voltage-tuned active inductor,
(3) a diagnosis of why the published response cannot be reproduced, (4) two re-optimised versions of the
baseline topology used as a fair reference, (5) a DC-cancellation loop that removes the input overload
limit, and (6) everything needed to reproduce the results and the paper.

**Status: schematic-level simulation only.** No layout, no foundry kit, no silicon. Corners and mismatch
coefficients are assumed values. See "Known limits" below before quoting any number.

## CONECCT 2027 revision (GPDK090, Spectre)

`paper_conecct2027/` is the revised, anonymised six-page paper; every number in it comes from the
GPDK090 / Spectre 12.1 campaign in `gpdk090_spectre/` (534 runs, schematic level). See
`paper_conecct2027/CHANGE_REPORT.md` and `REVIEWS.md`. GPDK090 is a generic kit, not a foundry
process; the PTM90 results below are kept separately and are not mixed with it.

## Headline results

Conditions: ngspice 42, PTM 90 nm BSIM4, 1 V, 35 °C, 50 fF photodiode, 30 fF load.

| | Reference (re-simulated) | Proposed |
|---|---|---|
| Transimpedance gain | 38.0 dBΩ | 53.9 dBΩ |
| Response | 11.8 dB peak at 18.9 GHz | 0.09 dB peaking |
| Bandwidth | 7.1 GHz (±1 dB flat) | 9.69 GHz (−3 dB) |
| Bandwidth tuning | none | 5.56 to 9.73 GHz with one voltage |
| Input noise at 5 GHz | 30.8 pA/√Hz | 15.4 pA/√Hz |
| Power | 1.32 mW | 0.97 mW |
| Feedback element | 2.4 nH spiral | 2 transistors + 30 fF |

| Robustness of the proposed circuit | |
|---|---|
| Worst peaking over 15 PVT conditions | 2.36 dB with Vtune fixed, 0.40 dB trimmed |
| Bandwidth over 15 PVT conditions | 8.03 to 11.40 GHz fixed, 7.94 to 10.67 GHz trimmed |
| Monte Carlo (200 runs), samples under 1 dB peaking | 91 % fixed, 100 % trimmed |

### Fair comparison (same 50/30 fF, ≤1 dB peaking, ≤1.2 mW)

| | Baseline re-optimised, max GBW | Baseline re-optimised, same gain | Proposed |
|---|---|---|---|
| Gain | 44.6 dBΩ | 54.0 dBΩ | 53.9 dBΩ |
| Bandwidth | 30.8 GHz | 3.6 GHz | 9.69 GHz |
| Power | 0.26 mW | 0.09 mW | 0.97 mW |
| Noise at 5 GHz | 17.1 pA/√Hz | 8.4 pA/√Hz | 15.4 pA/√Hz |
| Gain × bandwidth | 5.3 TΩHz | 1.8 TΩHz | 4.8 TΩHz |

At equal gain the proposed TIA has 2.7× the bandwidth; the baseline topology wins on power
and noise density. Compare against this table, not against the as-drawn baseline.

### Why the 2020 curve cannot be reproduced

With the stated 2.4 nH, no combination of PMOS gate biases, spiral loss and capacitances fits the published
curve better than 3.5 dB rms, and every case resonates. With the feedback inductance below about
30 pH and the mirror at about 137 µA per branch, the fit is 1.6 dB rms. The published
response is that of the circuit without effective inductive feedback (`scripts/baseline_diag.py`).

### DC-cancellation loop (`proposed_tia_dcc`)

| | Without loop | With loop |
|---|---|---|
| Average photocurrent with gain within 1 dB and bandwidth within 10 % | 10 µA | 500 µA |
| Bandwidth at 300 µA | collapsed | 9.64 GHz |
| Dark gain / bandwidth | 53.9 dBΩ / 9.69 GHz | 53.4 dBΩ / 9.86 GHz |
| Noise at 5 GHz (dark) | 15.4 pA/√Hz | 16.3 pA/√Hz |
| Power | 0.97 mW | 1.05 mW |
| Loop phase margin, low-frequency corner | n/a | ≥ 81°, 111 kHz to 1.4 MHz |


## Known limits

- **Input overload without the loop.** The feedback follower carries 99 µA; without the DC-cancellation
  loop, gain rises by 1.2 dB at 25 µA of average photocurrent and the feedback is lost near 100 µA.
- **DC-cancellation loop mismatch.** The held follower current varies by σ = 25 µA in Monte Carlo;
  21 of 100 samples need a Vtune trim to stay under 1 dB peaking. The reference current is ideal.
- **The baseline diagnosis** rests on digitised points and assumed capacitances. It shows which conditions
  fit the published curve, not what the original authors actually simulated.
- **No extra bandwidth at light load.** Plain follower feedback reaches 11.53 GHz against
  9.72 GHz for the tunable network. The inductive zero only helps at heavy load
  (1.32× at 250 fF).
- **Trimming cannot recover slow or hot corners.**
- PTM has no foundry corners; corners here are ±30 mV threshold and ±5 % mobility skews.
- **Novelty is narrow.** Tunable-bandwidth TIAs (measured in silicon) and active inductors in current-mirror TIAs already exist; see `docs/Literature_Review.md`.
- The Cadence (Spectre/Virtuoso) files have not been run yet. LTspice has been run on three of the circuits (below).

## LTspice check

LTspice 26.1.1, same PTM 90 nm card and conditions. Schematics, waveforms and logs are in `simulations/ltspice/`.

| Circuit | Gain at 100 MHz | Peak | f−3dB | ngspice |
|---|---|---|---|---|
| Original (as drawn) | 38.0 dBΩ | 50.0 dBΩ (12.0 dB peaking) | n/a (resonant) | 38.0 dBΩ, 11.8 dB peak |
| Proposed | 53.87 dBΩ | 53.96 dBΩ | 9.71 GHz | 53.9 dBΩ, 9.69 GHz |
| Baseline re-optimised, same gain | 53.95 dBΩ | 54.53 dBΩ | 3.63 GHz | 54.0 dBΩ, 3.6 GHz |

The two simulators agree to within 0.2 dB and 0.3 %.

## Repository layout

| Path | Contents |
|---|---|
| `netlists/ngspice/` | Five circuits, run with `ngspice -b <file>`: `baseline_tia` (as drawn), `baseline_reopt_gain`, `baseline_reopt_gbw`, `proposed_tia`, `proposed_tia_dcc` |
| `netlists/ltspice/` | `.net` netlists and `.asc` schematics of all five circuits, custom MOS symbols, model card |
| `simulations/ltspice/` | LTspice runs: `1_original_tia`, `5_original_vs_proposed`, `8_proposed_vs_reopt_baseline` (`.asc`, `.raw`, `.plt`, `.log`, measurement `.db`) |
| `netlists/cadence/` | Spectre netlists (`.scs`) of all five, SKILL script that builds all five Virtuoso schematics, OCEAN plot script |
| `models/ptm90.lib` | PTM 90 nm bulk BSIM4 card (models renamed `nmos90`, `pmos90`) |
| `scripts/` | `circuits.py` (single source of truth for all circuits), `run_all.py`, `make_figures.py`, emitters |
| `results/data/` | Raw simulation output (CSV, JSON) |
| `results/figures/` | Every figure, PNG and PDF |
| `paper/` | `main.tex`, `main.pdf`, `Paper_ActiveInductor_TIA.docx`, figures |
| `docs/` | `Design_Changes_Report.docx`, `Project_Presentation.pptx`, `Literature_Review.md`, and the scripts that build them |

## Reproduce

```bash
sudo apt-get install ngspice            # version 42 was used
pip install numpy scipy matplotlib
cd scripts
python3 run_all.py        # every simulation (about 30 minutes on 2 cores)
python3 baseline_diag.py screen fit fitlf lfscan   # why the 2020 curve cannot be reproduced
python3 baseline_diag.py opt; python3 baseline_diag.py optgain 53.87; python3 baseline_diag.py optnoise
python3 dcc_study.py      # DC-cancellation loop: sweep, noise, loop gain, step, eye, PVT, Monte Carlo
python3 summarize.py      # results/summary.json
python3 make_figures.py   # results/figures
python3 build_paper.py    # paper/numbers.tex and tables
python3 emit.py           # regenerate all netlists from circuits.py
cd ../paper && pdflatex main.tex && pdflatex main.tex
```

To change the design, edit `scripts/circuits.py` and rerun; every netlist, figure and number follows from it.

## Using the other simulators

- **LTspice:** open `netlists/ltspice/proposed_tia.asc` (schematic) or `proposed_tia.net` (netlist) and run.
  For the DC-cancellation version open `proposed_tia_dcc.asc`; the parameter `idc` is the average photocurrent.
  Keep `ptm90.lib` and the two `.asy` symbol files in the same folder. Nets in the schematic are joined by label.
- **Cadence Spectre:** `cd netlists/cadence && spectre proposed_tia.scs`, then `load("plot_results.ocn")` in OCEAN.
- **Cadence Virtuoso schematic:** create an empty library, then in the CIW `load("build_tia_schematics.il")`
  and `tiaBuildAll("YOUR_LIB")`. Add `ptm90.lib` under ADE > Setup > Model Libraries.

## Credits

- PTM 90 nm model card: Nanoscale Integration and Modeling (NIMO) group, Arizona State University
  (W. Zhao and Y. Cao, IEEE Trans. Electron Devices 53(11), 2006).
- Reference circuit: M. S. H. Alsheikhjader, Rafidain Journal of Science 29(1), 71-78, 2020.

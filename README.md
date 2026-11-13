# Transconductance-Amplifier

An inductorless, bandwidth-tunable current-mirror transimpedance amplifier (TIA) with active-inductor
feedback, designed and simulated at 1 V with the 90 nm Predictive Technology Model (BSIM4).

The starting point is the TIA of Alsheikhjader (Rafidain J. Sci. 29(1), 2020), which uses a 2.4 nH spiral
inductor from output back to input. This repository contains (1) a BSIM4 re-simulation of that circuit as
drawn, (2) a redesigned circuit in which the spiral is replaced by a voltage-tuned active inductor, and
(3) everything needed to reproduce the results and the paper.

**Status: schematic-level simulation only.** No layout, no foundry kit, no silicon. Corners and mismatch
coefficients are assumed values. See "Known limits" below before quoting any number.

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

The reference numbers are what the published schematic gives in BSIM4, not the numbers printed in the
2020 paper (43.92 dBΩ, flat 5 to 15 GHz). `docs/Design_Changes_Report.docx` explains the difference.

## Known limits

- **Input overload.** The feedback follower carries 99 µA; gain rises by 1.2 dB at 25 µA of
  average photocurrent and the feedback is lost near 100 µA. A DC-cancellation loop is needed and is not designed yet.
- **No extra bandwidth at light load.** Plain follower feedback reaches 11.53 GHz against
  9.72 GHz for the tunable network. The inductive zero only helps at heavy load
  (1.32× at 250 fF).
- **Trimming cannot recover slow or hot corners.**
- PTM has no foundry corners; corners here are ±30 mV threshold and ±5 % mobility skews.
- **Novelty is narrow.** Tunable-bandwidth TIAs (measured in silicon) and active inductors in current-mirror TIAs already exist; see `docs/Literature_Review.md`.
- LTspice and Cadence files were generated but not run (neither tool was available); only ngspice was run.

## Repository layout

| Path | Contents |
|---|---|
| `netlists/ngspice/` | `baseline_tia.cir`, `proposed_tia.cir`: run with `ngspice -b <file>` |
| `netlists/ltspice/` | `.net` netlists and `.asc` schematics of both circuits, custom MOS symbols, model card |
| `netlists/cadence/` | Spectre netlists (`.scs`), SKILL script that builds both Virtuoso schematics, OCEAN plot script |
| `models/ptm90.lib` | PTM 90 nm bulk BSIM4 card (models renamed `nmos90`, `pmos90`) |
| `scripts/` | `circuits.py` (single source of truth for both circuits), `run_all.py`, `make_figures.py`, emitters |
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
python3 summarize.py      # results/summary.json
python3 make_figures.py   # results/figures
python3 build_paper.py    # paper/numbers.tex and tables
python3 emit.py           # regenerate all netlists from circuits.py
cd ../paper && pdflatex main.tex && pdflatex main.tex
```

To change the design, edit `scripts/circuits.py` and rerun; every netlist, figure and number follows from it.

## Using the other simulators

- **LTspice:** open `netlists/ltspice/proposed_tia.asc` (schematic) or `proposed_tia.net` (netlist) and run.
  Keep `ptm90.lib` and the two `.asy` symbol files in the same folder. Nets in the schematic are joined by label.
- **Cadence Spectre:** `cd netlists/cadence && spectre proposed_tia.scs`, then `load("plot_results.ocn")` in OCEAN.
- **Cadence Virtuoso schematic:** create an empty library, then in the CIW `load("build_tia_schematics.il")`
  and `tiaBuildAll("YOUR_LIB")`. Add `ptm90.lib` under ADE > Setup > Model Libraries.

## Credits

- PTM 90 nm model card: Nanoscale Integration and Modeling (NIMO) group, Arizona State University
  (W. Zhao and Y. Cao, IEEE Trans. Electron Devices 53(11), 2006).
- Reference circuit: M. S. H. Alsheikhjader, Rafidain Journal of Science 29(1), 71-78, 2020.

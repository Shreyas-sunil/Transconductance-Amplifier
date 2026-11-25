# Project 3: 0.6 V bulk-driven class-AB two-stage OTA with a dynamic slew booster

**Status:** base paper reconstructed and re-simulated in PTM 90 nm (ngspice) at 0.6 V, one novelty variant simulated with
corners, temperature and Monte Carlo. Schematic level only. Cadence gpdk090 and LTspice netlists are generated but were not
run here.

## 1. Base paper

Ballo, Grasso, Pennisi, "A 0.6 V Bulk-Driven Class-AB Two-Stage OTA with Non-Tailed Differential Pair," *JLPEA* 13(2):24,
2023, doi:10.3390/jlpea13020024 (open access). Full list in `papers/PAPERS.md`.

Why this one: recent, open access, ultra-low voltage, and it has a clear, documented weakness. Its positive slew rate is
0.17 V/µs against −6.61 V/µs negative, a 39× asymmetry. A paper that fixes a weakness the base paper itself reports is an
easy story for reviewers.

**Caveat on the reconstruction.** Sizes come from the paper's text and table; the transistor-level figure was not readable
from the cloud. Download the PDF and check the schematic before writing anything.

### The circuits (VDD = 0.6 V, IBias = 180 nA, CL = 150 pF, L = 180 nm)

- **C1 Base reconstruction.** PMOS bulk-driven non-tailed pair M1/M2 (inputs on the bulks, gates at vb1), tail-less bias
  through MB1 whose bulk follows the input common mode (300 kΩ/300 kΩ divider). Diode loads M3/M5 with cross-coupled
  M7/M8 (positive feedback), current gain β = 15 into M4/M6, PMOS mirror M9/M10, quasi-floating-gate (QFG) class-AB
  output M11/M12 with RBATT = 1 MΩ and CBATT = 800 fF. Miller compensation Cc = 500 fF with Rc = 100 kΩ.
- **C2/C3 Proposed: dynamic QFG pull-down.** One extra small NMOS Mpd (gate at the first-stage node n3, source at the QFG
  node x, drain at the output-device gate g12). During a positive step it pulls g12 down directly instead of waiting for
  CBATT to couple the swing, so the PMOS output device turns on harder. At rest it is off. C2 uses W = 0.3 µm, C3 uses
  W = 0.5 µm (L = 0.18 µm).

## 2. Re-simulation of the base paper (PTM 90 nm, 27 °C)

| | Paper (180 nm, measured/post-layout) | This work, PTM 90 nm |
|---|---|---|
| Power | 3.29 µW | 4.91 µW |
| DC gain | 64.8 dB | 69.6 dB |
| GBW | 357 kHz | 399 kHz |
| Phase margin | 67.6° | 74.1° |
| SR+ / SR− (0.4 V step) | +0.17 / −6.61 V/µs | +0.046 / −5.94 V/µs |
| Settling time +/− | | 13.1 / 1.02 µs |

Small-signal numbers match well. The slew asymmetry is reproduced (and is worse here). Diagnosis from the simulation:
SR+ scales with 1/CL and is limited by how far CBATT can push the QFG node x (about 0.18 V). Even with ideal coupling the
architecture gives only 0.175 V/µs. That is the opening for a paper.

**A second finding the paper does not show:** the base circuit latches at 125 °C in every corner (DC gain collapses to
about −90 dB, the cross-coupled pair wins), and 1 of 30 Monte Carlo runs latches at 27 °C. The paper only checked −10, 27
and 85 °C.

## 3. Proposed variant: results (27 °C)

| | C1 Base | C2 Proposed, W = 0.3 µm | **C3 Proposed, W = 0.5 µm** |
|---|---|---|---|
| Power | 4.91 µW | 5.44 µW | 5.72 µW |
| DC gain | 69.6 dB | ≈ 70 dB | 70.7 dB |
| Phase margin | 74.1° | ≈ 78° | 80.5° |
| SR+ | 0.046 V/µs | 0.188 V/µs | **0.569 V/µs (12×)** |
| SR− | −5.94 V/µs | | −14.7 V/µs |
| Large-signal behaviour | clean | limit cycle | **limit cycle, ≈ 0.3 V p-p at the low output level** |

### Robustness (5 corners × −40/27/125 °C; 30 Monte Carlo runs, Avt = 3.5 mV·µm)

| | C1 Base | C2 / C3 Proposed |
|---|---|---|
| Latch at 125 °C | all 5 corners | inherited |
| Monte Carlo latch | 1 of 30 | |
| Limit cycle after a large step | none | 8–9 of 15 PVT runs, 28–29 of 30 Monte Carlo runs |

**Fair reading:** the slew-rate fix works (12× SR+ for 16 % more power), but the extra path creates a large-signal loop
that oscillates after a step in most runs. **As it stands the proposed circuit is not usable.** It needs either a
clamped/current-limited Mpd, a hysteretic turn-off, or a separate small compensation for the booster path. On top of that,
the base cross-coupled ratio α has to be backed off (or made temperature tracking) so the first stage does not latch hot.

## 4. Novelty and prior-art check

Bulk-driven class-AB OTAs at 0.3–0.6 V are an active area (Ballo/Grasso/Pennisi 2022–2023, Centurelli 2020–2022, Barile
2023, Beloso-Legarra TCAS-I 2023). Adaptive biasing and nonlinear current mirrors are the usual slew fixes. What is still
open:
- A **dynamic QFG booster** that fixes the positive-slew limit of the QFG output stage without static current, with a
  stability analysis of the extra large-signal loop. Not found in the papers checked.
- A **temperature-robust non-tailed bulk-driven pair** (α that tracks temperature so the first stage never latches). The
  base paper's own data stop at 85 °C, so a 125 °C-safe version is a real contribution.

## 5. Publishability

Highest upside, highest risk. If the limit cycle is fixed and the 125 °C latch is removed, "symmetric slew at 0.6 V with
< 20 % power cost, robust to 125 °C" against a 2023 base paper is a solid Q2/Q3 story (*AEÜ*, *Integration*,
*Microelectronics Journal*, *IJCTA*, *JLPEA*). Today it is not publishable: the main claimed improvement comes with an
oscillation. Expect two to four weeks of design work before it is clear whether it can be saved.

## 6. Files

| Path | What it is |
|---|---|
| `netlists/ngspice/` | C1–C3 with testbenches `_C_ac` (open loop) and `_C_tr` (unity-gain follower step), plus `ptm90.lib`. Run `ngspice -b <file>`. |
| `netlists/ltspice/` | Same for LTspice. Change `level = 54` to `level = 14` in `ptm90.lib` if LTspice rejects it. Bulk-driven devices need a model that handles forward body bias. |
| `netlists/cadence_gpdk090/` | Spectre netlists (`nmos1v`/`pmos1v`, `section=NN`). PTM sizes copied over: retune bias and α in GPDK090 before quoting numbers. |
| `scripts/` | `projC.py` (circuit and measurements), `runC.py` (corners and Monte Carlo), shared helpers (`sim.py`, `corners.py`, `sweep.py`, `summ.py`, `emit.py`, `tbs.py`, `plots.py`). |
| `results/plots/` | `C_open_loop_ac.png`, `C_follower_transient.png`. |
| `results/data/` | AC and transient CSVs, `pvt_mc_results.json`, `pvt_mc_table.csv` (`osc_hi`/`osc_lo` are the peak-to-peak ripple after settling, used to flag the limit cycle). |
| `papers/PAPERS.md` | Base and supporting papers with DOIs and open-access links. |

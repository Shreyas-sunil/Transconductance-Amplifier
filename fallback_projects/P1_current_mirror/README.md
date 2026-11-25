# Project 1: Dynamically matched, low-voltage FVF current mirror with sub-0.1 Ω input resistance

**Status (v2, 25 Nov 2026):** base paper reconstructed in PTM 90 nm (ngspice) at 1 V. The proposed mirror beats the
reconstruction on every static metric, and cuts the random (mismatch) gain error from 6.2 % to 0.23 % (σ) with dynamic
element matching (DEM). Checked over 5 corners × −40/27/125 °C and 40 Monte Carlo runs. Schematic level only; LTspice and
Cadence gpdk090 netlists are generated but were not run here.

## 1. Base paper

Ramírez-Angulo, Paul, Gangineni, Hinojo-Montero, Huerta-Chua, "Class AB Voltage Follower and Low-Voltage Current Mirror
with Very High Figures of Merit Based on the Flipped Voltage Follower," *JLPEA* 13(2):28, 2023, doi:10.3390/jlpea13020028
(open access). Reported (180 nm, post-layout): Rin 0.212 Ω, Rout 112 GΩ, error < 0.01 %, Vin 0.15 V, compliance 0.2 V,
BW 144 MHz. Full list in `papers/PAPERS.md`.

**Caveat:** the paper's transistor figures were not readable from the cloud, so the base circuit (A3) is rebuilt from its
text and equations (FVF mirror plus a common-source gain booster on each cascode gate). Check it against Fig. 4 of the
PDF before writing anything.

## 2. The weakness the proposal attacks

The base paper's "< 0.01 % error" is a **nominal** number. With realistic random mismatch (Avt = 3.5 mV·µm, mirror devices
10/0.36 µm) the mirror has a **6.2 % σ gain error** (Monte Carlo, 40 runs). A current mirror is an accuracy circuit, so
this is the number that matters, and the base paper does not report it. Fixing it by area alone would need roughly
(6.2 / 0.23)² ≈ 700× larger mirror devices.

## 3. The proposed mirror (A6)

Two changes on top of the FVF core, with no extra bias current:

1. **Dynamic element matching of the mirror pair.** The two mirror devices (MA, MB) share gate and source, so only their
   drains need swapping. Four small NMOS switches (4/0.1 µm), placed under the cascodes, swap which device is the input
   and which is the output every half clock period (500 kHz). The averaged output is then I·(1 + δ²/2) instead of
   I·(1 + δ): the first-order mismatch term cancels. The switches sit at low-impedance nodes inside the cascodes, so they
   barely touch Rin or Rout.
2. **Enhanced FVF core (A5).** Cascoded common-source boosters (one extra transistor each, in series with the existing
   booster bias, Vcb = 0.45 V), a wider booster device (8 µm) and narrower cascodes (10 µm). This lowers Rin and the input
   voltage, and raises Rout and bandwidth.

## 4. Results (PTM 90 nm, 1 V, Ib = 2 µA, Iin = 10 µA, 27 °C)

| | Paper (180 nm) | A3 Base reconstruction | **A6 Proposed (DEM)** |
|---|---|---|---|
| Input resistance | 0.212 Ω | 0.54 Ω | **0.065 Ω** |
| Systematic gain error | < 0.01 % | −0.007 % | −0.0035 % static, **+0.0002 % chopped** |
| **Random gain error σ (Monte Carlo, 40 runs)** | not reported | 6.2 % | **0.23 %** (mean +0.12 %, worst 1.0 %) |
| Random error σ at Iin = 2 µA | | | 0.31 % (11 % without DEM) |
| Input voltage | 0.15 V | 0.231 V | **0.175 V** |
| Output compliance (1 %) | 0.2 V | 0.215 V | **0.165 V** |
| Output resistance at 0.5 V | 112 GΩ | 7.0 GΩ | **19 GΩ** |
| Output resistance, gate tunnelling off | | 38 GΩ | **812 GΩ** |
| −3 dB bandwidth | 144 MHz | 340 MHz (299 MHz with switches) | **409 MHz** |
| Step 1→20 µA overshoot | | 46.5 % | **6.6 %** |
| Static power | | 4.4 µW | 4.4 µW (+ clock, about 20 nW) |

**Over PVT** (5 corners × 3 temperatures): chopped error stays within −0.008 … +0.002 %, Rin 0.049–0.095 Ω (base
0.45–0.67 Ω). The worst corner (fast, 125 °C) still gives 2.5 GΩ and −0.016 % static error.

**Over the input range** (1–20 µA, nominal) the chopped error stays within ±0.003 %.

**Clock frequency:** charge injection keeps the error under 0.011 % up to 2 MHz; at 5 MHz it reaches −0.09 %. 500 kHz is
the chosen point.

**On Rout vs the paper's 112 GΩ:** PTM 90 nm includes gate tunnelling, which leaks current from the output cascode gate
into the output and caps Rout near 20–35 GΩ. With tunnelling switched off (`ptm90_nogl.lib`, closer to the thick oxide of
180 nm) the proposed mirror reaches 812 GΩ. That makes Rout a technology limit, not a topology one. Say so in the paper,
and report both numbers.

### Costs and limits to state in the paper
- **Output ripple.** Each clock edge makes a short glitch (about 7 ns) on the output. With mismatch, the output also has a
  square-wave part at the clock frequency of ±δ·I. The averaged current is accurate, so the load must average (a bias
  line with a capacitor, a DAC, an integrator). The paper should show the glitch energy and ripple spectrum.
- The DEM residual is second order (δ²/2), so it is always slightly positive. Its mean (0.12 %) could be removed by a
  four-phase scheme that also swaps the Ib sources. That is a natural follow-up.
- Rout drops to 2–3 GΩ near the ends of the output range (0.3 V and 0.8 V), again from gate tunnelling. The base drops to
  0.4–0.9 GΩ there.
- The Ib sources are ideal in both circuits, as in the base paper's measurement. In silicon they are PMOS mirrors, and
  their mismatch should be swapped too (four more switches).

## 5. Ablation (what each change buys, nominal)

| | Rin | Rout (0.5 V) | Vin | Compliance | Random error σ |
|---|---|---|---|---|---|
| A3 base reconstruction | 0.54 Ω | 7.0 GΩ | 0.231 V | 0.215 V | 6.2 % |
| A3 + DEM | 0.54 Ω | 7.0 GΩ | 0.231 V | 0.215 V | 0.21 % |
| A5 enhanced core, no DEM | 0.065 Ω | 19 GΩ | 0.175 V | 0.165 V | 5.4 % |
| **A6 = A5 + DEM** | **0.065 Ω** | **19 GΩ** | **0.175 V** | **0.165 V** | **0.23 %** |

DEM gives the accuracy. The cascoded booster core gives the Rin, Vin, compliance and bandwidth gains.

## 6. Novelty and prior-art check

Dynamic element matching itself is old (Van de Plassche, 1976, for DACs), and the FVF mirrors (level-shifted 2016,
gain-boosted 2019, bulk-driven QFG 2020, this 2023 base) are all published. **None of the FVF high-accuracy mirror papers
found reports Monte Carlo accuracy or uses DEM.** The pitch: "the first sub-0.1 Ω FVF mirror whose accuracy holds under
mismatch". Before writing, search IEEE Xplore for "dynamic element matching" with "flipped voltage follower", and for
"chopped current mirror", to confirm.

## 7. Publishability

**Moderate to good** now. There is one clear headline (random error 6.2 % → 0.23 % at the same area and power), a strong
supporting set (3× lower Rin than the paper, lower Vin and compliance, 2.8× the bandwidth) and an honest Rout discussion.
For a Q2 journal (*AEÜ*, *Integration*, *Microelectronics Journal*, *IJCTA*) it needs layout and post-layout in gpdk090, a
ripple/glitch spectrum, and ideally the four-phase or Ib-swapped version. *JLPEA* and *Electronics* (MDPI), where the base
paper appeared, are realistic once the gpdk090 check is done.

## 8. Files

| Path | What it is |
|---|---|
| `netlists/ngspice/` | A1–A4 (v1) plus **A5** (enhanced core), **A6** (DEM mirror: `_A_dc` held in phase 1, `_A_chop` chopped transient) and the base with DEM. `ptm90.lib` included. Run `ngspice -b <file>`. |
| `netlists/ltspice/` | Same for LTspice. Change `level = 54` to `level = 14` in `ptm90.lib` if LTspice rejects it. |
| `netlists/cadence_gpdk090/` | Spectre netlists (`nmos1v`/`pmos1v`, `section=NN`). PTM sizes copied over: retune Vcn, Vcb and booster sizes in GPDK090. |
| `scripts/` | v2: `projA2.py` (base and proposed cores, DEM, all measurements), `runA3.py` (corners, Monte Carlo, Iin and clock sweeps), `plots2.py`, `ptm90_nogl.lib` (gate tunnelling off). v1 scripts are kept. |
| `results/plots/A_dem_mirror.png` | Monte Carlo histograms (static vs DEM), chopped output waveform, error vs Iin, error vs clock frequency. |
| `results/plots/A_mirror_characteristics.png` | v1 plot (A1–A4). |
| `results/data/` | `pvt_mc_results_v2_dem.json` and `pvt_mc_table_v2_dem.csv` (v2), plus the v1 CSVs and JSON. |
| `papers/PAPERS.md` | Base and supporting papers with DOIs and open-access links. |
| `COMPARISON.md` | The three projects side by side. |

The earlier single-booster variant (A4, v1) was a trade-off and is kept only for reference.

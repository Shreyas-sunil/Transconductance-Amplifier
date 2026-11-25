# Project 1: Low-voltage high-accuracy FVF current mirror

**Status:** base paper reconstructed and re-simulated in PTM 90 nm (ngspice) at 1 V, one novelty variant simulated with
corners, temperature and Monte Carlo. Schematic level only. Cadence gpdk090 and LTspice netlists are generated but were not
run here.

## 1. Base paper

Ramírez-Angulo, Paul, Gangineni, Hinojo-Montero, Huerta-Chua, "Class AB Voltage Follower and Low-Voltage Current Mirror
with Very High Figures of Merit Based on the Flipped Voltage Follower," *JLPEA* 13(2):28, 2023, doi:10.3390/jlpea13020028
(open access). Full list in `papers/PAPERS.md`.

Why this one: recent, open access, 1 V supply like your TIA work, and it reports record numbers (Rin 0.212 Ω,
Rout 112 GΩ, error < 0.01 %) that a fallback paper can be compared against.

**Caveat on the reconstruction.** The paper's transistor-level figures are images and its size tables were not readable
from the cloud. I rebuilt the mirror from its text and equations: FVF cascode mirror plus a gain-boosting amplifier on each
cascode. The paper's boosters are folded-cascode amplifiers referenced to a level-shifted node (Vx = 0.15 V); mine are
single common-source boosters (Vx ≈ 0.23 V). Download the PDF and check Fig. 4 before writing anything.

### The circuits (VDD = 1 V, Ib = 2 µA, mirror devices 10/0.36 µm, cascodes 40/0.36 µm)

- **A1 Conventional wide-swing cascode mirror.** Reference.
- **A2 Plain FVF mirror.** Iin enters the source of the input cascode M1C, which closes an FVF loop; Ib is removed at the output.
- **A3 Base reconstruction ("HP" mirror).** A2 plus a CS booster on each cascode gate (bias Ib/10, 0.3 pF compensation each).
- **A4 Proposed: one differential booster.** The input FVF is left alone (it already gives a low input impedance). A single
  PMOS-input differential booster compares the drain of the output mirror device with the drain of the input device and
  drives the output cascode gate, so both mirror devices see the same VDS. No level shifter, one booster instead of two.

## 2. Re-simulation (PTM 90 nm, 27 °C, Iin = 10 µA unless noted)

| | Paper (180 nm, post-layout) | A1 Cascode | A2 Plain FVF | A3 Base reconstruction | **A4 Proposed** |
|---|---|---|---|---|---|
| Input resistance (1 kHz) | 0.212 Ω | 5.49 kΩ | 24.9 Ω | **0.54 Ω** | 24.9 Ω |
| Gain error at 10 µA | < 0.01 % | +0.145 % | −2.18 % | **−0.007 %** | −0.090 % |
| Worst error, 1–20 µA | | 0.33 % | 4.43 % | 0.009 % | 0.13 % |
| Input voltage at 20 µA | 0.15 V | 0.387 V | 0.176 V | 0.231 V | **0.176 V** |
| Output resistance | 112 GΩ | 12 MΩ | 48 MΩ | **7.0 GΩ** | 2.2 GΩ |
| Output compliance (1 %) | 0.2 V | 0.14 V | 0.135 V | 0.215 V | **0.145 V** |
| −3 dB bandwidth | 144 MHz | 635 MHz | 348 MHz | 340 MHz | 351 MHz |
| Static power (Iin = 0) | +25 % vs conventional | 0 | 4.0 µW | 4.4 µW | 4.2 µW |

The reconstruction reproduces the base paper's character: sub-ohm input resistance, 0.01 % systematic accuracy, GΩ output
resistance and a constant input voltage. Rout is lower than 112 GΩ because my boosters have one gain stage, not two.

**The proposed A4 is a trade-off, not a win:** it saves 55 mV of input headroom and 70 mV of output compliance with one
booster fewer, but input resistance is 46× higher, output resistance 3× lower and accuracy 10× worse than A3.

### Robustness (5 corners × −40/27/125 °C; 40 Monte Carlo runs, Avt = 3.5 mV·µm)

| | A1 | A2 | A3 | A4 |
|---|---|---|---|---|
| Error at 10 µA, PVT range | 0.05 – 0.34 % | −4.5 – −1.3 % | −0.018 – −0.005 % | −0.31 – −0.05 % |
| Error at 10 µA, Monte Carlo σ | 4.8 % | 6.2 % | 6.2 % | 7.3 % |
| Rin, PVT range | 4.1 – 11.7 kΩ | 12 – 602 Ω | 0.45 – 0.67 Ω | 12 – 602 Ω |

Two findings matter for any paper here:
1. **Random mismatch dominates accuracy.** With these device areas, every topology has a 5–7 % σ gain error. The base
   paper's "0.01 %" is a systematic (nominal) number. A fair paper must report both, and size the mirror pair for the
   accuracy it claims.
2. The plain FVF input (A2, A4) loses its loop at the fast/125 °C corner (Rin rises to 602 Ω). The bias needs to track.

## 3. Novelty and prior-art check

Level-shifted FVF mirrors (2016), gain-boosted FVF mirrors (2019), bulk-driven QFG FVF mirrors (2020), the base paper's
two-booster version (2023) and a class AB FVF mirror/precision rectifier from the same group (2023) are all published.
The base paper's own future work (class AB version, double-cascoded auxiliaries) is the obvious next step, so expect
competition there.

Ideas that are still open and that the reconstruction can support:
- **Mismatch-aware high-accuracy mirror:** a chopped or dynamically matched FVF mirror that attacks the 5–7 % random error,
  which none of these papers address. This is the strongest angle.
- **Class AB bidirectional version with boosting**, if the 2023 precision-rectifier paper does not already cover it
  (read it first).

## 4. Publishability

Low as it stands. The A4 variant does not dominate the base, and a pure current-mirror paper needs one clear figure of
merit win. Worth pursuing only with the mismatch angle above, plus layout in gpdk090. Typical venues: *Analog Integrated
Circuits and Signal Processing*, *Int. J. Electronics*, *Integration*, *Microelectronics Journal* (check quartiles on SJR).

## 5. Files

| Path | What it is |
|---|---|
| `netlists/ngspice/` | A1–A4 with testbench `_A_dc` (DC transfer, AC input resistance and bandwidth, output sweep), plus `ptm90.lib`. |
| `netlists/ltspice/` | Same for LTspice (`.dc` by default; the `.ac` and output-sweep lines are given as comments). Change `level = 54` to `level = 14` in `ptm90.lib` if LTspice rejects it. |
| `netlists/cadence_gpdk090/` | Spectre netlists (`nmos1v`/`pmos1v`, `section=NN`). PTM sizes copied over: retune Vcn and booster sizes in GPDK090. |
| `scripts/` | `projA.py` (circuits and measurements), `runA.py` (corners and Monte Carlo), helper modules. |
| `results/plots/A_mirror_characteristics.png` | Gain error, input voltage, input impedance vs frequency, output characteristic. |
| `results/data/` | DC, input-impedance and output-sweep CSVs; `pvt_mc_results.json`; `pvt_mc_table.csv`. |
| `papers/PAPERS.md` | Base and supporting papers with DOIs and open-access links. |

Note: the output-side Ib subtraction uses an ideal current source, so output resistance is that of the NMOS mirror alone,
as in the base paper's measurement.

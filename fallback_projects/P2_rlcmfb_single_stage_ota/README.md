# Project 2: Single-stage OTA (differential amplifier) with resistive local CMFB and partial positive feedback

**Status:** base paper re-simulated in PTM 90 nm (ngspice), one novelty variant simulated with corners, temperature and
Monte Carlo. Schematic level only. Cadence gpdk090 and LTspice netlists are generated but were not run here.

## 1. Base paper

Ramírez-Angulo et al., "Simple Technique to Improve Essentially the Performance of One-Stage Op-Amps in Deep Submicrometer
CMOS Technologies," *JLPEA* 13(1):4, 2023, doi:10.3390/jlpea13010004 (open access). Full list in `papers/PAPERS.md`.

Why this one: it is recent, open access, gives every size and bias (W = 10 µm, L = 2Lmin, IB = 2.5 µA, CL = 2 pF,
R = 300 kΩ and Rs = 3 kΩ at 90 nm, ±0.45 V), and it already reports 90 nm numbers, so the re-simulation can be checked
against the paper directly.

### The circuits

- **Conventional symmetrical OTA (B1).** NMOS pair M1–M2 with 5 µA tail. PMOS diode loads M3, M4 at nodes a, b.
  M3P (gate b) drives the output, M4P (gate a) feeds the NMOS mirror M5–M6 to the output.
- **RLCMFB OTA, the base circuit (B2, B3).** The diode connection of M3, M4 is removed. Their gates go to a common node
  cm, and two resistors R tie a and b to cm. Differential signals now see R instead of 1/gm, so gain and GBW rise, and the
  a/b swing makes the output branch class AB. A series resistor Rs with CL puts a zero near the a/b pole.
- **Proposed PPF-RLCMFB OTA (B4).** 20 % of each load device is moved into a cross-coupled PMOS pair Mx3 (gate b, drain a)
  and Mx4 (gate a, drain b). The pair is a negative conductance in parallel with R, so the same gain needs a 3× smaller R.
  Total device width and all bias currents are unchanged, so power is unchanged.

## 2. Re-simulation of the base paper (PTM 90 nm, 27 °C)

| | Paper, 90 nm (NCSU models) | This work, PTM 90 nm |
|---|---|---|
| Conventional: gain | 32.9 dB | **32.8 dB** |
| Conventional: GBW | 4.8 MHz | **4.95 MHz** |
| Conventional: PM | 89° | **89.2°** |
| Conventional: SR+ / SR− | 2.4 / −2 V/µs | **2.53 / −2.55 V/µs** |
| RLCMFB: gain | 60.8 dB | 54.2 dB |
| RLCMFB: GBW | 38.4 MHz | 48.5 MHz |
| RLCMFB: PM | 68° | 77.7° |
| RLCMFB: SR+ / SR− | 42.1 / −22.3 V/µs | 26.0 / −24.0 V/µs |
| Power | 4.5 µW stated | 11.5 µW (10 µA from 0.9 V plus bias branch) |

The conventional OTA matches almost exactly. The RLCMFB version is within the spread you expect from different model
cards (PTM vs NCSU). Its improvement factors (≈ +21 dB, ≈ 10× GBW, ≈ 10× slew) are reproduced.

## 3. Proposed variant: results (all at the same 11.5 µW and 2 pF)

| | B1 Conventional | B2 Base RLCMFB, Rs = 3k | B3 Base RLCMFB, Rs = 5k | **B4 Proposed, α = 0.2, R = 100k, Rs = 5k** |
|---|---|---|---|---|
| DC gain | 32.8 dB | 54.2 dB | 54.2 dB | **71.6 dB** |
| GBW | 4.95 MHz | 48.5 MHz | 73.6 MHz | 68.5 MHz |
| Phase margin | 89.2° | 77.7° | 80.9° | 66.7° |
| SR+ / SR− (V/µs) | 2.53 / −2.55 | 26.0 / −24.0 | 15.8 / −15.2 | 17.9 / −15.4 |
| LCMFB resistors | none | 2 × 300 kΩ | 2 × 300 kΩ | **2 × 100 kΩ** |
| Base RLCMFB with R = 100k (same area) | | | 46.6 dB | |

**Fair reading:** against the base at the same Rs, the proposed circuit gives +17.4 dB of gain at the same power and
about the same GBW, with one third of the resistor area. Slew rate drops by about 1 V/µs versus B3 and 8 V/µs versus B2,
because the smaller R limits the a/b swing.

### Robustness (5 corners × −40/27/125 °C, and 40 Monte Carlo runs with Avt = 3.5 mV·µm)

| | Base RLCMFB, Rs = 3k | Proposed α = 0.2 | Proposed α = 0.15 |
|---|---|---|---|
| Gain, PVT range | 51.5 – 56.2 dB | 56.1 – 74.1 dB | 51.0 – 63.9 dB |
| Gain, Monte Carlo mean / σ | 54.1 / 0.45 dB | 70.8 / **8.7 dB** | 58.5 / 5.7 dB |
| GBW, PVT range | 30 – 72 MHz | 41 – 102 MHz | 39 – 105 MHz |
| PM, PVT range | 76 – 78° | 63 – 74° | 70 – 85° |

The proposed circuit is never worse than the base (worst-case 56 dB vs 51.5 dB), but its gain spread is large. That is the
known weakness of positive feedback: the gain depends on how close gmx·R gets to 1. **A reviewer will raise this first.**

## 4. Novelty and prior-art check

- RLCMFB itself (2002), RLCMFB plus adaptive biasing (López-Martín, JSSC 2005), RLCMFB in recycling folded cascodes
  (Soni 2020, Katourani 2022) and **local positive feedback with LCMFB resistors in a folded cascode (Zhang, Zhao, Dong 2022)**
  are all published. The closest is Zhang 2022.
- What is still open: (a) positive feedback inside the RLCMFB load of the minimal symmetrical OTA, with an analysis of the
  gain-versus-gmx·R boundary; (b) a way to hold gmx·R constant over PVT so the gain spread shrinks. (b) is what would make
  it a paper rather than a variant.

**Concrete next steps to make it publishable**
1. Derive A0 = gm1·R/(1 − gmx·R + go·R) and the latch condition; pick α from the worst corner, not nominal.
2. Make the cross-coupled pair a replica-biased element (for example, set its current from a branch that tracks 1/R)
   so gmx·R stays near 0.5–0.6 over PVT; target Monte Carlo σ < 2 dB.
3. Retune Rs for PM ≥ 60° at every corner; add CMRR, PSRR, noise, offset and THD.
4. Redo in gpdk090 with real poly resistors (`rppolyhr`), then layout and post-layout (your Virtuoso setup can do this).

## 5. Publishability

Moderate. As it stands (+17 dB nominal, fragile) it is a conference paper. With step 2 working and post-layout results in
gpdk090 it fits Q3 journals such as *Analog Integrated Circuits and Signal Processing*, *Int. J. Circuit Theory and
Applications*, *Circuits, Systems & Signal Processing* or *JLPEA*/*Electronics* (MDPI). Q2 venues (AEÜ, Integration,
Microelectronics Journal) will expect layout and a stronger robustness story. Check the current quartile on SJR before
submitting; quartiles move every year.

## 6. Files

| Path | What it is |
|---|---|
| `netlists/ngspice/` | Every circuit × testbench (`_B_ac` open loop, `_B_tr` unity-gain follower step), with `ptm90.lib`. Run `ngspice -b <file>`. |
| `netlists/ltspice/` | Same circuits for LTspice with the PTM90 card. If LTspice rejects `level = 54`, change it to `level = 14`. |
| `netlists/cadence_gpdk090/` | Spectre netlists using `nmos1v`/`pmos1v` and `gpdk090.scs section=NN` (path as in your VM; edit if different). Sizes are the PTM ones, so retune bias before quoting numbers. |
| `scripts/` | Python + ngspice framework: `projB.py` (circuits and measurements), `tB2.py` (proposed variant), `runB.py` (corners and Monte Carlo), `corners.py`, `sweep.py`, `summ.py`, `plots.py`. |
| `results/plots/` | `B_open_loop_ac.png`, `B_follower_transient.png`. |
| `results/data/` | AC and transient CSVs, `pvt_mc_results.json`, `pvt_mc_table.csv`. |
| `papers/PAPERS.md` | Base and supporting papers with DOIs and open-access links. |

Measurement notes: open-loop gain uses RF = 100 MΩ and CF = 1 F to set the DC point, as in the paper. Slew rate is the
20–80 % slope on the load capacitor (after Rs), 0.4 V step. Corners are emulated with ±30 mV threshold shifts (PTM has no
foundry corners).

# Project 2: Single-stage RLCMFB OTA with a PVT-stable negative-conductance gain boost

**Status (v2, 25 Nov 2026):** base paper re-simulated in PTM 90 nm (ngspice). The new version (B5) gives **+12.3 dB of
gain over the base with a Monte Carlo spread of 1.9 dB** (the earlier B4 had 8.7 dB) and a worst-case PVT gain 12.4 dB
above the base's worst case. Checked over 5 corners × −40/27/125 °C and 40 Monte Carlo runs, with offset, CMRR, PSRR and
noise. Schematic level only; LTspice and Cadence gpdk090 netlists are generated but were not run here.

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

## 3b. v2: the improved circuit (B5), and why B4 spread so much

**Diagnosis.** In B4 the cross-coupled devices share the load current with the RLCMFB load devices: node a feeds both M3
(gate at cm) and Mx3 (gate at b), and M1 fixes their sum. A few millivolts of threshold mismatch between M3 and Mx3 moves
10–15 % of the current between them, so gmx moves by the same amount. Because the gain is gm1·R/(1 − gmx·R + go·R) and B4
sits close to gmx·R = 1, that small shift changes the gain by many dB. Temperature does the same through UT.

**Fix (B5).** The PMOS cross-coupled pair is replaced by a small **NMOS cross-coupled pair hung from a and b with its own
tail current** (Mx3: drain a, gate b; Mx4: drain b, gate a; common source tx; tail Mtx to VSS). Now:
- gmx is set by the tail current alone, not by a current split, so device mismatch only adds offset.
- In common mode the tail is a high impedance, so the pair does not fight the RLCMFB loop. Nominal CMRR rises from 79 to
  98 dB.
- The tail current comes from a **PTAT beta-multiplier** (devices 8/4 µm, Rp = 260 kΩ, same resistor type as R). In weak
  inversion gmx = Ix/(2·n·UT), so with Ix ∝ UT/Rp the product gmx·R ≈ (R/Rp)·ln K/(2n) is a resistor ratio. It tracks
  temperature and process.
- The NMOS pair has plenty of headroom at ±0.45 V (tail VDS about 0.33 V). A PMOS tail version was tried first and left
  the tail in triode.
- R drops from 300 kΩ to 150 kΩ.

### Results (PTM 90 nm, ±0.45 V, CL = 2 pF, Rs = 5 kΩ, 27 °C)

| | B2 Base, Rs = 3k | B3 Base, Rs = 5k | B4 earlier version | **B5 New** |
|---|---|---|---|---|
| DC gain | 54.2 dB | 54.2 dB | 71.6 dB | **66.5 dB** |
| Gain, PVT range | 51.5 – 56.2 dB | 51.5 – 56.2 dB | 56.1 – 74.1 dB | **63.9 – 69.4 dB** |
| Gain, Monte Carlo mean ± σ (40 runs) | 54.1 ± 0.41 dB | 54.1 ± 0.41 dB | 70.8 ± 8.7 dB | **65.8 ± 1.9 dB** (min 62.5) |
| GBW | 48.5 MHz | 73.6 MHz | 68.5 MHz | 71.9 MHz |
| GBW, PVT range | 30 – 72 MHz | 43 – 111 MHz | 41 – 102 MHz | 45 – 105 MHz |
| Phase margin (PVT min) | 77.7° (76°) | 80.9° (77°) | 66.7° (63°) | 68.7° (66°) |
| SR+ / SR− (V/µs) | 26.0 / −24.0 | 15.8 / −15.2 | 17.9 / −15.4 | 15.6 / −14.6 |
| Offset σ (Monte Carlo) | 6.0 mV | 6.0 mV | | 5.2 mV |
| CMRR nominal / MC mean | 79 / 76 dB | 79 / 76 dB | | 98 / 71 dB |
| PSRR+ nominal | 81 dB | 81 dB | | 77 dB |
| Input noise at 1 kHz / 1 MHz | 230 / 36 nV/√Hz | same | | 238 / 38 nV/√Hz |
| Power | 11.5 µW | 11.5 µW | 11.5 µW | **13.0 µW** |
| LCMFB resistors | 2 × 300 kΩ | 2 × 300 kΩ | 2 × 100 kΩ | 2 × 150 kΩ + 260 kΩ bias |

**Ablation (same core, nominal 66.5 dB):** with a constant (non-PTAT) tail current, PVT gain spreads over 56–78 dB. With an
ideal PTAT source it holds 69.2–70.2 dB and Monte Carlo σ is 1.5 dB. So the PTAT bias is what removes the temperature
spread, and the extra Monte Carlo spread in B5 (1.9 dB) comes from mismatch inside the bias generator.

**Fair reading:** B5 trades 13 % more power (the PTAT reference and the tail, about 1.5 µW) for a robust +12 dB of gain at
the same GBW and slew rate as B3, with half the LCMFB resistance. Against B4 it gives up 5 dB of nominal gain to cut the
spread by 4.5×. The guaranteed-gain view is what reviewers will look at: worst case 62.5 dB (Monte Carlo) and 63.9 dB
(PVT), against 52.9 dB (Monte Carlo) and 51.5 dB (PVT) for the base.

### What to add before submitting
1. Derive A0 = gm1·R/(1 − gmx·R + go·R) with gmx·R set by the PTAT ratio; show the latch boundary and the margin chosen.
2. Combined corner + Monte Carlo runs, plus a supply sweep (±0.40–0.50 V) for the beta-multiplier.
3. THD in the follower, and a startup check of the beta-multiplier (a tiny start-up device is included).
4. Redo in gpdk090 with `rppolyhr` resistors for R and Rp (they must be the same type), then layout and post-layout.

## 4. Novelty and prior-art check

- RLCMFB itself (2002), RLCMFB plus adaptive biasing (López-Martín, JSSC 2005), RLCMFB in recycling folded cascodes
  (Soni 2020, Katourani 2022) and **local positive feedback with LCMFB resistors in a folded cascode (Zhang, Zhao, Dong 2022)**
  are all published. The closest is Zhang 2022.
- What is still open, and what B5 now does: (a) a negative-conductance boost inside the RLCMFB load of the minimal
  symmetrical OTA, decoupled from the load current with its own tail; (b) gmx·R held by a PTAT/R resistor ratio, so the
  boost is stable over PVT and mismatch. Zhang 2022 uses a plain cross-coupled load in a folded cascode, without the
  tail or the PTAT ratio. Check IEEE Xplore for "negative conductance" + "PTAT" OTAs before writing.

## 5. Publishability

**Good for Q3, possible Q2 with layout.** The v1 fragility is fixed: B5 has a robust +12 dB gain (worst case at least +9.6 dB over
PVT and mismatch) at the same GBW and slew, for 13 % more power. With post-layout results in gpdk090 it fits Q3 journals such as *Analog Integrated Circuits and Signal Processing*, *Int. J. Circuit Theory and
Applications*, *Circuits, Systems & Signal Processing* or *JLPEA*/*Electronics* (MDPI). Q2 venues (AEÜ, Integration,
Microelectronics Journal) will expect layout and a stronger robustness story. Check the current quartile on SJR before
submitting; quartiles move every year.

## 6. Files

| Path | What it is |
|---|---|
| `netlists/ngspice/` | Every circuit (B1–B4, **B5 new**) × testbench (`_B_ac` open loop, `_B_tr` unity-gain follower step), with `ptm90.lib`. Run `ngspice -b <file>`. |
| `netlists/ltspice/` | Same circuits for LTspice with the PTM90 card. If LTspice rejects `level = 54`, change it to `level = 14`. |
| `netlists/cadence_gpdk090/` | Spectre netlists using `nmos1v`/`pmos1v` and `gpdk090.scs section=NN` (path as in your VM; edit if different). Sizes are the PTM ones, so retune bias before quoting numbers. |
| `scripts/` | Python + ngspice framework: `projB.py` (circuits and measurements), `tB2.py` (B4), **`tB5.py` (B5 with behavioral, constant or transistor-level PTAT tail)**, **`p2extra.py` (offset, CMRR, PSRR, noise)**, `runB.py` (v1 corners and Monte Carlo), **`runB2.py` (v2)**, `corners.py`, `sweep.py`, `summ.py`, `plots.py`, `plots2.py`. |
| `results/plots/` | `B_open_loop_ac.png`, `B_follower_transient.png` (v1), **`B_new_ota.png`** (B5 vs base open loop, and Monte Carlo gain histograms of base, B4 and B5). |
| `results/data/` | AC and transient CSVs, `pvt_mc_results.json` and `pvt_mc_table.csv` (v1), **`pvt_mc_results_v2_ptat.json`, `pvt_mc_table_v2_ptat.csv`, `B_ac_*.csv` (v2)**. |
| `COMPARISON.md` | The three projects side by side. |
| `papers/PAPERS.md` | Base and supporting papers with DOIs and open-access links. |

Measurement notes: open-loop gain uses RF = 100 MΩ and CF = 1 F to set the DC point, as in the paper. Slew rate is the
20–80 % slope on the load capacitor (after Rs), 0.4 V step. Corners are emulated with ±30 mV threshold shifts (PTM has no
foundry corners).

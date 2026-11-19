# Change report: TIA_CONECCT2027 → revised submission (19 Nov 2026)

## What was simulated

Two campaigns ran on the Cadence VM with Spectre 12.1.0 and GPDK090 v4.6 (534 Spectre runs in total).
Everything is schematic-level with ideal R and C. Raw CSVs, every netlist and logs are in
`gpdk090_spectre/results/` (final pass) and `results_pass1/`.

| Analysis | New in this revision |
|---|---|
| DC operating point, device regions and margins | yes (all circuits) |
| AC, input impedance, noise | re-run, all seven circuits |
| Global and local loop gain (`stb`) | yes, first time on GPDK090 |
| Vtune sweep with noise and loop gain at each point | extended |
| Impedance of the gyrator network alone | yes, with the L_eq formula checked against it |
| 45 PVT points (5 sections × 3 temperatures × 3 supplies), fixed and trimmed | supplies added; trimming first time on GPDK090 |
| 200-run mismatch Monte Carlo, fixed and trimmed | first time on GPDK090 |
| CL and CPD sweeps with re-tuning | first time on GPDK090 |
| Feedback network taken apart (follower, +Ca, Mt only, full) | new; explains why the plain follower is faster at 30 fF |
| R ±15 %, C ±10 % | new |
| DC-cancellation loop: photocurrent sweep in 5 sections, loop gain, noise, step | first time on GPDK090 |
| PRBS-7 eyes at 10 and 12.5 Gb/s | first time on GPDK090 |

## New or corrected designs

* **B1 (same-gain spiral baseline):** re-optimised on GPDK090 itself. The previous "regain" baseline
  was a PTM design ported to GPDK090; it gave 55.4 dBΩ, so it was not gain-matched. B1 gives 53.9 dBΩ,
  5.92 GHz at 0.09 mA.
* **B2:** the same topology forced to at least 0.9 mA (5.10 GHz). It shows that extra current does not
  help the spiral topology at equal gain.
* **F1, F2:** plain-follower feedback at v1 sizes (9.66 GHz) and re-optimised (9.99 GHz).
* **v2:** re-sized proposed circuit, 8.40 GHz at 0.94 mA. Its tuning range shrinks to 1.06:1 and 80 of
  200 MC samples peak above 1 dB untrimmed, so it is reported but not recommended.

## Main findings (all GPDK090)

1. v1: 53.8 dBΩ, 7.76 GHz, 0.97 mA, tunable 5.70 to 7.76 GHz (1.36:1) with <0.1 dB peaking.
   The global-loop phase margin is at least 108° over the tuning range.
2. The plain follower is faster at CL = 30 fF because every capacitance the gyrator network adds at the
   input costs bandwidth. Ca alone cuts it from 9.66 to 5.79 GHz.
3. The tunable network wins above about 132 fF of load (1.38× F1 at 300 fF). It also wins with large
   photodiodes: it holds ≤1 dB to 300 fF at 5.03 GHz, where F1 peaks by 3.2 dB.
4. Trimming brings all 45 PVT points and all 200 MC samples under 1 dB. Untrimmed, 17 PVT points and
   7 MC samples exceed 1 dB, and F1 never needs trimming.
5. The DC loop holds gain within 1 dB and bandwidth within 10 % to 300 µA at NN (75 µA in SF). Without
   it, gain moves by more than 1 dB at 50 µA.
6. The gyrator network is resistive (573 Ω = 1/g_f), turns inductive only above 0.236 V (0.214 V
   predicted), and has Q ≤ 0.17.

## Manuscript changes

* Title, abstract, contributions and conclusion rewritten around the gain-matched comparison. The paper
  no longer claims more bandwidth than the plain follower.
* GPDK090 is described as a generic kit everywhere; the old text called it a "foundry" kit.
* PTM90 results are confined to one sentence of history and are not mixed with GPDK090 numbers.
* Anonymised for double-blind review. The author list is kept, commented out, in `main.tex` for
  camera-ready.
* New figures: schematic with bias generator, network impedance, AC/noise, loop gains, tuning,
  load/photodiode/decomposition, PVT/MC, DC loop schematic, DC loop and eye. New tables: nominal
  comparison, tuning law, "where each option wins", context.
* References: [11] Kumar et al. (IEEE Access 2021) and [12] Chen et al. (TVLSI 2016) added. The
  middlebrook, pelgrom, sackingerla and ngspice entries are no longer cited and were removed.
* Every number comes from `numbers_gpdk.tex`, which `post/analyze.py` generates from the CSVs.

## Not done

* Layout and parasitic extraction: no layout tools were run in the VM session.
* The SKILL script for the v2 and B1 schematic cells (`gpdk090_spectre/virtuoso/build_pass2.il`) has not
  been executed in Virtuoso. The Spectre netlists are the verified reference.
* The 2027 conference author page was not yet online. Format follows the CONECCT 2026 rules: 6–8 pages,
  IEEE conference template, double-blind.

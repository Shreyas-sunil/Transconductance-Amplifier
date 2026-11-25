# Fallback analog projects: comparison and recommendation (v2, 25 Nov 2026)

Three projects, each built on a 2023 open-access base paper, re-simulated in PTM 90 nm with ngspice, with the proposed
circuit checked over 5 corners, −40/27/125 °C and Monte Carlo. All results are schematic level. LTspice and Cadence
gpdk090 netlists are included but were not run here.

## At a glance

| | P1 Current mirror | P2 Single-stage OTA (RLCMFB) | P3 0.6 V class-AB two-stage OTA |
|---|---|---|---|
| Base paper | Ramírez-Angulo et al., JLPEA 2023 (FVF mirror, 0.212 Ω Rin) | Ramírez-Angulo et al., JLPEA 2023 (resistive local CMFB) | Ballo, Grasso, Pennisi, JLPEA 2023 (bulk-driven, QFG class AB) |
| Base re-simulation | Character reproduced (0.54 Ω, −0.007 %, 7 GΩ); circuit rebuilt from text, needs a Fig. 4 check | **Matches the paper** (conventional 32.8 dB / 4.95 MHz vs 32.9 / 4.8) | Small signal matches, slew asymmetry reproduced |
| Proposed | **Dynamic element matching of the mirror pair + cascoded-booster FVF core** | **NMOS cross-coupled pair with its own PTAT tail in the RLCMFB load** | Dynamic QFG pull-down for positive slew |
| Key result | **Random error σ 6.2 % → 0.23 %; Rin 0.065 Ω (paper 0.212); Vin 0.175 V; compliance 0.165 V; BW 409 MHz; same power** | **+12.3 dB gain (66.5 dB), Monte Carlo σ 1.9 dB (v1: 8.7 dB), PVT 63.9–69.4 dB, same GBW and slew** | 12× SR+, but a large-signal limit cycle |
| Main cost or risk | Clock ripple at the output (averaged current is accurate); Rout 19 GΩ, capped by 90 nm gate tunnelling (812 GΩ without it) | +13 % power (13.0 vs 11.5 µW) | Oscillation in most runs; base latches at 125 °C |
| Closest prior art | DEM in DACs (1976); FVF mirrors 2016–2023, none with DEM or Monte Carlo accuracy | Zhang, Zhao, Dong 2022 (positive feedback + LCMFB, no tail or PTAT) | Adaptive-bias class-AB OTAs (Centurelli, Barile, Beloso-Legarra) |
| Effort to a paper | Moderate (gpdk090 + layout, ripple spectrum) | Low to moderate (gpdk090 + layout, analysis) | Moderate to high |
| Publishability | **Moderate to good** | **Good for Q3, possible Q2 with layout** | High upside, high risk |
| Venues | JLPEA/Electronics now; AEÜ, Integration, MEJ, IJCTA with layout | AICSP, IJCTA, CSSP, JLPEA; AEÜ/Integration/MEJ with layout | AEÜ, Integration, MEJ, IJCTA, JLPEA |

## Recommendation

1. **P1 and P2 are both strong now.** P1 has the more striking headline: it beats the base paper on accuracy under
   mismatch, Rin, input voltage, compliance and bandwidth. Its one honest gap is Rout, which is a 90 nm technology limit.
   P2 is the simplest to verify in gpdk090 and to explain.
2. Pick **P1 if you want the stand-out paper**, P2 if you want the quickest safe one. Doing both is realistic: they share
   the tools and the PTM/gpdk090 flow.
3. **Keep P3 as a stretch.** It needs the limit cycle and the hot latch fixed before it is a paper.

For any of them, a Q2 journal will expect gpdk090, layout and post-layout extraction, plus a figure-of-merit table against
6–10 recent papers. Check journal quartiles on SJR before submitting.

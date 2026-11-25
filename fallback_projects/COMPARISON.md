# Fallback analog projects: comparison and recommendation

Three projects, each built on a 2023 open-access base paper, re-simulated in PTM 90 nm with ngspice, with one novelty
variant checked over 5 corners, −40/27/125 °C and Monte Carlo. All results are schematic level. LTspice and Cadence
gpdk090 netlists are included but were not run here.

## At a glance

| | P1 Current mirror | P2 Single-stage OTA (RLCMFB) | P3 0.6 V class-AB two-stage OTA |
|---|---|---|---|
| Base paper | Ramírez-Angulo et al., JLPEA 2023 (FVF mirror, 0.212 Ω Rin) | Ramírez-Angulo et al., JLPEA 2023 (resistive local CMFB) | Ballo, Grasso, Pennisi, JLPEA 2023 (bulk-driven, QFG class AB) |
| Base re-simulation | Character reproduced (0.54 Ω, −0.007 %, 7 GΩ). Circuit rebuilt from text, needs a Fig. 4 check | **Matches the paper** (conventional 32.8 dB / 4.95 MHz vs 32.9 / 4.8) | Small signal matches, slew asymmetry reproduced |
| Novelty tried | One differential booster instead of two | Partial positive feedback inside the RLCMFB load | Dynamic QFG pull-down for positive slew |
| Key result | Trade-off: −55 mV input headroom, but 46× higher Rin | **+17.4 dB gain at the same power, 3× less resistor area** | 12× SR+, but a large-signal limit cycle |
| Main risk | No clear win; mismatch (5–7 % σ) dominates every topology | Gain spread (Monte Carlo σ 8.7 dB) from positive feedback | Oscillation in most runs; base latches at 125 °C |
| Closest prior art | Gain-boosted FVF mirrors 2019, base paper 2023 | Zhang, Zhao, Dong 2022 (positive feedback + LCMFB in a folded cascode) | Adaptive-bias class-AB OTAs (Centurelli, Barile, Beloso-Legarra) |
| Fix needed to publish | A new idea (chopped or dynamically matched mirror) | Replica-bias the cross-coupled pair so gmx·R stays ~0.5–0.6 | Tame the booster loop and the hot latch |
| Effort to a paper | High (new idea from scratch) | **Low to moderate** (2–3 weeks + gpdk090 layout) | Moderate to high (2–4 weeks before you know if it works) |
| Publishability | Low | **Moderate, Q3 now, Q2 with layout** | High upside, high risk |
| Venues | AICSP, Int. J. Electronics, Integration, MEJ | AICSP, IJCTA, CSSP, JLPEA/Electronics; AEÜ/Integration/MEJ with layout | AEÜ, Integration, MEJ, IJCTA, JLPEA |

## Recommendation

1. **Start with P2.** The base paper replicates almost exactly, the circuit is small, the improvement is large and simple to
   explain, and the one weakness (gain spread) has a clear fix to try. It is the safest fallback.
2. **Keep P3 as the stretch.** It attacks a weakness the base paper reports itself and adds a 125 °C failure the paper did
   not check. If the limit cycle can be removed it is the strongest paper of the three.
3. **Park P1** unless a mismatch-reduction idea comes up. As simulated it does not beat its base paper.

For any of them, a Q2 journal will expect a real PDK (gpdk090), layout and post-layout extraction, plus noise, offset,
CMRR/PSRR and a figure-of-merit table against 6–10 recent papers. Check journal quartiles on SJR before submitting.

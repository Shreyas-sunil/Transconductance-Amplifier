# Simulated peer review, CONECCT 2027 submission

Three reviews written against the final manuscript as a hostile reviewer would, followed by what was
changed and what could not be changed. Scores use a 1 (reject) to 5 (strong accept) scale.

## Reviewer 1 (novelty), score 2 → 3 after revision

1. *Active-inductor feedback in current-mirror TIAs is not new.* The same group's TIAs [6], [14] use
   active inductors, and bandwidth-tunable TIAs were measured in 2006 and 2010 [15], [16].
   **Response:** agreed. The introduction now says that the network itself is not claimed as new and
   states the contribution as a gain-matched measurement of its cost and benefit. It also names the
   difference from [6], [14]: those use local, untuned PMOS active inductors, and this design replaces
   the global output-to-input spiral and is tuned.
2. *By your own numbers the proposed circuit loses.* It loses to the plain follower at nominal load
   (20 % less bandwidth) and to the spiral on efficiency (10.9× the current).
   **Response:** stated in the abstract, Table II, Table IV and the conclusion. The claim is now limited
   to the cases where the tuning input helps: photodiode capacitance, heavy load, and corner and
   mismatch trimming.
3. *Calling it an "active inductor" is misleading when it is resistive at the operating point.*
   **Response:** accepted. Section III-B now shows that the network is inductive only above 0.236 V and
   acts as a movable zero over the flat-response range. "Gyrator-C feedback" replaces "active inductor"
   in the title and figures.
4. *The criticism of the 2020 paper rests on a predictive-model fit that is not shown.*
   **Response:** the GPDK090 operating point (M1 at 0.12 nA, region 1) is shown. The fit is described
   as earlier work, and the paper does not compare against the published curve.

## Reviewer 2 (methodology), score 3 → 3

1. *Is the spiral baseline fair?* B1's mirror widths ended at the search's 0.2 µm lower bound.
   **Response:** reported in Section IV. The same bounds, constraints and test bench were used for every
   circuit. B2 shows that giving the spiral topology more current makes it slower at equal gain.
   **Not changed:** the bound was not lowered to the kit minimum. A smaller B1 would only widen the
   efficiency gap, which already favours B1.
2. *B1 uses ideal bias voltages, which makes its PVT spread look worse than a real design.*
   **Response:** said explicitly in VI-A and in the limitations. The PVT comparison is used only for v1
   against F1.
3. *Monte Carlo covers mismatch only.* **Response:** stated. Process spread is covered by the five
   corner sections.
4. *Trimming per die needs a DAC and a calibration loop that is not designed.* **Response:** stated as a
   limitation.
5. *Noise integrated to each circuit's own bandwidth makes the comparison uneven.* **Response:** the
   values integrated to a common 10 GHz are now given as well, with a sensitivity estimate.
6. *The eye diagrams are noiseless.* **Response:** stated. They are used only to show the absence of
   ringing.
7. *Schematic-level only.* **Not fixable in this revision.** There is no layout or extraction. The
   limitations section names the node that extraction would hurt most: the gyrator network adds
   capacitance at the input.

## Reviewer 3 (circuit performance), score 2 → 3

1. *0.97 mA for 7.8 GHz at 54 dBΩ is not efficient.* **Response:** agreed and stated. v2 shows that
   re-sizing buys 8 % bandwidth at 4 % less current but gives up the tuning range. v1 is kept for that
   reason.
2. *M1 has only 56 mV of saturation margin, and 10 of 45 corners leave saturation.* **Response:**
   reported with the corners named (slow, hot, low supply). F1 has the same weakness because the input
   stage is shared.
3. *Overload at 50 µA without the DC loop; the loop's corner limit is lower.* **Response:** the 75 µA
   worst-section limit (SF, set by the 10 % bandwidth criterion) and the 2 MHz low-frequency corner are
   now in the text.
4. *No sensitivity figure.* **Response:** added. 1.51 µA rms gives about 21 µA peak to peak at
   BER 1e-12, excluding later stages.
5. *Stability over tuning is asserted, not shown.* **Response:** Fig. 4 and Table III now give loop
   gains, crossover frequencies and phase margins (at least 108°) at every Vtune setting.

## Acceptance risk

| Risk | Level | Why |
|---|---|---|
| Novelty judged incremental | High | The network is known. The paper's value is the gain-matched comparison and the honest crossover analysis. |
| Simulation-only, generic PDK | Medium | Acceptable for CONECCT's VLSI track if declared, which it is. |
| Proposed circuit loses on the headline metric | Medium | Mitigated by stating it plainly and showing where the tuning input pays. |
| Format and anonymity | Low | Six pages, IEEE conference template, author block removed, no self-citation by name. |

Overall estimate: borderline accept to weak accept at a regional IEEE conference such as CONECCT. It is
more likely to be accepted than the previous draft, which claimed GPDK090 was a "foundry" kit and
compared against a spiral baseline that was not gain-matched.

# Literature review and novelty check

Search done 13 Nov 2026 with general web search (IEEE Xplore, Wiley, Springer, ResearchGate, university
repositories). Not a systematic database search: run the same queries in IEEE Xplore and Scopus before submission.

## Verdict

**No single element of the proposed circuit is new.** Each one has prior art:

| Element of this work | Closest prior art | What they did |
|---|---|---|
| Source-follower active inductor | Razavi, IEEE SSC Magazine 2020; Yuan 2008 | A source follower with a gate resistor gives an inductive output impedance. Standard textbook circuit. |
| Active inductor in a current-mirror TIA | Shaaban *et al.*, Int. J. Circuit Theory Appl. 2025 (doi 10.1002/cta.4353) | Current-mirror TIA, 45 nm, 1 V, 1 pF photodiode; shunt-inductive peaking with passive and two active-inductor versions. Passive version: 30.6 dBΩ, 2.8 GHz, 1.63 mW, 23.55 pA/√Hz. |
| | Zohoori *et al.*, Microelectronics J. 2018 | Current-mirror TIA, 90 nm, 1 V, active-inductor output load: 40.5 dBΩ, 7 GHz, 1.4 mW. |
| | Al-Berwari & Alsheikhjader, Rafidain J. Sci. 2023; Alsheikhjader & Issa, JJP 2024; Alyas & Alsheikhjader, JJP 2026 | Same group as the baseline paper. CG/CS or RGC input plus current mirror with PMOS triode active inductors as *local* feedback. 42 dBΩ at 1 GHz (2023); 68.2 dBΩ, 2.5 GHz, 0.555 mW (2024). |
| Flipped-voltage-follower input | Güngördü *et al.*, AICSP 2022; FVF current-mirror input in the FGATI detector front end | FVF-based TIA input stages exist; the 2022 work is 1 V, 1.2 mW, up to 400 MHz. |
| Inductorless active feedback at input | Lu *et al.*, IEEE TVLSI 2010; Taghavi *et al.*, IEEE TCAS-I 2015 | CG input with CS active feedback (54.6 dBΩ, 7 GHz measured); modified RGC, 10 Gb/s. |
| Voltage-tuned TIA bandwidth | Hwang *et al.*, IEEE MWCL 2006 | Measured: 3.9 to 7.6 GHz at constant 52 dBΩ, 0.18 µm, 2 V, 34 mW. Tuning chosen for lowest BER. |
| | Chien *et al.*, IEEE TMTT 2010 | Measured: 6.2 to 10.5 GHz, 47.8 dBΩ, 0.18 µm, 1.8 V, 33.3 mW; feedback loop as tuning mechanism. |
| | Dash, Cowan & Liboiron-Ladouceur, NEWCAS 2013 | Variable-bandwidth, power-scalable receiver front end, 65 nm, 0.85 to 13.5 GHz. |

## What can still be claimed

Not found in the search: an active inductor used as the **global output-to-input feedback** of a current-mirror
TIA, replacing a passive spiral, with **one control voltage** used both to set bandwidth and to **trim PVT peaking**,
at 1 V. That is a narrow, incremental combination. The second contribution, which no one else can make, is the
BSIM4 re-simulation showing the 2020 baseline circuit does not behave as published.

The paper (`paper/main.tex`) now says this explicitly in a "Related work and positioning" paragraph and no longer
implies that tunability or inductorless operation are new.

## Corrections made to the paper

- Reference [abdalla] was wrong. The Int. J. Circuit Theory Appl. paper (doi 10.1002/cta.4353) is by **Shaaban *et al.*, 2025**,
  not Abdalla 2024. Fixed. **First names and co-authors still need checking on the Wiley page.**
- Zohoori 2018 uses an active-inductor load; the comparison table said "none". Fixed.
- Hassan 2012 is 40 nm; the table said "n/r". Fixed.
- Added Shaaban 2025, Chien 2010, and power figures for Hwang 2006 and Alsheikhjader & Issa 2024 to the comparison table,
  marked which entries are measured silicon.
- Added seven references: Lu 2010, Taghavi 2015, Razavi 2020, Al-Berwari 2023, Güngördü 2022, Chien 2010, Dash 2013.
  Volume, issue and page numbers for Lu 2010, Taghavi 2015 and Razavi 2020 were written from memory, not from the
  search results: check them.

## What this means for a Q1/Q2 submission

The strongest comparators (Hwang 2006, Chien 2010, Lu 2010) are **measured silicon**. A simulation-only paper with a
predictive model will be compared against them. Realistic options:

1. Keep it simulation-only and target a journal that accepts design studies (the baseline's own follow-ups went to
   Rafidain J. Sci. and Jordan J. Phys.; Shaaban 2025 went to IJCTA as simulation). Check each journal's current
   quartile yourself before choosing.
2. Strengthen it toward Q1: move to a foundry PDK, add the DC-cancellation loop, do post-layout extraction, and ideally
   tape out.

## Queries run

- active inductor feedback transimpedance amplifier CMOS tunable bandwidth
- inductorless current-mirror transimpedance amplifier 10 Gb/s CMOS
- flipped voltage follower transimpedance amplifier optical receiver
- source follower active inductor shunt peaking TIA gyrator bandwidth extension
- flipped-voltage-follower current-mirror (FVF-CM) transimpedance amplifier input stage
- tunable bandwidth TIA control voltage active inductor peaking reconfigurable
- "An Active Inductor Based Transimpedance Amplifier with Two Local Feedbacks"
- TIA source follower feedback output to input active inductor global feedback
- Hwang *et al.* "A CMOS tunable transimpedance amplifier" MWCL 2006
- variable bandwidth power-scalable optical receiver front-end 65 nm

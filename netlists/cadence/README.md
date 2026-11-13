# Cadence files

| File | What it is |
|---|---|
| `baseline_tia.scs`, `proposed_tia.scs` | Spectre netlists of the reference and proposed circuits. Run `spectre proposed_tia.scs`. Analyses: DC operating point, AC transimpedance, input-referred noise, and (proposed only) a Vtune sweep. |
| `ptm90.lib` | PTM 90 nm BSIM4 card in SPICE syntax. Spectre reads non-`.scs` includes as SPICE. |
| `build_tia_schematics.il` | SKILL script that draws both schematics in Virtuoso from analogLib parts. In the CIW: `load("build_tia_schematics.il")` then `tiaBuildAll("YOUR_LIB")` (the library must exist). Nets are joined by wire labels. |
| `plot_results.ocn` | OCEAN script that plots gain and noise from the Spectre result directories. |

For ADE: open the generated schematic, choose Spectre, add `ptm90.lib` under Setup > Model Libraries, and create
design variables with the values listed at the top of the `.scs` file (`vdd`, `cpd`, `cout`, `iref`, `vtune`, `rn`, `rb`, `ca`, `cb`).

These files were generated from `scripts/circuits.py` without access to a Cadence installation, so they have not been run.
The ngspice netlists in `../ngspice` are the ones that produced the published numbers; compare against them first.
A native Virtuoso cellview (OpenAccess database) cannot be produced outside Cadence, which is why the schematic is delivered as a SKILL script.

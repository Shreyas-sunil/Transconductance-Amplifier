# Cadence files

| File | What it is |
|---|---|
| `baseline_tia.scs` | The 2020 baseline exactly as drawn (M2b gate at VDD, 2.4 nH ideal spiral). |
| `baseline_reopt_gain.scs` | Same topology, re-optimised for maximum bandwidth at the proposed TIA's gain (fair comparison). |
| `baseline_reopt_gbw.scs` | Same topology, re-optimised for maximum gain-bandwidth product (fair comparison). |
| `proposed_tia.scs` | Proposed TIA. Analyses: DC operating point, AC transimpedance, input-referred noise and a Vtune sweep. |
| `proposed_tia_dcc.scs` | Proposed TIA with the DC-cancellation loop. Design variable `idc` is the average photocurrent. Adds a sweep of `idc` (0, 100, 300, 500 uA) and a transient photocurrent step (0 to 200 uA and back) that shows the loop settling. |
| `ptm90.lib` | PTM 90 nm BSIM4 card in SPICE syntax. Spectre reads non-`.scs` includes as SPICE. |
| `build_tia_schematics.il` | SKILL script that draws all five schematics in Virtuoso from analogLib parts. In the CIW: `load("build_tia_schematics.il")` then `tiaBuildAll("YOUR_LIB")` (the library must exist). Nets are joined by wire labels. |
| `plot_results.ocn` | OCEAN script that plots gain and noise from the Spectre result directories. |

Run any netlist with `spectre <name>.scs`.

For ADE: open the generated schematic, choose Spectre, add `ptm90.lib` under Setup > Model Libraries, and create
design variables with the values listed at the top of the matching `.scs` file. The baseline variants use `vg2b`,
`vg3b`, `lf` and `rsl`; the DCC version adds `rtap`, `ctap`, `cint` and `idc`.

These files are written by `scripts/emit.py` from `scripts/circuits.py` and have not been run in Cadence yet.
The ngspice netlists in `../ngspice` are the ones that produced the published numbers; compare against them first.
A native Virtuoso cellview (OpenAccess database) cannot be produced outside Cadence, which is why the schematic is delivered as a SKILL script.

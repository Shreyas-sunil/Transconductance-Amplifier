# GPDK090 Cadence cross-check

Virtuoso 6.1.5 / Spectre 12.1, GPDK090 v4.6 models (`nmos1v`, `pmos1v`), 1 V, C_PD = 50 fF, C_L = 30 fF.
The GPDK090 model files belong to the kit and are not included.

| File | What it does |
|---|---|
| `gen.py` | Writes `build_gpdk090.il` (SKILL builder for `TIA_2020_base_gpdk090` and `TIA_proposed_v1_gpdk090`) |
| `gen_regain.py` | Writes `build_regain.il` (same-gain baseline `TIA_2020_regain_gpdk090`) |
| `check.py` | Connectivity check of the generated schematics |
| `sim.ocn` | Nominal AC run |
| `sweep.ocn` | `vtn` (V_tune) sweep of the proposed cell |
| `corners.ocn` | 3 cells x NN/SS/FF/FS/SF x -40/35/125 C |
| `noise.ocn` | Input-referred noise, NN, 35 C |
| `library/TIA_Proj_gpdk090.tgz` | The Virtuoso library (base and proposed cells) |

Run a builder with `virtuoso -nograph -replay build_gpdk090.il`, then `ocean -nograph -restore corners.ocn`.
Results are in `../results/gpdk090/`; `../scripts/gpdk090_tables.py` turns them into the paper tables.
All device lengths are >= 100 nm, the kit minimum. Schematic-level only.

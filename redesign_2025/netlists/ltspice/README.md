# LTspice files (PTM 90 nm BSIM4, VDD = 1 V)

Eleven circuits, each as three files. Keep everything in this folder (the `.net` and `.asc` read `ptm90.lib`; the `.asc`
files also need `tia_nmos4.asy` and `tia_pmos4.asy`).

| File | Use |
|---|---|
| `<name>.asc` | Schematic with the AC analysis already set. Open it and press Run, then click the `out` net to plot Zt. Nets are joined by label |
| `<name>.net` | The same circuit as a netlist: File > Open (change the file type to All files), then Run. The `.noise` and `.op` lines are commented, remove the `;` to use one (one analysis at a time) |
| `<name>_eye.net` | Transient with a 3 Gb/s PRBS7 current (20 uA peak-to-peak), written inline. Plot `V(out)`. LTspice has no eye view: right-click the x-axis and enter `mod(time,333.33p)` to fold it |

| `<name>` | What it is |
|---|---|
| `base_mdfrgc_robust`, `base_mdfrgc_nominal` | Base paper (Abdollahi 2025), rebuilt from its equations; worst-case and nominal sizing |
| `ref_rgc_robust` | Conventional RGC |
| `prop_mdfrgc_trim` | **Proposed** trimmable negative-RC TIA. Parameter `vcv` is the control voltage; `.step param vcv 0 1 0.05` is in the file (commented) |
| `var_cmnrc_robust`, `var_cmnrc_nominal`, `var_cmrgc_robust` | Current-mirror variants (negative result) |
| `ref_shaaban_L`, `ref_shaaban_AN`, `ref_shaaban_AP` | Shaaban 2025 **reconstructions** from the abstract (not their circuit) |
| `ref_pftia_earlier` | Earlier work of this project |

Expected nominal results are in `../../results/tables.md`; for example `base_mdfrgc_robust` should give 56.8 dB at low
frequency and 4.0 GHz, `prop_mdfrgc_trim` 67.6 dB and 2.76 GHz. The `.meas` lines print `zt0` (low-frequency gain, as a
magnitude) and `f3db` (-3 dB frequency) in the log (View > SPICE Output Log).

## What was checked, and what was not

LTspice was not available to me. `scripts/verify_ltspice.py` checks every file another way: it rebuilds a netlist from
each `.asc` (pin positions, wires and net labels), takes each `.net` and `_eye.net` as written, simulates all three in
ngspice and compares them with the verified results. All 11 circuits agree (gain within 0.05 dB, bandwidth within 1 %,
eye swing within 10 %; see `../../results/ltspice_verification.json`). That proves connectivity, values and the shape
of the files. It does **not** prove LTspice's own behaviour:

* The model card uses `level = 54` (the standard PTM BSIM4 card). If LTspice rejects it, change `level = 54` to
  `level = 14` in `ptm90.lib` (both models).
* If LTspice reports a DC convergence problem (ngspice needed gmin stepping), add `.options gmin=1e-10` or `.options cshunt=1e-15`.
* `.noise V(out) Iin ...` uses the current source as the input, which LTspice accepts.
* The schematic layout is an automatic grid, not tidy. Connectivity is by net label.

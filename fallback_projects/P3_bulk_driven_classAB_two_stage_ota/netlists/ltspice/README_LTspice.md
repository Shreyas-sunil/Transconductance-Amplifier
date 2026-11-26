# LTspice simulations (P3_bulk_driven_classAB_two_stage_ota)

Every circuit of this project as a ready-to-run LTspice schematic (`.asc`) and the same deck as a netlist (`.net`). Both use
`ptm90.lib` (PTM 90 nm BSIM4, the same file as your TIA LTspice runs) from this folder.

**How to run:** keep the whole folder together, open an `.asc`, press Run. The `.meas` results appear in the error log
(View > SPICE Error Log). Each file holds one analysis; one circuit has one file per testbench.

**How the schematics are drawn:** each device is placed on a grid and its pins carry net labels. Pins with the same label
are connected. This keeps the files exact copies of the simulated netlists. Move parts and draw wires if you want a
textbook-style drawing for the paper; the labels keep it connected while you do.

**Checks done here:** the connectivity of every `.asc` was read back from its geometry and compared with the netlist, and
every deck was simulated in ngspice with the same model. The right-hand column is that ngspice result. LTspice itself
could not be run in the cloud, so expect small differences (solver tolerances) and tell me if a file does not open or run.

| File | Testbench | ngspice reference result |
|---|---|---|
| `C1_base_reconstruction_C_ac.asc` / `.net` | Open-loop AC | A0 69.6 dB, UGF 0.399 MHz, PM 74.1° |
| `C1_base_reconstruction_C_tr.asc` / `.net` | Unity-gain follower, 0.1→0.5 V step | SR+ 0.0439 V/µs, SR− -4.79 V/µs |
| `C2_proposed_dyn_qfg_W0p3_C_ac.asc` / `.net` | Open-loop AC | A0 70.4 dB, UGF 0.417 MHz, PM 78.6° |
| `C2_proposed_dyn_qfg_W0p3_C_tr.asc` / `.net` | Unity-gain follower, 0.1→0.5 V step | SR+ 0.178 V/µs, SR− -4.6 V/µs |
| `C3_proposed_dyn_qfg_W0p5_C_ac.asc` / `.net` | Open-loop AC | A0 70.7 dB, UGF 0.421 MHz, PM 80.5° |
| `C3_proposed_dyn_qfg_W0p5_C_tr.asc` / `.net` | Unity-gain follower, 0.1→0.5 V step | SR+ 0.536 V/µs, SR− -4.18 V/µs |

Note: C3 shows the large-signal limit cycle described in the README (its falling edge comes right after the rise).

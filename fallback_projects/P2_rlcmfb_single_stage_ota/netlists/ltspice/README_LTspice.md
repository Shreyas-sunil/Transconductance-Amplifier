# LTspice simulations (P2_rlcmfb_single_stage_ota)

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
| `B1_conventional_ota_B_ac.asc` / `.net` | Open-loop AC | A0 32.8 dB, UGF 4.95 MHz, PM 89.2° |
| `B1_conventional_ota_B_tr.asc` / `.net` | Unity-gain follower, ±0.2 V step | SR+ 2.5 V/µs, SR− -2.6 V/µs |
| `B2_base_rlcmfb_Rs3k_B_ac.asc` / `.net` | Open-loop AC | A0 54.2 dB, UGF 48.5 MHz, PM 77.7° |
| `B2_base_rlcmfb_Rs3k_B_tr.asc` / `.net` | Unity-gain follower, ±0.2 V step | SR+ 26.0 V/µs, SR− -24.1 V/µs |
| `B3_base_rlcmfb_Rs5k_B_ac.asc` / `.net` | Open-loop AC | A0 54.2 dB, UGF 73.6 MHz, PM 80.9° |
| `B3_base_rlcmfb_Rs5k_B_tr.asc` / `.net` | Unity-gain follower, ±0.2 V step | SR+ 15.7 V/µs, SR− -15.3 V/µs |
| `B4_v1_ppf_rlcmfb_B_ac.asc` / `.net` | Open-loop AC | A0 71.6 dB, UGF 68.5 MHz, PM 66.7° |
| `B4_v1_ppf_rlcmfb_B_tr.asc` / `.net` | Unity-gain follower, ±0.2 V step | SR+ 18.0 V/µs, SR− -15.2 V/µs |
| `B5_proposed_nmos_xc_ptat_B_ac.asc` / `.net` | Open-loop AC | A0 66.5 dB, UGF 71.9 MHz, PM 68.7° |
| `B5_proposed_nmos_xc_ptat_B_tr.asc` / `.net` | Unity-gain follower, ±0.2 V step | SR+ 15.5 V/µs, SR− -14.7 V/µs |

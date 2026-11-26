# LTspice simulations (P1_current_mirror)

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
| `A1_conventional_cascode_mirror_A_dc.asc` / `.net` | DC sweep of Iin, 0–20 µA | error at 10 µA +0.1449 %, at 2 µA +0.0343 %, V(inn) at 10 µA 0.339 V |
| `A1_conventional_cascode_mirror_A_ac.asc` / `.net` | AC, input impedance and current-gain bandwidth | Rin at 1 kHz 5490 Ω, −3 dB bandwidth 635 MHz |
| `A1_conventional_cascode_mirror_A_out.asc` / `.net` | DC sweep of the output voltage Vo, 0–1 V | -I(Vo) at 0.5 V 10.0145 µA (Rout: see README) |
| `A2_plain_fvf_mirror_A_dc.asc` / `.net` | DC sweep of Iin, 0–20 µA | error at 10 µA -2.1848 %, at 2 µA -0.8650 %, V(inn) at 10 µA 0.176 V |
| `A2_plain_fvf_mirror_A_ac.asc` / `.net` | AC, input impedance and current-gain bandwidth | Rin at 1 kHz 24.88 Ω, −3 dB bandwidth 349 MHz |
| `A2_plain_fvf_mirror_A_out.asc` / `.net` | DC sweep of the output voltage Vo, 0–1 V | -I(Vo) at 0.5 V 9.7815 µA (Rout: see README) |
| `A3_base_fvf_mirror_reconstruction_A_dc.asc` / `.net` | DC sweep of Iin, 0–20 µA | error at 10 µA -0.0072 %, at 2 µA -0.0052 %, V(inn) at 10 µA 0.231 V |
| `A3_base_fvf_mirror_reconstruction_A_ac.asc` / `.net` | AC, input impedance and current-gain bandwidth | Rin at 1 kHz 0.5378 Ω, −3 dB bandwidth 340 MHz |
| `A3_base_fvf_mirror_reconstruction_A_out.asc` / `.net` | DC sweep of the output voltage Vo, 0–1 V | -I(Vo) at 0.5 V 9.9993 µA (Rout: see README) |
| `A4_v1_single_booster_mirror_A_dc.asc` / `.net` | DC sweep of Iin, 0–20 µA | error at 10 µA -0.0902 %, at 2 µA -0.0956 %, V(inn) at 10 µA 0.176 V |
| `A4_v1_single_booster_mirror_A_ac.asc` / `.net` | AC, input impedance and current-gain bandwidth | Rin at 1 kHz 24.87 Ω, −3 dB bandwidth 351 MHz |
| `A4_v1_single_booster_mirror_A_out.asc` / `.net` | DC sweep of the output voltage Vo, 0–1 V | -I(Vo) at 0.5 V 9.9910 µA (Rout: see README) |
| `A5_enhanced_core_cascoded_boosters_A_dc.asc` / `.net` | DC sweep of Iin, 0–20 µA | error at 10 µA -0.0035 %, at 2 µA -0.0041 %, V(inn) at 10 µA 0.175 V |
| `A5_enhanced_core_cascoded_boosters_A_ac.asc` / `.net` | AC, input impedance and current-gain bandwidth | Rin at 1 kHz 0.06508 Ω, −3 dB bandwidth 494 MHz |
| `A5_enhanced_core_cascoded_boosters_A_out.asc` / `.net` | DC sweep of the output voltage Vo, 0–1 V | -I(Vo) at 0.5 V 9.9997 µA (Rout: see README) |
| `A6_proposed_dem_mirror_phase1_A_dc.asc` / `.net` | DC sweep of Iin, 0–20 µA | error at 10 µA -0.0035 %, at 2 µA -0.0041 %, V(inn) at 10 µA 0.175 V |
| `A6_proposed_dem_mirror_phase1_A_ac.asc` / `.net` | AC, input impedance and current-gain bandwidth | Rin at 1 kHz 0.06506 Ω, −3 dB bandwidth 409 MHz |
| `A6_proposed_dem_mirror_phase1_A_out.asc` / `.net` | DC sweep of the output voltage Vo, 0–1 V | -I(Vo) at 0.5 V 9.9996 µA (Rout: see README) |
| `A3_base_with_dem_chopped_A_chop.asc` / `.net` | Transient with the 500 kHz DEM clock, averaged output | averaged error -0.0057 %, V(inn) 0.231 V |
| `A6_proposed_dem_mirror_chopped_A_chop.asc` / `.net` | Transient with the 500 kHz DEM clock, averaged output | averaged error +0.0002 %, V(inn) 0.175 V |

Notes: the `_A_ac` deck gives Rin and bandwidth; for the chopped DEM decks the averaged current is the result and the
output shows short glitches at each clock edge. Rout values in the README come from an `.ac` drive on Vo with tight
tolerances; the `_A_out` slope (`rout_ohm`) is coarser.

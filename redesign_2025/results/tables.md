## Main table

| Design | Gain dBΩ | BW GHz | Power mW | Noise (avg over BW) pA/√Hz | Gain×BW THz·Ω | Worst peaking 45 PVT dB | BW range 45 PVT GHz | MC σ(BW) GHz, samples >1 dB | Eye opening mV | In-band dip (local min below DC gain), dB |
|---|---|---|---|---|---|---|---|---|---|---|
| `base_mdfrgc_robust` | 56.8 | 4.01 | 0.83 | 18.1 | 2.77 | 0.00 | 2.66 to 4.78 | 0.03, 0/200 | 13.4 of 13.8 | 0.0 |
| `base_mdfrgc_nominal` | 67.8 | 2.70 | 0.48 | 11.1 | 6.64 | 6.25 | 1.13 to 3.29 | 0.04, 0/200 | 46.0 of 51.9 | 2.3 |
| `ref_rgc_robust` | 56.0 | 3.53 | 0.80 | 17.3 | 2.23 | 0.00 | 2.52 to 4.12 | 0.01, 0/200 | 12.7 of 13.1 | 0.0 |
| `prop_mdfrgc_trim` | 67.6 | 2.76 | 0.55 | 12.3 | 6.64 | 8.28 | 1.10 to 4.07 | 0.46, 0/200 | 48.6 of 52.7 | 1.4 |
| `var_cmnrc_robust` | 55.5 | 3.09 | 1.03 | 20.4 | 1.85 | 0.91 | 2.15 to 4.14 | 0.12, 0/200 | 14.2 of 15.5 | 0.0 |
| `var_cmnrc_nominal` | 72.5 | 2.62 | 0.74 | 12.7 | 11.09 | 22.90 | 0.20 to 3.65 | 0.14, 2/200 | 87.4 of 95.1 | 1.9 |
| `var_cmrgc_robust` | 50.4 | 3.79 | 1.10 | 21.7 | 1.25 | 0.17 | 2.38 to 5.32 | 0.18, 0/200 | 6.7 of 7.6 | 0.0 |
| `ref_shaaban_L` | 58.4 | 4.74 | 1.49 | 13.4 | 3.93 | 0.00 | 0.48 to 5.08 | 1.85, 0/200 | 12.8 of 16.3 | 3.0 |
| `ref_shaaban_AN` | 54.4 | 2.55 | 1.24 | 30.1 | 1.34 | 1.27 | 1.44 to 3.24 | 0.06, 0/200 | 11.9 of 12.2 | 0.0 |
| `ref_shaaban_AP` | 56.5 | 2.54 | 1.23 | 20.3 | 1.70 | 1.58 | 1.14 to 3.83 | 0.06, 0/200 | 15.1 of 15.5 | 0.0 |
| `ref_pftia_earlier` | 67.2 | 2.66 | 0.39 | 15.4 | 6.10 | 4.20 | 1.03 to 3.60 | 0.73, 92/200 | 63.4 of 67.5 | 0.0 |

## Bandwidth / peaking vs photodiode capacitance (nominal corner)

| Design | Cpd 0.1 pF | 0.25 pF | 0.45 pF | 0.7 pF | 1.0 pF |
|---|---|---|---|---|---|
| `base_mdfrgc_robust` | 3.12 GHz / 0.0 dB | 3.73 GHz / 0.0 dB | 4.01 GHz / 0.0 dB | 3.71 GHz / 0.0 dB | 3.30 GHz / 0.0 dB |
| `base_mdfrgc_nominal` | 1.06 GHz / 0.0 dB | 1.20 GHz / 0.0 dB | 2.70 GHz / 0.0 dB | 2.41 GHz / 3.3 dB | 2.15 GHz / 6.3 dB |
| `ref_rgc_robust` | 3.47 GHz / 0.0 dB | 3.71 GHz / 0.0 dB | 3.53 GHz / 0.0 dB | 3.15 GHz / 0.0 dB | 2.75 GHz / 0.0 dB |
| `prop_mdfrgc_trim` | 1.07 GHz / 0.0 dB | 1.36 GHz / 0.0 dB | 2.76 GHz / 0.0 dB | 2.44 GHz / 3.7 dB | 2.13 GHz / 8.6 dB |
| `var_cmnrc_robust` | 3.16 GHz / 0.0 dB | 3.43 GHz / 0.0 dB | 3.09 GHz / 0.7 dB | 2.72 GHz / 1.6 dB | 2.39 GHz / 2.2 dB |
| `var_cmnrc_nominal` | 1.33 GHz / 0.0 dB | 1.68 GHz / 0.0 dB | 2.62 GHz / 0.0 dB | 2.28 GHz / 0.0 dB | 2.00 GHz / 0.0 dB |
| `var_cmrgc_robust` | 3.76 GHz / 0.0 dB | 4.13 GHz / 0.0 dB | 3.79 GHz / 0.0 dB | 3.32 GHz / 0.1 dB | 2.88 GHz / 0.3 dB |
| `ref_shaaban_L` | 7.91 GHz / 6.0 dB | 5.98 GHz / 2.1 dB | 4.74 GHz / 0.0 dB | 0.41 GHz / 0.0 dB | 0.26 GHz / 0.0 dB |
| `ref_shaaban_AN` | 4.55 GHz / 2.2 dB | 3.44 GHz / 1.5 dB | 2.55 GHz / 0.6 dB | 1.82 GHz / 0.0 dB | 1.23 GHz / 0.0 dB |
| `ref_shaaban_AP` | 4.63 GHz / 3.2 dB | 3.46 GHz / 1.9 dB | 2.54 GHz / 0.5 dB | 1.73 GHz / 0.0 dB | 0.98 GHz / 0.0 dB |
| `ref_pftia_earlier` | 2.09 GHz / 0.0 dB | 3.16 GHz / 0.0 dB | 2.66 GHz / 0.8 dB | 2.23 GHz / 2.0 dB | 1.91 GHz / 2.8 dB |

## Trimming

| prop_mdfrgc_trim, 45 conditions | Bandwidth GHz | Worst peaking dB | Gain dBΩ |
|---|---|---|---|
| vc fixed at 0.30 V | 1.10 to 4.07 | 8.26 | 67.6 to 67.6 |
| vc trimmed per condition (0.05 V grid) | 1.41 to 3.47 | 0.93 | 67.6 to 67.8 |

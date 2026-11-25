# Base paper and supporting papers

PDFs could not be downloaded from the build environment (the network proxy blocks the publishers),
so this folder holds citations and links only. Everything below was read as web text (abstracts, open-access
full text or catalogue records); the "what I could verify" column says how much of each paper was available.

## Base paper (reproduced in `../netlists/`, circuit `mdfrgc`)

| | |
|---|---|
| Paper | B. Abdollahi, B. Mesgari, S. Saeedi, Z. Sohrabi, H. Zimmermann, "Low-Noise Modified-RGC Transimpedance Amplifier With Bandwidth Enhancement Using an Intrinsic Negative-RC Network," *IEEE Access*, vol. 13, pp. 33521-33531, 2025. doi 10.1109/ACCESS.2025.3543679 |
| Open-access copy | https://repositum.tuwien.at/bitstream/20.500.12708/214116/1/Abdollahi-2025-IEEE%20Access-vor.pdf |
| Their result | 0.35 um X-FAB, 3.3 V, measured: about 69 dBohm, 1.7 GHz at Cin = 0.45 pF, 7.4 mW, about 6 pA/rtHz, 2 and 3 Gb/s eyes |
| What I could verify | Full text and equations (4)-(16). The schematic (Fig. 3) is an image, so the netlist is rebuilt from the equations: see `../README.md`, section "How the base paper was reproduced" |

## Supporting papers

| Paper | Link | What I could verify |
|---|---|---|
| A. M. Shaaban, S. M. Sharroush, Y. Abdalla, S. F. Nafea, "Design of a Novel CMOS Transimpedance Amplifier Based on a Current Mirror," *Int. J. Circuit Theory Appl.* 53(8), 4919-4934, 2025. doi 10.1002/cta.4353 | https://onlinelibrary.wiley.com/doi/10.1002/cta.4353 | Abstract and figure captions only (45 nm, 1 V, 1 pF; passive-inductor version 30.6 dB, 2.8 GHz, 1.63 mW, 23.55 pA/rtHz). The circuit in `shaaban_*` is a reconstruction, not their netlist |
| S. Zohoori, M. Dolatshahi, M. Pourahmadi, M. Hajisafari, "A CMOS, low-power current-mirror-based transimpedance amplifier for 10 Gbps optical communications," *Microelectron. J.* 80, 18-27, 2018. doi 10.1016/j.mejo.2018.08.001 | https://www.researchgate.net/publication/327993968 | Abstract only (90 nm, 1 V: 40.5 dBohm, 7 GHz, 20.3 pA/rtHz, 1.4 mW). Not reproduced |
| M. S. H. Alsheikhjader, A. A. Issa, "A Simulated 45 nm MOSFET Channel Process in Transimpedance Amplifier Design for Optoelectronics Applications," *Jordan J. Phys.* 17(2), 165-178, 2024. doi 10.47011/17.2.4 | https://jjp.yu.edu.jo/index.php/jjp/article/download/328/96/1385 | Full text, but no node-level schematic or bias values. Not reproduced |
| B. Abdollahi et al., "Inductor-Less Low-Power Low-Voltage Cross-Coupled Regulated-Cascode TIA," *IEEE Access* 12, 147106-147114, 2024. doi 10.1109/ACCESS.2024.3474788 | https://ieeexplore.ieee.org/document/10706244/ | Abstract only (0.35 um: 60 dBohm, 1.8 GHz, 9.2 pA/rtHz, 2.2 mW) |
| Y. Takahashi et al., "Low-Power Regulated Cascode CMOS Transimpedance Amplifier with Local Feedback Circuit," *Electronics* 11(6), 854, 2022. doi 10.3390/electronics11060854 | https://www.mdpi.com/2079-9292/11/6/854 | Abstract and topology text (65 nm, 1 V, 46 dBohm, 11.4 GHz, 23.9 mW) |
| S. Park et al., "A CMOS Inverter-Based Active Feedback Transimpedance Amplifier," *Photonics* 11, 617, 2024. doi 10.3390/photonics11070617 | https://dspace.ewha.ac.kr/bitstream/2015.oak/269396/1/photonics-11-00617-v2.pdf | Full text, no netlist |
| J. C. Garcia-Montesdeoca et al., "High Gain, Low Noise and Power TIA Based on Second Generation Voltage Conveyor in 65 nm CMOS," *Sensors* 22, 5997, 2022. doi 10.3390/s22165997 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9414398 | Full text; sizes of 20 devices but no connections |
| Earlier work in this repo | `../../paper/`, `../../docs/Literature_Review.md` | Complete |

Reconstructed circuits are labelled as such everywhere in this folder. Numbers quoted from papers are the authors' own,
at their technology nodes; the simulations here are PTM 90 nm at 1 V and are not directly comparable.

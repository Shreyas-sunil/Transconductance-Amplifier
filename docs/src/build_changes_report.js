// Builds docs/Design_Changes_Report.docx from results/numbers.json and results/summary.json
const fs = require('fs'), path = require('path');
const D = require('docx');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, HeadingLevel, ImageRun,
        AlignmentType, LevelFormat, BorderStyle, Footer, PageNumber } = D;
const ROOT = path.resolve(__dirname, '..', '..');
const N = JSON.parse(fs.readFileSync(path.join(ROOT, 'results', 'numbers.json')));
const S = JSON.parse(fs.readFileSync(path.join(ROOT, 'results', 'summary.json')));
const FIG = f => path.join(ROOT, 'paper', 'figures', f);
const W = 9026;  // A4 text width in DXA with 1" margins
const INK = '1F1F1E', MUTED = '5F5E5A', HEAD = 'E8EEF7';

const P = (t, o = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, ...o,
  children: (Array.isArray(t) ? t : [t]).map(x => typeof x === 'string' ? new TextRun({ text: x }) : x) });
const B = t => new TextRun({ text: t, bold: true });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const LI = t => new Paragraph({ numbering: { reference: 'bul', level: 0 }, spacing: { after: 80, line: 276 },
  children: (Array.isArray(t) ? t : [t]).map(x => typeof x === 'string' ? new TextRun(x) : x) });
const NUM = t => new Paragraph({ numbering: { reference: 'num', level: 0 }, spacing: { after: 80, line: 276 }, children: [new TextRun(t)] });
const border = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, rows, header = true) {
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ tableHeader: header && i === 0, children: r.map((c, j) => new TableCell({
      width: { size: widths[j], type: WidthType.DXA }, borders, margins: { top: 60, bottom: 60, left: 90, right: 90 },
      shading: header && i === 0 ? { type: ShadingType.CLEAR, fill: HEAD, color: 'auto' } : undefined,
      children: String(c).split('\n').map(line => new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: line, bold: header && i === 0, size: 19 })] })) })) })) });
}
function img(file, wpx, ratio, caption) {
  return [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
            children: [new ImageRun({ type: 'png', data: fs.readFileSync(FIG(file)), transformation: { width: wpx, height: Math.round(wpx * ratio) } })] }),
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: caption, italics: true, size: 18, color: MUTED })] })];
}
const sz = S.sizes, wl = k => `${sz[k][0]} µm / ${sz[k][1]} nm`;
const pv = S.pvt, mc = S.mc;

const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun('Design Changes Report')] }),
  P([new TextRun({ text: 'Tunable active-inductor feedback for the 90 nm current-mirror transimpedance amplifier', size: 26, color: MUTED })]),
  P([new TextRun({ text: 'What was changed in the reference circuit, why, and what each change did. All numbers are ngspice 42 simulations with the 90 nm PTM BSIM4 model at 1 V and 35 °C, with a 50 fF photodiode and a 30 fF load unless stated.', color: MUTED })], { spacing: { after: 240 } }),

  H1('1. Result in one table'),
  table([3000, 2000, 2000, 2026], [
    ['Metric', 'Reference (re-simulated)', 'Proposed', 'Change'],
    ['Transimpedance gain', `${N.BZt} dBΩ (${N.BZtOhm} Ω)`, `${N.PZt} dBΩ (${N.PZtOhm} Ω)`, `+${N.GainImp} dB`],
    ['Response shape', `${N.BPk} dB peak at ${N.BFpk} GHz`, `${N.PPk} dB peaking`, 'resonance removed'],
    ['Usable bandwidth', `${N.BFlat} GHz (±1 dB flat)`, `${N.PBW} GHz (−3 dB)`, ''],
    ['Bandwidth tuning', 'none', `${N.TuneMin} to ${N.TuneMax} GHz`, 'one control voltage'],
    ['Input noise at 5 GHz', `${N.BInFive} pA/√Hz`, `${N.PInFive} pA/√Hz`, `${N.NoiseRatio}× lower`],
    ['Power', `${N.BPow} mW`, `${N.PPow} mW`, `−${N.PowSave} %`],
    ['Feedback element', '2.4 nH spiral', '2 transistors + 30 fF', `about ${N.AreaRatio}× smaller (estimate)`],
    ['Eye opening, 10 Gb/s, 100 µA', `${N.EyeBTenH} mV`, `${N.EyePTenH} mV`, ''],
  ]),
  P(''),
  P([B('Read this first. '), 'The reference numbers above are not the ones printed in the 2020 paper. They are what the published schematic produces when it is simulated with a BSIM4 model. Section 2 explains the difference. The proposed circuit also has real costs, listed in Section 5; the main one is that its input overloads at a few tens of microamperes of average photocurrent.']),

  H1('2. What the reference circuit does in BSIM4'),
  ...img('schem_baseline.png', 380, 601 / 993, 'Figure 1. Reference circuit (Alsheikhjader 2020, Fig. 1) as drawn.'),
  P('The published schematic ties the gates of M1 and M2b to VDD. With a model that enforces the threshold voltage this has three consequences.'),
  LI([B('M2b is off. '), `Its gate-source voltage is zero, so it conducts only ${N.BIOne} nA of leakage.`]),
  LI([B('M1 is a switch, not an amplifier. '), `With no bias current it sits in deep triode (channel conductance ${N.BGdsOne} mS) and simply ties node N to the input. M2 is then diode-connected through M1 and the inductor.`]),
  LI([B('The gain is 1/(2gm), then a resonance. '), `At low frequency the gain is 1/(gm2 + gm3 + gds2 + gds3 + gds3b) = ${N.BZtOhm} Ω, which matches the simulation exactly. As the inductor impedance rises the feedback is removed, the gain rises, and the 2.4 nH inductor resonates with the node capacitances at ${N.BFpk} GHz with an ${N.BPk} dB peak.`]),
  P(`The published paper shows about 157 Ω flat from 5 to 15 GHz with no peak and 10 to 16 pA/√Hz noise. The re-simulation gives ${N.BZtOhm} Ω, a strong peak, and ${N.BInTen} to ${N.BInOne} pA/√Hz. With the M3b gate at the −1 V shown in the published figure the result is ${N.BMZt} dBΩ and ${N.BMPow} mW, which is further from the published curve, not closer. Section 2A locates the cause.`),
  H1('2A. Why the published curve cannot be reproduced'),
  P('Each hypothesis was tested by fitting the two unpublished quantities (photodiode and load capacitance, 5 fF to 2 pF) to the twelve digitised published points and reading the remaining error.'),
  table([5400, 3626], [
    ['Hypothesis', 'Best rms error'],
    ['As drawn, 50 fF / 30 fF', `${N.DgRmsDrawn} dB`],
    ['As drawn, capacitances free', `${N.DgRmsFitDrawn} dB`],
    ['M3b gate at −1 V, as labelled', `${N.DgRmsMOne} dB`],
    ['M2b gate grounded (M1 gets bias current)', `${N.DgRmsMTwoB} dB`],
    ['Lossy spiral, 15 Ω series', `${N.DgRmsLoss} dB`],
    ['Everything free with 2.4 nH: both gate biases, loss up to 110 Ω, both capacitances', `${N.DgRmsBestL} dB, still resonant`],
    [`Feedback inductance free (best below about ${N.DgLfMax} pH)`, `${N.DgRmsNoL} dB`],
  ]),
  P(''),
  P(`With the stated 2.4 nH the response must rise before the capacitances roll it off, because the low-frequency gain is 1/(gm2 + gm3) and the inductor removes that feedback as frequency rises. A bias sweep of both PMOS gates (${N.DgNScreen} points) never brought the peak below ${N.DgPkMin} dB. The published curve falls steadily from 203 Ω, which only happens if the feedback reactance stays negligible. The best match has under about ${N.DgLfMax} pH of feedback inductance and about ${N.DgIdNoL} µA per mirror branch (M3b gate at ${N.DgVgNoL} V), a fifth of the drawn bias. So the published response is that of the circuit without effective inductive feedback, at a lower bias than drawn. A unit error on the inductor, or an inductor left out of the signal path, would do this, but only the original simulation files could confirm it. The paper's own transfer function (its Eq. 9) also disagrees with its plot: it gives about ${N.DgEqNine} Ω at 1 GHz, not 203 Ω.`),
  ...img('fig_baseline_diagnosis.png', 600, 801 / 2279, 'Figure 2A. (a) Best fits to the published curve. (b) Fit error against feedback inductance. (c) Baseline as drawn, re-optimised baselines and proposed TIA.'),
  H1('2B. A fair reference'),
  P('Comparing against a circuit whose common-gate device is in triode overstates the improvement. The baseline topology was re-optimised with the same search and constraints as the proposed TIA (50/30 fF, at most 1 dB peaking, at most 1.2 mW), with the widths, both PMOS gate biases, the inductance (0.2 to 6 nH) and a series loss up to 60 Ω free.'),
  table([2900, 2042, 2042, 2042], [
    ['Metric', 'Baseline re-opt., max GBW', 'Baseline re-opt., same gain', 'Proposed'],
    ['Gain', `${N.RbZt} dBΩ`, `${N.RgZt} dBΩ`, `${N.PZt} dBΩ`],
    ['Bandwidth', `${N.RbBw} GHz`, `${N.RgBw} GHz`, `${N.PBW} GHz`],
    ['Power', `${N.RbPow} mW`, `${N.RgPow} mW`, `${N.PPow} mW`],
    ['Noise at 5 GHz', `${N.RbInFive} pA/√Hz`, `${N.RgInFive} pA/√Hz`, `${N.PInFive} pA/√Hz`],
    ['Gain × bandwidth', `${N.RbGbw} TΩHz`, `${N.RgGbw} TΩHz`, `${N.PGbw} TΩHz`],
    ['Feedback element', `${N.RbLf} nH + ${N.RbRs} Ω`, `${N.RgLf} nH + ${N.RgRs} Ω`, 'active, tunable'],
  ]),
  P(''),
  P(`At the same gain the proposed circuit has ${N.BwRatioGain}× the bandwidth. The baseline topology is better on power and noise density, and at its own best point it has a slightly higher gain-bandwidth product than the proposed circuit at a quarter of the power. The improvements in Section 1 are against the circuit as drawn; this table is the comparison to use when arguing for the design.`),
  ...img('fig_baseline_reproduction.png', 560, 848 / 2136, 'Figure 2. Reference circuit re-simulated in BSIM4 against points digitised from the published figures.'),
  H2('Issues in the published analysis that this work resolves'),
  table([2600, 6426], [
    ['Issue in the 2020 paper', 'How it is handled here'],
    ['Bandwidth quoted as 5–15 GHz in one place and 10–15 GHz in another', 'One definition is used everywhere: the first frequency at which the gain is 3 dB below its 100 MHz value. For the peaking reference, the ±1 dB flatness limit is reported instead.'],
    ['Low-frequency −3 dB point never identified', 'Both circuits are DC-coupled and flat down to 10 MHz, the lowest simulated frequency; there is no lower corner.'],
    ['Output-impedance equation is dimensionally inconsistent', `Re-derived for the as-drawn circuit: Zout = 1 / [go + (gm2 + gds2 + gm3) / (1 + (gm2 + gds2)·Zf)]. At low frequency this is ${N.ZoutBF} Ω; simulation gives ${N.ZoutB} Ω. It peaks at ${N.ZoutBMax} Ω at the resonance.`],
    ['Power, photodiode capacitance and load not reported', `Stated and fixed: CPD = 50 fF, CL = 30 fF, and power is reported for every case (${N.BPow} mW reference, ${N.PPow} mW proposed).`],
  ]),

  H1('3. The proposed circuit'),
  ...img('schem_proposed.png', 470, 601 / 1183, 'Figure 3. Proposed circuit. Vb1 and Vbp come from a small bias generator (50 µA reference).'),
  table([1800, 2400, 4826], [
    ['Device', 'Size (W / L) or value', 'Role'],
    ['M1', wl('M1'), 'Common-gate input device, now in saturation'],
    ['M2', wl('M2'), 'Mirror input; with M1 forms a flipped voltage follower'],
    ['M3', wl('M3'), 'Mirror output'],
    ['M3b', wl('M3b'), 'PMOS current-source load, mirrored from the reference'],
    ['Mf', wl('Mf'), 'Feedback source follower (the active-inductor transistor)'],
    ['Mt', wl('Mt'), 'PMOS triode device = tunable resistor Rt, gate = Vtune'],
    ['Ca', '30 fF', 'Gate-source capacitor of Mf; sets the tuning range'],
    ['RN', '5 kΩ', 'Load at node N (replaces M2b)'],
    ['Mbp, Mbr, Mbn, Rb', `${wl('Mbp')}, ${wl('Mbr')}, ${wl('Mbn')}, 4.2 kΩ`, 'Bias generator for Vbp and Vb1'],
  ]),

  H1('4. Change log: what, why, effect'),
  table([420, 2300, 3053, 3253], [
    ['#', 'Change', 'Why', 'Measured effect'],
    ['1', 'M2b (PMOS with gate at VDD) replaced by resistor RN = 5 kΩ', 'M2b was off, which starved M1 of current. A resistor needs no bias voltage, adds no capacitance and damps the local loop.', `M1 now carries ${N.IOne} µA in saturation (gm = ${N.GmOne} mS). Node N sits at ${N.Vn} V.`],
    ['2', 'M1 gate moved from VDD to Vb1 = 0.71 V (replica bias)', 'With the gate at VDD the input sat at 0.50 V, which leaves no headroom for a feedback transistor at a 1 V supply.', `Input level drops from ${N.BVin} V to ${N.Vin} V. M1 and M2 form a flipped voltage follower with low input resistance; local-loop phase margin is ${N.LoopPMl}° or more.`],
    ['3', 'M3b gate moved from a fixed −1 V / 0 V source to a mirror of a 50 µA reference', 'A fixed gate voltage makes the current depend directly on VDD and threshold voltage, and −1 V over-stresses a 1 V device.', `Output-branch current is ${N.IThree} µA and tracks the reference. Total supply current falls from 1322 µA to ${N.ITot} µA.`],
    ['4', 'Spiral Lf = 2.4 nH replaced by source follower Mf with gate network Mt + Ca', 'Remove the spiral (area, fixed value, resonance) and gain a control knob. The follower’s gate-source drop fits because of change 2.', `Gain ${N.PZt} dBΩ, no resonance (${N.PPk} dB peaking), −3 dB at ${N.PBW} GHz. Estimated area of the feedback element about ${N.AIArea} µm² against ${N.SpiralArea} mm² for the spiral.`],
    ['5', 'Tuning voltage Vtune on the gate of Mt', 'Rt sets how quickly the feedback is removed with frequency, which sets bandwidth and peaking. No DC current flows in Mt, so tuning does not move the bias point.', `Rt from ${N.RtMin} Ω to ${N.RtMaxOne} Ω moves the bandwidth from ${N.TuneMin} to ${N.TuneMax} GHz with under 1 dB peaking and unchanged gain.`],
    ['6', 'Devices resized: M1 5→4.5 µm, M2 5→3.5 µm, M3 5→7 µm, M3b 5 µm/90 nm → 28 µm/180 nm', 'Chosen by a constrained search (bandwidth maximised for ≥53 dBΩ, ≤1 dB peaking, ≤1.2 mW, all devices saturated). A longer M3b raises the output resistance; a mirror ratio above one raises the gain.', `Mirror gain gm3/gm2 = ${N.Mratio}, output resistance ${N.Ro} Ω, loop gain ${N.LoopTzero} dB.`],
    ['7', 'Test conditions fixed and stated', 'The 2020 paper gives no photodiode or load capacitance, so results could not be compared.', 'CPD = 50 fF and CL = 30 fF everywhere; sensitivity to both is reported (Section 6).'],
  ]),
  P(''),
  H2('How the active inductor works'),
  P(`Seen from the input, Mf with its gate network has impedance (1 + s·Rt·Cg) / (gf + s·Cg). At low frequency it is a resistance 1/gf = ${N.AIRs} Ω. If Rt is larger than 1/gf the impedance rises with frequency, which is inductive behaviour; if Rt is smaller, it falls. In simulation Vtune moves the element from capacitive (below about 0.27 V) to inductive (above). Simulated on its own, the equivalent inductance at 1 GHz is ${N.AILB} nH at 0.32 V, ${N.AILC} nH at 0.36 V and ${N.AILD} nH at 0.40 V, with a quality factor of at most ${N.AIQD}. It is a very lossy inductor and is used as a tunable zero, not as a resonator.`),
  ...img('fig_vtune_tuning.png', 560, 997 / 2138, 'Figure 4. Response of the proposed circuit as Vtune is swept.'),

  H1('5. What got worse, and what the change does not do'),
  P('These are simulation results too, and they belong in any paper written from this work.'),
  LI([B('Input overload (fixed in Section 5A). '), `Mf carries only ${N.IF} µA, and photocurrent displaces it. Without the DC-cancellation loop the gain rises by ${N.OvA} dB at 25 µA of DC input current and ${N.OvB} dB at 50 µA (bandwidth down to ${N.OvBwB} GHz); the feedback is lost near 100 µA.`]),
  LI([B('No bandwidth gain at light load. '), `With the gate of Mf tied straight to the output and no Ca, the bandwidth is ${N.LdResLight} GHz, higher than the ${N.LdAiLight} GHz of the tunable network. The network pays about 16 % of bandwidth for tunability. It only extends bandwidth when the load is heavy: ${N.LdRatioMid}× at 150 fF and ${N.LdRatioHeavy}× at 250 fF.`]),
  LI([B('Trimming cannot recover a slow corner. '), `Vtune removes peaking and pulls fast corners back, but at SS, 0.9 V, 85 °C the bandwidth stays at ${pv.rows[13].f3_trim.toFixed(2)} GHz.`]),
  LI([B('The feedback network adds noise. '), `Mf and Mt together contribute ${Number(N.NsMf) + Number(N.NsMt)} % of the output noise power at 5 GHz. The total is still lower than the reference because the triode M1 of the reference alone contributed ${N.NsBMOne} %.`]),
  LI([B('More parts. '), 'Seven extra devices (Mf, Mt, Ca, RN and the bias generator) and a 2 pF decoupling capacitor. The bias generator uses 97 µA.']),
  LI([B('Tight headroom on M3b. '), 'Its saturation margin is 37 mV at the nominal point.']),

  H1('5A. Change 7: DC-cancellation loop'),
  P('What collapses under average photocurrent is the follower current I(Mf), which appears as VGS(Mf) = VOUT − VIN. Holding VOUT at a fixed reference does not work, because the dark output level moves by 80 mV over the PVT conditions. The loop therefore regulates I(Mf) directly.'),
  LI([B('Replica. '), 'Mr, half the width of Mf, driven from VOUT and biased at Ith/2 from the bias generator, gives VR = VOUT − VGS(Ith).']),
  LI([B('Comparison. '), 'A five-transistor OTA with a PMOS input pair compares VR with VIN, both taken through 100 kΩ / 0.2 pF taps, and integrates the difference on Cint = 2 pF.']),
  LI([B('Cancellation. '), 'The OTA output drives Mdc (6 µm / 180 nm), which sinks the excess photocurrent from the input.']),
  LI([B('Threshold. '), `Ith ≈ 105 µA, just above the dark follower current. A first version with Ith below the dark current failed Monte Carlo: the dark I(Mf) is a difference of two larger currents (σ = ${N.DcMcImfDarkStd} µA), and low samples were held far below nominal. Vtune is re-centred to 0.26 V.`]),
  ...img('schem_dcc.png', 480, 0.56, 'Figure 5A. DC-cancellation loop.'),
  table([4200, 2413, 2413], [
    ['Metric', 'Without loop', 'With loop'],
    ['Photocurrent with gain within 1 dB and bandwidth within 10 %', `${N.PrLimit} µA`, `${N.DcLimit} µA`],
    ['Bandwidth at 100 µA', `${N.PrBwHundred} GHz`, `${N.DcBwHund} GHz`],
    ['Bandwidth at 300 µA', 'feedback lost', `${N.DcBwThree} GHz`],
    ['Dark gain and bandwidth', `${N.PZt} dBΩ, ${N.PBW} GHz`, `${N.DcZtDark} dBΩ, ${N.DcBwDark} GHz`],
    ['Noise at 5 GHz, dark', `${N.PInFive} pA/√Hz`, `${N.DcInFive} pA/√Hz (+${N.DcNoisePct} %)`],
    ['Power', `${N.PPow} mW`, `${N.DcPow} mW (+${N.DcPowAdd} µW)`],
    ['Eye opening at 10 Gb/s, 100 µA average', `${N.PrEyeHund} %`, `${N.DcEyeHund} %`],
    ['Loop phase margin; low-frequency corner', '—', `≥ ${N.DcPmMin}°; ${N.DcFloDark} kHz to ${N.DcFloMax} MHz`],
    ['Step 0 → 200 µA', `drops ${N.PrDrop} mV and stays`, `dips ${N.DcDip} mV, back within ${N.DcErr} mV in ${N.DcSettle} µs`],
  ]),
  P(''),
  ...img('fig_dcc.png', 560, 1478 / 2122, 'Figure 5B. (a) Bandwidth and gain against average photocurrent. (b) Currents. (c) Step response. (d) Transimpedance with the loop.'),
  P(`Corners: the dark cancellation current stays under ${N.DcPvtIdccMax} µA in all ${N.DcPvtN} conditions, and at 300 µA the bandwidth is at least ${N.DcPvtBwMinB} GHz except at SS, 0.9 V, 85 °C (${N.DcPvtBwMin} GHz). Monte Carlo (${N.DcMcN} samples, mismatch only): bandwidth at 300 µA ${N.DcMcBwMean} ± ${N.DcMcBwStd} GHz, minimum ${N.DcMcBwMin} GHz; held current σ = ${N.DcMcImfStd} µA. ${N.DcMcPkN} samples peak above 1 dB untrimmed (worst ${N.DcMcPkMax} dB); a Vtune trim brings every one under 1 dB with at least ${N.DcTrBwMin} GHz dark and ${N.DcTrBwThree} GHz at 300 µA.`),
  P('Cost: ten transistors, two resistors and 2.4 pF of capacitance (about 240 µm² as MOS capacitors at an assumed 10 fF/µm²). The reference current is ideal in simulation; the slow-corner result depends on it, so a bandgap-derived reference is needed.'),

  H1('6. Robustness'),
  ...img('fig_pvt.png', 560, 1067 / 2134, 'Figure 5. Fifteen process, voltage and temperature conditions, with Vtune fixed and trimmed.'),
  table([4513, 2256, 2257], [
    ['Quantity over 15 PVT conditions', 'Vtune fixed at 0.28 V', 'Vtune trimmed'],
    ['Bandwidth range', `${N.PvtBwMin} to ${N.PvtBwMax} GHz`, `${N.PvtBwTMin} to ${N.PvtBwTMax} GHz`],
    ['Worst peaking', `${N.PvtPkMax} dB`, `${N.PvtPkTMax} dB`],
    ['Gain range', `${N.PvtZtMin} to ${N.PvtZtMax} dBΩ`, 'unchanged'],
    ['Power range', `${N.PvtPMin} to ${N.PvtPMax} mW`, 'unchanged'],
  ]),
  P(''),
  ...(mc ? [P(`Monte Carlo, ${N.McN} samples (global variation plus Pelgrom mismatch with assumed coefficients): with Vtune fixed the bandwidth is ${N.McBwMean} ± ${N.McBwStd} GHz and the worst peaking is ${N.McPkMax} dB (${N.McPkYieldFixed} % of samples under 1 dB). With trimming the bandwidth is ${N.McBwTMean} ± ${N.McBwTStd} GHz, the worst peaking is ${N.McPkTMax} dB and every sample is under 1 dB. Gain is ${N.McZtMean} ± ${N.McZtStd} dBΩ.`)] : []),
  P(`Stability: the global loop has ${N.LoopTzero} dB of low-frequency gain and at least ${N.LoopPMg}° of phase margin. The local M1–M2 loop is the limiting one: ${N.LoopPMl}° at 50 fF and ${N.LoopPMlCpd}° at 200 fF of photodiode capacitance.`),
  P(`Photodiode capacitance: with Vtune fixed, peaking grows with CPD. Lowering Vtune keeps it under 1 dB up to 200 fF, at about 7.4 GHz.`),
  P(`Sensitivity estimate: ${N.PIrmsTot} µA rms total input-referred noise gives a minimum input swing of ${N.SensIpp} µA peak to peak for a bit-error ratio of 1e-12, or ${N.SensdBm} dBm average optical power at an assumed 0.8 A/W.`),

  H1('7. Files to simulate'),
  table([3300, 5726], [
    ['File', 'Use'],
    ['netlists/ngspice/proposed_tia.cir, baseline_tia.cir', 'Run with: ngspice -b proposed_tia.cir. Prints the operating point, gain, peak and −3 dB frequency, and writes AC and noise data. These are the files every number in this report came from.'],
    ['netlists/*/proposed_tia_dcc.*', 'Proposed TIA with the DC-cancellation loop, in ngspice, LTspice (.net and .asc) and Spectre. Parameter idc is the average photocurrent; the Spectre file adds an idc sweep and a photocurrent step.'],
    ['netlists/*/baseline_reopt_gain.*, baseline_reopt_gbw.*', 'The two re-optimised baselines used as the fair reference, in all three simulators.'],
    ['scripts/baseline_diag.py, dcc_study.py', 'The baseline diagnosis and fair re-optimisation, and the DC-cancellation characterisation.'],
    ['netlists/ltspice/*.net', 'Open in LTspice (File > Open, All files) and run. Same circuit and model. Not run here: LTspice is not available in the environment that produced this report.'],
    ['netlists/ltspice/*.asc + tia_nmos4.asy, tia_pmos4.asy', 'LTspice schematics of both circuits. Nets are joined by label. Connectivity was checked against the netlist by script, but the files have not been opened in LTspice.'],
    ['netlists/cadence/*.scs', 'Spectre netlists: spectre proposed_tia.scs. Includes AC, noise and a Vtune sweep. Not run here.'],
    ['netlists/cadence/build_tia_schematics.il', 'SKILL script that builds all five schematics in Virtuoso from analogLib parts: load it in the CIW and call tiaBuildAll("YOUR_LIB"). Not run here; expect to tidy the placement.'],
    ['scripts/run_all.py, make_figures.py', 'Regenerate every result and figure.'],
    ['models/ptm90.lib', '90 nm PTM BSIM4 card (models renamed nmos90 / pmos90).'],
  ]),
  P(''),
  H1('8. Before you submit'),
  NUM('Re-run the Spectre netlists in Cadence and compare with the ngspice numbers; small differences in BSIM4 version handling are possible.'),
  NUM('Replace the ideal reference current with a bandgap-derived one and re-check the DC-cancellation threshold at the slow corner.'),
  NUM('Move to a foundry kit if you have access (the PTM card has no corners, mismatch data or layout rules), lay out the circuit and repeat the key results post-layout.'),
  NUM('Check every reference against the original paper (see docs/Literature_Review.md for the ones flagged).'),
  NUM('Have your supervisor review Sections 2, 2A and 2B before they go into a manuscript, since they differ from a published paper. Consider contacting the original author for the simulation settings.'),
];

const doc = new Document({
  creator: 'Shreyas S', title: 'Design Changes Report',
  styles: { default: { document: { run: { font: 'Arial', size: 21, color: INK } },
      title: { run: { font: 'Arial', size: 44, bold: true, color: INK }, paragraph: { spacing: { before: 0, after: 80 } } },
      heading1: { run: { font: 'Arial', size: 28, bold: true, color: '1C3D6E' }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true } },
      heading2: { run: { font: 'Arial', size: 23, bold: true, color: INK }, paragraph: { spacing: { before: 220, after: 100 }, keepNext: true } } } },
  numbering: { config: [
    { reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: 'num', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] } ] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 16, color: MUTED })] })] }) },
    children }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(path.join(ROOT, 'docs', 'Design_Changes_Report.docx'), b); console.log('wrote Design_Changes_Report.docx'); });

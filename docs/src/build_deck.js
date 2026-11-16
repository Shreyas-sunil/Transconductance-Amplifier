// Builds docs/Project_Presentation.pptx from results/numbers.json and the paper figures
const fs = require('fs'), path = require('path');
const pptxgen = require('pptxgenjs');
const sharp = require('sharp');
const SK = process.env.PPTX_THEME_DIR || path.join(__dirname, 'pptx');  // folder containing scripts/apply_theme.js
const ROOT = path.resolve(__dirname, '..', '..');
const N = JSON.parse(fs.readFileSync(path.join(ROOT, 'results', 'numbers.json')));
const S = JSON.parse(fs.readFileSync(path.join(ROOT, 'results', 'summary.json')));
const FIG = f => path.join(ROOT, 'paper', 'figures', f);
const THEME = { name: 'TIA', headFontFace: 'Cambria', bodyFontFace: 'Calibri',
  colors: { dk1: '14213D', lt1: 'FFFFFF', dk2: '3A4763', lt2: 'EEF1F6', accent1: '1F6F8B', accent2: 'E76F24', accent3: '2A9D8F',
            accent4: 'C9A227', accent5: '6C5B9E', accent6: '8A94A6', hlink: '1F6F8B', folHlink: '6C5B9E' } };

(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE';                       // 13.33 x 7.5 in
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = 'Tunable active-inductor feedback TIA in 90 nm CMOS'; pres.author = 'Shreyas S';
  const C = pres.SchemeColor;
  pres.defineSlideMaster({ title: 'Dark', background: { color: THEME.colors.dk1 },
    objects: [{ placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 2.2, w: 11.7, h: 1.8, fontSize: 40, bold: true, color: C.background1, align: 'left', valign: 'top' }, text: '' } },
              { placeholder: { options: { name: 'body', type: 'body', x: 0.8, y: 4.2, w: 11.7, h: 1.6, fontSize: 18, color: C.background2, align: 'left', valign: 'top' }, text: '' } }] });
  pres.defineSlideMaster({ title: 'Content', background: { color: THEME.colors.lt1 }, slideNumber: { x: 12.3, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: C.accent6 },
    objects: [{ placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.35, w: 12.1, h: 0.95, fontSize: 30, bold: true, color: C.text1, align: 'left', valign: 'middle' }, text: '' } },
              { text: { text: 'Tunable active-inductor TIA · 90 nm PTM · simulation', options: { x: 0.6, y: 6.95, w: 8, h: 0.3, fontSize: 10, color: C.accent6, isTextBox: true, margin: 0 } } }] });
  const dims = async f => { const m = await sharp(FIG(f)).metadata(); return m.height / m.width; };
  async function pic(slide, f, x, y, w, maxH, name) {
    const r = await dims(f); let h = w * r, ww = w;
    if (maxH && h > maxH) { h = maxH; ww = h / r; }
    slide.addImage({ path: FIG(f), x: x + (w - ww) / 2, y, w: ww, h, objectName: name || f, altText: name || f });
    return h;
  }
  const T = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, color: C.text1, fontSize: 16, valign: 'top', ...o });
  function stat(slide, x, y, w, big, label, col) {
    slide.addShape(pres.ShapeType.roundRect, { x, y, w, h: 1.45, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: 'card ' + label });
    T(slide, big, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.75, fontSize: 30, bold: true, color: col || C.accent1, fontFace: THEME.headFontFace, valign: 'middle' });
    T(slide, label, { x: x + 0.2, y: y + 0.92, w: w - 0.4, h: 0.45, fontSize: 13, color: C.text2 });
  }
  const bullets = (slide, items, o) => slide.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 10 } })),
    { isTextBox: true, margin: 0, color: C.text1, fontSize: 16, valign: 'top', ...o });
  let s;

  pres.addSection({ title: 'Overview' });
  s = pres.addSlide({ masterName: 'Dark', sectionTitle: 'Overview' });
  s.addText('An inductorless, bandwidth-tunable current-mirror TIA with active-inductor feedback', { placeholder: 'title' });
  s.addText([{ text: '90 nm CMOS (PTM BSIM4), 1 V supply · schematic-level simulation study', options: { breakLine: true } }, { text: 'Shreyas S · R V College of Engineering' }], { placeholder: 'body' });
  s.addNotes('Project overview. Everything shown is simulation with a predictive model; no layout or silicon.');

  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Overview' });
  s.addText('The starting point: a TIA that needs a 2.4 nH spiral', { placeholder: 'title' });
  bullets(s, ['Reference: Alsheikhjader, Rafidain J. Sci. 2020. Common-gate input, current mirror, and a 2.4 nH inductor from output back to input.',
              'Published claim: 43.92 dBΩ, flat from 5 to 15 GHz, 10–16 pA/√Hz, at 1 V in 90 nm.',
              'A spiral of that value is far larger than all the transistors together, cannot be tuned after fabrication, and has a low quality factor on silicon.',
              'Question: can an active inductor take its place at 1 V, and what does it cost?'], { x: 0.6, y: 1.6, w: 6.0, h: 4.9 });
  await pic(s, 'schem_baseline.png', 7.0, 1.6, 5.7, 4.6, 'Reference schematic');
  s.addNotes('The reference paper does not report power, photodiode capacitance, load or device model.');

  pres.addSection({ title: 'Reference re-examined' });
  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Reference re-examined' });
  s.addText('In BSIM4 the reference circuit gives a resonance, not a flat band', { placeholder: 'title' });
  stat(s, 0.6, 1.6, 2.9, `${N.BZt} dBΩ`, 'low-frequency gain (published: 43.9)', C.accent2);
  stat(s, 0.6, 3.25, 2.9, `${N.BPk} dB`, `peak at ${N.BFpk} GHz`, C.accent2);
  stat(s, 0.6, 4.9, 2.9, `${N.BIOne} nA`, 'bias current in M1: it is a triode switch', C.accent2);
  await pic(s, 'fig_baseline_reproduction.png', 3.9, 1.6, 8.8, 3.6, 'Reference re-simulation');
  T(s, 'With the gates of M1 and M2b at VDD, M2b is off and M1 has no current. The gain is 1/(gm2 + gm3 + …) = ' + N.BZtOhm + ' Ω until the inductor resonates.', { x: 3.9, y: 5.35, w: 8.8, h: 1.2, fontSize: 14, color: C.text2 });
  s.addNotes('Points from the published figures are digitised and approximate.');

  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Reference re-examined' });
  s.addText('The published curve is the circuit without its inductor', { placeholder: 'title' });
  await pic(s, 'fig_baseline_diagnosis.png', 0.6, 1.55, 12.1, 3.9, 'Baseline diagnosis');
  bullets(s, [`With 2.4 nH, nothing fits better than ${N.DgRmsBestL} dB rms (any bias, spiral loss, capacitance), and it always resonates.`,
              `Below about ${N.DgLfMax} pH of feedback inductance, at a fifth of the drawn bias, the fit is ${N.DgRmsNoL} dB rms.`,
              `Fair reference: re-optimised under the same rules, the baseline reaches ${N.RgBw} GHz at the proposed gain (proposed: ${N.PBW} GHz), but uses ${N.RgPow} mW and ${N.RgInFive} pA/√Hz.`],
            { x: 0.6, y: 5.5, w: 12.1, h: 1.35, fontSize: 14 });
  s.addNotes('Each hypothesis was fitted with the photodiode and load capacitances free. A unit error on the inductor would explain the published curve, but only the original files could confirm it. At its own best point the re-optimised baseline has a gain-bandwidth product of ' + N.RbGbw + ' THz·Ω at ' + N.RbPow + ' mW, against ' + N.PGbw + ' at ' + N.PPow + ' mW for the proposed circuit.');

  pres.addSection({ title: 'Proposed circuit' });
  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Proposed circuit' });
  s.addText('Three changes: bias the input stage, mirror the load, replace the spiral', { placeholder: 'title' });
  await pic(s, 'schem_proposed.png', 0.6, 1.6, 6.9, 4.6, 'Proposed schematic');
  bullets(s, [`Input stage: RN replaces the off PMOS and M1 gets a proper gate bias. M1 and M2 form a flipped voltage follower; the input drops from ${N.BVin} V to ${N.Vin} V.`,
              'Load: M3b mirrors a 50 µA reference instead of using a fixed gate voltage.',
              'Feedback: source follower Mf, with its gate driven from the output through the PMOS resistor Mt (gate = Vtune) and a 30 fF capacitor Ca.',
              `Headroom works at 1 V: input ${N.Vin} V, output ${N.Vout} V, 0.34 V left for M3b.`], { x: 7.8, y: 1.6, w: 4.9, h: 4.9, fontSize: 15 });
  s.addNotes('Sizes were chosen by a constrained differential-evolution search and then rounded.');

  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Proposed circuit' });
  s.addText('The follower and its gate network behave as a lossy, tunable inductor', { placeholder: 'title' });
  await pic(s, 'fig_active_inductor.png', 0.6, 1.6, 7.6, 3.4, 'Active inductor impedance');
  T(s, [{ text: 'Z = (1 + s·Rt·Cg) / (gf + s·Cg)', options: { bold: true, breakLine: true, fontSize: 18 } },
        { text: `Series resistance 1/gf = ${N.AIRs} Ω. Inductive when Rt exceeds 1/gf; in simulation that is above Vtune ≈ 0.27 V.`, options: { breakLine: true } },
        { text: `At 1 GHz: ${N.AILB} nH at 0.32 V, ${N.AILC} nH at 0.36 V, ${N.AILD} nH at 0.40 V. Peak Q is ${N.AIQD}.`, options: { breakLine: true } },
        { text: 'It is used as a tunable zero in the feedback path, not as a resonator.' }], { x: 8.5, y: 1.6, w: 4.2, h: 4.6, fontSize: 15, paraSpaceAfter: 10 });
  T(s, 'Vtune sets Rt. Small Rt: feedback stays on, response droops early. Larger Rt: feedback is removed sooner with frequency, response flattens, then peaks.', { x: 0.6, y: 5.25, w: 7.6, h: 1.2, fontSize: 14, color: C.text2 });
  s.addNotes('The element is unilateral: it injects current at the input under control of the output voltage but does not load the output with signal current.');

  pres.addSection({ title: 'Results' });
  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Results' });
  s.addText(`${N.GainImp} dB more gain, ${N.NoiseRatio}× lower noise, ${N.PowSave} % less power, no inductor`, { placeholder: 'title' });
  stat(s, 0.6, 1.6, 2.9, `${N.PZt} dBΩ`, `gain (reference: ${N.BZt})`);
  stat(s, 3.7, 1.6, 2.9, `${N.PBW} GHz`, `−3 dB bandwidth, ${N.PPk} dB peaking`);
  stat(s, 6.8, 1.6, 2.9, `${N.PInFive} pA/√Hz`, `noise at 5 GHz (reference: ${N.BInFive})`);
  stat(s, 9.9, 1.6, 2.8, `${N.PPow} mW`, `power at 1 V (reference: ${N.BPow})`);
  await pic(s, 'fig_baseline_vs_proposed.png', 1.6, 3.3, 10.1, 3.4, 'Reference vs proposed');
  s.addNotes('Same test conditions for both: 50 fF photodiode, 30 fF load, 1 V, 35 C.');

  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Results' });
  s.addText(`One voltage moves the bandwidth from ${N.TuneMin} to ${N.TuneMax} GHz`, { placeholder: 'title' });
  await pic(s, 'fig_vtune_tuning.png', 0.6, 1.6, 8.6, 4.2, 'Tuning');
  bullets(s, [`Rt goes from ${N.RtMin} Ω to ${N.RtMaxOne} Ω for Vtune from 0 to ${N.VtOneDb} V.`,
              'Gain does not change and peaking stays under 1 dB over that range.',
              `At the lowest setting the integrated noise falls from ${N.PIrms} to ${N.IrmsMin} µA rms.`,
              `Above ${N.VtOneDb} V the bandwidth saturates and peaking grows.`], { x: 9.5, y: 1.6, w: 3.2, h: 4.9, fontSize: 15 });
  s.addNotes('No DC current flows in Mt, so tuning does not disturb the operating point.');

  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Results' });
  s.addText('The feedback network adds about a fifth of the noise', { placeholder: 'title' });
  await pic(s, 'fig_noise.png', 0.6, 1.6, 8.6, 4.2, 'Noise');
  bullets(s, [`At 5 GHz: M1 ${N.NsMOne} %, M2 ${N.NsMTwo} %, M3 ${N.NsMThree} %, Mf ${N.NsMf} %, Mt ${N.NsMt} %, RN ${N.NsRn} %.`,
              `Total input noise ${N.PIrmsTot} µA rms.`,
              `Estimated sensitivity ${N.SensdBm} dBm at 1e-12, assuming 0.8 A/W.`,
              `The reference is noisier because its triode M1 alone contributes ${N.NsBMOne} %.`], { x: 9.5, y: 1.6, w: 3.2, h: 4.9, fontSize: 15 });

  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Results' });
  s.addText('Trimming Vtune removes peaking across process, voltage and temperature', { placeholder: 'title' });
  await pic(s, 'fig_pvt.png', 0.6, 1.6, 7.9, 4.6, 'PVT');
  stat(s, 8.9, 1.6, 3.8, `${N.PvtPkMax} → ${N.PvtPkTMax} dB`, 'worst peaking over 15 conditions');
  stat(s, 8.9, 3.25, 3.8, S.mc ? `${N.McPkYieldFixed} → ${N.McPkYieldTrim} %` : 'n/a', S.mc ? `Monte Carlo samples under 1 dB peaking (${N.McN} runs)` : 'Monte Carlo');
  T(s, `Trimming cannot recover a slow, hot corner: bandwidth stays at ${S.pvt.rows[13].f3_trim.toFixed(1)} GHz at SS, 0.9 V, 85 °C. Corners and mismatch coefficients are assumed values, not foundry data.`, { x: 8.9, y: 4.95, w: 3.8, h: 1.6, fontSize: 14, color: C.text2 });

  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Results' });
  s.addText('Eye diagrams: open at 10 and 12.5 Gb/s with seven times the swing', { placeholder: 'title' });
  await pic(s, 'fig_eye_diagrams.png', 0.6, 1.5, 8.4, 5.2, 'Eye diagrams');
  bullets(s, [`10 Gb/s: ${N.EyePTenH} mV opening, ${N.EyePTenW} % of the bit period (reference: ${N.EyeBTenH} mV).`,
              `12.5 Gb/s: ${N.EyePTwH} mV and ${N.EyePTwW} %; the reference closes to ${N.EyeBTwW} % horizontally because of ringing.`,
              'PRBS-7, 100 µA peak-to-peak input, no noise added.'], { x: 9.3, y: 1.6, w: 3.4, h: 4.9, fontSize: 15 });

  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Results' });
  s.addText(`DC cancellation: bandwidth held up to ${N.DcLimit} µA of photocurrent`, { placeholder: 'title' });
  await pic(s, 'fig_dcc.png', 0.6, 1.5, 7.4, 5.3, 'DC cancellation');
  stat(s, 8.4, 1.6, 4.3, `${N.PrLimit} → ${N.DcLimit} µA`, 'average photocurrent, gain ±1 dB, bandwidth −10 %');
  bullets(s, [`A replica follower and an OTA hold the follower current near 105 µA; Mdc sinks the photocurrent.`,
              `Cost: ${N.DcPowAdd} µW, +${N.DcNoisePct} % noise at 5 GHz, 2.4 pF of capacitance.`,
              `Phase margin ≥ ${N.DcPmMin}°; low-frequency corner ${N.DcFloDark} kHz to ${N.DcFloMax} MHz.`,
              `Monte Carlo: ${N.DcMcBwMean} ± ${N.DcMcBwStd} GHz at 300 µA; ${N.DcMcPkN} of ${N.DcMcN} samples need a Vtune trim.`], { x: 8.4, y: 3.3, w: 4.3, h: 3.5, fontSize: 14 });
  s.addNotes('Without the loop, every microampere of photocurrent is taken from the follower until it cuts off. The threshold is set above the dark follower current so the loop is always engaged; a version with the threshold below failed Monte Carlo.');

  pres.addSection({ title: 'Limits and next steps' });
  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Limits and next steps' });
  s.addText('What the active inductor does not do', { placeholder: 'title' });
  const cards = [['Power and noise against a fair baseline', `Re-optimised for the same gain, the baseline topology uses ${N.RgPow} mW and ${N.RgInFive} pA/√Hz, but reaches only ${N.RgBw} GHz. The gain is in bandwidth, not efficiency.`],
                 ['No extra bandwidth at light load', `Plain follower feedback reaches ${N.LdResLight} GHz against ${N.LdAiLight} GHz. The zero only helps at heavy load: ${N.LdRatioHeavy}× at 250 fF.`],
                 ['Slow corners stay slow', 'Trimming removes peaking and reins in fast corners, but cannot restore bandwidth lost by the input stage.'],
                 ['Simulation only', 'Predictive model, no layout parasitics, ideal reference current, synthetic corners. Post-layout and silicon results are still to come.']];
  cards.forEach((c, i) => { const x = 0.6 + (i % 2) * 6.15, y = 1.6 + Math.floor(i / 2) * 2.55;
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 5.95, h: 2.3, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: 'limit ' + (i + 1) });
    T(s, c[0], { x: x + 0.25, y: y + 0.2, w: 5.45, h: 0.5, fontSize: 19, bold: true, color: C.accent2, fontFace: THEME.headFontFace });
    T(s, c[1], { x: x + 0.25, y: y + 0.8, w: 5.45, h: 1.35, fontSize: 15, color: C.text1 }); });

  s = pres.addSlide({ masterName: 'Content', sectionTitle: 'Limits and next steps' });
  s.addText('Where it sits among related designs', { placeholder: 'title' });
  const hdr = ['Work', 'Process, supply', 'Gain (dBΩ)', 'Bandwidth (GHz)', 'Power (mW)', 'Inductor', 'Tunable'];
  const rows = [['Alsheikhjader 2020, as published', '90 nm, 1 V', '43.92', '5–15 (flat band)', 'n/r', 'spiral 2.4 nH', 'no'],
                ['Same circuit, re-simulated here', '90 nm PTM, 1 V', N.BZt, `${N.BFlat} (±1 dB)`, N.BPow, 'spiral 2.4 nH', 'no'],
                ['Same topology, re-optimised here', '90 nm PTM, 1 V', N.RgZt, N.RgBw, N.RgPow, `spiral ${N.RgLf} nH`, 'no'],
                ['Zohoori et al. 2018', '90 nm, 1 V', '40.5', '7', '1.4', 'active, load', 'no'],
                ['Alsheikhjader & Issa 2024', '45 nm, 1 V', '68.2', '2.5', '0.56', 'active, local', 'no'],
                ['Shaaban et al. 2025', '45 nm, 1 V', '30.6', '2.8', '1.63', 'shunt peaking', 'no'],
                ['Hwang et al. 2006 (silicon)', '0.18 µm, 2 V', '52', '3.9–7.6', '34', 'none', 'yes'],
                ['Chien et al. 2010 (silicon)', '0.18 µm, 1.8 V', '47.8', '6.2–10.5', '33.3', 'passive', 'yes'],
                ['This work (simulated)', '90 nm PTM, 1 V', N.PZt, `${N.TuneMin}–${N.TuneMax}`, N.PPow, 'active, global', 'yes'],
                ['This work + DC cancellation', '90 nm PTM, 1 V', N.DcZtDark, N.DcBwDark, N.DcPow, 'active, global', 'yes']];
  const cell = (t, o = {}) => ({ text: String(t), options: { fontSize: 13, color: C.text1, valign: 'middle', ...o } });
  s.addTable([hdr.map(h => cell(h, { bold: true, fill: { color: C.background2 } }))].concat(rows.map((r, i) => r.map(c => cell(c, i >= rows.length - 2 ? { bold: true, color: C.accent1 } : {})))),
    { x: 0.6, y: 1.5, w: 12.1, colW: [3.5, 1.9, 1.3, 1.9, 1.2, 1.4, 0.9], rowH: 0.38, border: { type: 'solid', pt: 0.5, color: 'C9CED8' }, objectName: 'comparison table' });
  T(s, 'Tunable TIAs already exist in silicon; what is new here is narrow: an active inductor as global feedback in a current-mirror TIA, with one voltage for both tuning and PVT trimming at 1 V. Other works: authors’ figures under their own conditions. n/r: not reported.', { x: 0.6, y: 5.75, w: 12.1, h: 0.9, fontSize: 13, color: C.text2 });

  s = pres.addSlide({ masterName: 'Dark', sectionTitle: 'Limits and next steps' });
  s.addText('Next: foundry kit, layout, bandgap reference, silicon', { placeholder: 'title' });
  s.addText([{ text: 'Repository: netlists for ngspice, LTspice and Spectre, a Virtuoso SKILL builder, all scripts and raw data, the paper in LaTeX and Word.', options: { breakLine: true } },
             { text: 'Every number in this deck is regenerated by scripts/run_all.py.' }], { placeholder: 'body' });

  const out = path.join(ROOT, 'docs', 'Project_Presentation.pptx');
  await pres.writeFile({ fileName: out });
  const { applyTheme } = require(path.join(SK, 'scripts', 'apply_theme.js'));
  await applyTheme(out, THEME);
  console.log('wrote', out);
})();

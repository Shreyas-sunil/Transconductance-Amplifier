"""Generate paper/numbers.tex and the result tables from results/summary.json, copy figures."""
import os, json, shutil, glob
import circuits as C

S = json.load(open(os.path.join(C.ROOT, 'results', 'summary.json')))
P = os.path.join(C.ROOT, 'paper')
M = {}
p, b, bm = S['prop'], S['base'], S['base_m1v']
def put(k, v, fmt='%.2f'): M[k] = (fmt % v) if not isinstance(v, str) else v
put('PZt', p['zt_db'], '%.1f'); put('PZtOhm', p['zt_ohm'], '%.0f'); put('PBW', p['f3_ghz']); put('PPow', p['power_mw']); put('PPk', p['peaking_db'])
put('PInOne', p['in1'], '%.1f'); put('PInFive', p['in5'], '%.1f'); put('PInTen', p['in10'], '%.1f'); put('PIrms', p['irms_ua']); put('PIrmsTot', p['irms_tot_ua'])
put('PFlat', p['f_flat1db_ghz'], '%.1f'); put('PInAvg', p['in_avg'], '%.1f'); put('PFom', p['fom'], '%.0f')
put('Vin', p['vin']); put('Vout', p['vout']); put('Vn', p['vn']); put('IOne', p['i1_ua'], '%.0f'); put('ITwo', p['i2_ua'], '%.0f'); put('IThree', p['i3_ua'], '%.0f'); put('IF', p['if_ua'], '%.0f')
put('GmOne', p['gm1_ms']); put('GmTwo', p['gm2_ms']); put('GmThree', p['gm3_ms']); put('GmF', p['gmf_ms']); put('RtNom', p['rt_ohm'], '%.0f'); put('Ro', p['ro_ohm'], '%.0f'); put('ITot', p['itot_ua'], '%.0f')
put('BZt', b['zt_db'], '%.1f'); put('BZtOhm', b['zt_ohm'], '%.0f'); put('BPk', b['peaking_db'], '%.1f'); put('BFpk', b['fpk_ghz'], '%.1f'); put('BFlat', b['f_flat1db_ghz'], '%.1f')
put('BPow', b['power_mw']); put('BInOne', b['in1'], '%.1f'); put('BInFive', b['in5'], '%.1f'); put('BInTen', b['in10'], '%.1f'); put('BInFifteen', b['in15'], '%.1f'); put('BIrmsTot', b['irms_tot_ua'], '%.1f')
put('BITwo', b['i2_ua'], '%.0f'); put('BIOne', b['i1_na'], '%.1f'); put('BGmTwo', b['gm2_ms']); put('BGdsOne', b['gds1_ms']); put('BVin', b['vin']); put('BFom', b['fom_flat'], '%.0f')
put('BMZt', bm['zt_db'], '%.1f'); put('BMPow', bm['power_mw']); put('BMPk', bm['peaking_db'], '%.1f'); put('BMInFive', bm['in5'], '%.1f')
put('GainImp', S['gain_improvement_db'], '%.1f'); put('NoiseRatio', S['noise_ratio_5g'], '%.1f'); put('PowSave', S['power_saving_pct'], '%.0f')
t = S['tune']
put('TuneMin', t['f3_min_ghz']); put('TuneMax', t['f3_max_ghz']); put('TuneRatio', t['ratio']); put('VtOneDb', t['vt_at_1db']); put('RtMin', t['rt_min'], '%.0f')
put('RtMaxOne', t['rt_max_1db'], '%.0f'); put('IrmsMin', t['irms_min_ua']); put('PkMax', t['pk_max_db'], '%.1f'); put('VtMax', t['vt_max'])
put('VtNom', S['params']['vtune']); put('AIRs', S['ai']['0.28']['rs'], '%.0f'); put('AIgm', S['ai_gm_ms'])
for k, tag in (('0.28', 'A'), ('0.32', 'B'), ('0.36', 'C'), ('0.40', 'D')):
    put('AIL' + tag, S['ai'][k]['L1g_nh'], '%.1f'); put('AIQ' + tag, S['ai'][k]['qmax']); put('AIRt' + tag, S['ai'][k]['rt'], '%.0f')
l = S['loop']
put('LoopTzero', l['global_t0_db'], '%.1f'); put('LoopPMg', l['global_pm_min'], '%.0f'); put('LoopPMl', l['local_pm_min'], '%.0f'); put('LoopPMlCpd', l['local_pm_cpd']['200f'], '%.0f')
put('LoopFuMin', min(l['global_fu_ghz']), '%.1f'); put('LoopFuMax', max(l['global_fu_ghz']), '%.1f')
v = S['pvt']
for k in ('f3_nom', 'pk_nom', 'f3_trim', 'pk_trim', 'zt_nom', 'p_nom'):
    nm = {'f3_nom': 'PvtBw', 'pk_nom': 'PvtPk', 'f3_trim': 'PvtBwT', 'pk_trim': 'PvtPkT', 'zt_nom': 'PvtZt', 'p_nom': 'PvtP'}[k]
    put(nm + 'Min', v[k + '_min']); put(nm + 'Max', v[k + '_max'])
mo = S['model']
put('ZtExact', mo['z0_exact'], '%.0f'); put('ZtApprox', mo['z0_approx'], '%.0f'); put('Tzero', mo['t0']); put('AOne', mo['a1'], '%.1f')
put('Mratio', p['gm3_ms'] / p['gm2_ms']); put('Fz', mo['fz_ghz'], '%.1f'); put('Fp', mo['fp_ghz'], '%.1f')
for k, vv in mo['caps'].items(): put('Cap' + k, vv, '%.0f')
put('ModelRmsNom', [x for x in mo['val'] if abs(x['vt'] - 0.28) < 1e-6][0]['rms']); put('ModelRmsMax', max(x['rms'] for x in mo['val']))
put('ModelRmsLow', max(x['rms'] for x in mo['val'] if x['vt'] <= 0.281)); put('ModelMaxLow', max(x['mx'] for x in mo['val'] if x['vt'] <= 0.281), '%.1f'); put('ModelMaxAll', max(x['mx'] for x in mo['val']), '%.1f')
e = {(x['circ'], x['rate']): x for x in S['eye'] if x['vtune'] is None}
for (c, r), tag in ((('prop', 10e9), 'EyePTen'), (('base', 10e9), 'EyeBTen'), (('prop', 12.5e9), 'EyePTw'), (('base', 12.5e9), 'EyeBTw')):
    put(tag + 'H', e[(c, r)]['eye_height_V'] * 1e3, '%.1f'); put(tag + 'Pct', e[(c, r)]['eye_height_pct'], '%.0f'); put(tag + 'W', e[(c, r)]['eye_width_pct'], '%.0f'); put(tag + 'Amp', e[(c, r)]['amp_V'] * 1e3, '%.1f')
put('ZoutB', S['zout']['base']['zout_100M'], '%.0f'); put('ZoutBF', S['zout']['base']['formula_lf'], '%.0f'); put('ZoutP', S['zout']['prop']['zout_100M'], '%.0f'); put('ZoutBMax', S['zout']['base']['zout_max'], '%.0f')
put('SensIpp', S['sens']['ipp_min_ua'], '%.1f'); put('SensdBm', S['sens']['p_avg_dbm'], '%.1f')
a = S['area']
put('SpiralSide', a['spiral_side_um'], '%.0f'); put('SpiralArea', a['spiral_um2'] / 1e6, '%.3f'); put('AIArea', a['ai_um2'], '%.0f'); put('AreaRatio', a['ratio'], '%.0f')
o = {x['idc']: x for x in S['overload']}
put('OvA', o[25]['zt'] - o[0]['zt'], '%.1f'); put('OvB', o[50]['zt'] - o[0]['zt'], '%.1f'); put('OvC', o[100]['zt'] - o[0]['zt'], '%.1f'); put('OvBwB', o[50]['f3'], '%.1f'); put('OvBwC', o[100]['f3'], '%.1f')
ld = {x['cl']: x for x in S['load']}
put('LdResLight', ld[30]['f3_res']); put('LdAiLight', ld[30]['f3_ai']); put('LdRatioLight', ld[30]['ratio']); put('LdResHeavy', ld[250]['f3_res']); put('LdAiHeavy', ld[250]['f3_ai']); put('LdRatioHeavy', ld[250]['ratio'])
put('LdRatioMid', ld[150]['ratio'])
ns = S['noise_share_prop']
for k, tag in (('m1', 'NsMOne'), ('m2', 'NsMTwo'), ('m3', 'NsMThree'), ('mf', 'NsMf'), ('mt', 'NsMt'), ('m3b', 'NsMThreeB'), ('rn', 'NsRn')):
    put(tag, ns.get(k, 0), '%.0f')
put('NsBMOne', S['noise_share_base']['m1'], '%.0f')
if 'mc' in S:
    m = S['mc']
    put('McN', m['n'], '%d'); put('McBwMean', m['f3']['mean']); put('McBwStd', m['f3']['std']); put('McBwMin', m['f3']['min']); put('McBwMax', m['f3']['max'])
    put('McBwTMean', m['f3_t']['mean']); put('McBwTStd', m['f3_t']['std']); put('McBwTMin', m['f3_t']['min']); put('McBwTMax', m['f3_t']['max'])
    put('McPkMax', m['pk']['max']); put('McPkTMax', m['pk_t']['max']); put('McZtMean', m['zt']['mean'], '%.1f'); put('McZtStd', m['zt']['std']); put('McPStd', m['pwr']['std'], '%.3f')
    put('McYieldFixed', m['yield_bw9_fixed'], '%.0f'); put('McYieldTrim', m['yield_bw9_trim'], '%.0f'); put('McPkYieldFixed', m['yield_pk1_fixed'], '%.0f'); put('McPkYieldTrim', m['yield_pk1_trim'], '%.0f')
    put('McVtMin', m['vt']['min']); put('McVtMax', m['vt']['max'])
open(os.path.join(P, 'numbers.tex'), 'w').write('% auto-generated by scripts/build_paper.py from results/summary.json - do not edit\n' +
                                               ''.join('\\newcommand{\\%s}{%s}\n' % kv for kv in M.items()))
json.dump(M, open(os.path.join(C.ROOT, 'results', 'numbers.json'), 'w'), indent=1)
# ---- tables
rows = ['%s & %.2f & %.2f & %.2f & %.2f & %.2f \\\\' % (r['case'].replace('%', '\\%').replace(' C', '\\,$^\\circ$C'), r['f3_nom'], r['pk_nom'], r['vt'], r['f3_trim'], r['pk_trim']) for r in v['rows']]
open(os.path.join(P, 'table_pvt.tex'), 'w').write('\n'.join(rows) + '\n')
rows = ['%.2f & %.0f & %.2f & %.2f & %.2f & %.1f \\\\' % (r['vt'], r['rt'], r['f3'], r['pk'], r['irms'], r['in5']) for r in t['table'] if r['vt'] <= 0.401]
open(os.path.join(P, 'table_tune.tex'), 'w').write('\n'.join(rows) + '\n')
rows = ['%d & %.2f & %.2f & %.2f & %.2f & %.2f \\\\' % (r['cl'], r['f3_res'], r['f3_ai_nom'], r['vt'], r['f3_ai'], r['ratio']) for r in S['load']]
open(os.path.join(P, 'table_load.tex'), 'w').write('\n'.join(rows) + '\n')
sz = S['sizes']
rows = ['$M_1$ & %g/%g & $M_f$ & %g/%g \\\\' % (sz['M1'][0], sz['M1'][1] / 1000, sz['Mf'][0], sz['Mf'][1] / 1000),
        '$M_2$ & %g/%g & $M_t$ & %g/%g \\\\' % (sz['M2'][0], sz['M2'][1] / 1000, sz['Mt'][0], sz['Mt'][1] / 1000),
        '$M_3$ & %g/%g & $M_{bp}, M_{br}$ & %g/%g \\\\' % (sz['M3'][0], sz['M3'][1] / 1000, sz['Mbp'][0], sz['Mbp'][1] / 1000),
        '$M_{3b}$ & %g/%g & $M_{bn}$ & %g/%g \\\\' % (sz['M3b'][0], sz['M3b'][1] / 1000, sz['Mbn'][0], sz['Mbn'][1] / 1000)]
open(os.path.join(P, 'table_sizes.tex'), 'w').write('\n'.join(rows) + '\n')
for f in glob.glob(os.path.join(C.ROOT, 'results', 'figures', '*')):
    shutil.copy(f, os.path.join(P, 'figures'))
print(len(M), 'macros written')

# ---------------------------------------------------------------- baseline diagnosis, fair baselines, DCC
import numpy as np
D = os.path.join(C.ROOT, 'results', 'data')
jl = lambda n: json.load(open(os.path.join(D, n)))
M2 = {}
def put2(k, v, fmt='%.2f'): M2[k] = (fmt % v) if not isinstance(v, str) else v
dg = {r['label']: r for r in jl('baseline_diag.json')}
put2('DgRmsDrawn', dg['H0']['rms_db_5030'], '%.1f'); put2('DgRmsFitDrawn', dg['H0']['rms_db'], '%.1f')
put2('DgRmsMOne', dg['H1']['rms_db'], '%.1f'); put2('DgRmsMTwoB', dg['H2']['rms_db'], '%.1f'); put2('DgRmsLoss', dg['H3']['rms_db'], '%.1f')
put2('DgRmsBestL', min(dg[k]['rms_db'] for k in ('H0', 'H1', 'H2', 'H3', 'H4', 'H5')), '%.1f')
put2('DgRsBestL', dg['H5']['rs'], '%.0f'); put2('DgRmsNoL', dg['H6']['rms_db'], '%.1f'); put2('DgVgNoL', dg['H6']['vg3b'], '%.2f')
put2('DgIdNoL', dg['H6']['id_m2'] * 1e6, '%.0f'); put2('DgPwrNoL', dg['H6']['pwr'], '%.2f' if False else '%.2f')
M2['DgPwrNoL'] = '%.2f' % (dg['H6']['pwr'] * 1e3)
sc = jl('baseline_lfscan.json'); emin = min(r['rms_db'] for r in sc)
put2('DgLfMax', max(r['lf'] for r in sc if r['rms_db'] <= emin + 0.1) * 1e12, '%.0f')
put2('DgRmsTwoFour', [r for r in sc if abs(r['lf'] - 2.4e-9) < 1e-12][0]['rms_db'], '%.1f')
scr = jl('baseline_screen.json')
put2('DgSatMax', max(r['vds_m1'] / 0.1 if False else 0 for r in scr), '%.2f')
put2('DgVdsRatioMax', max(r['vds_m1'] / r['vdsat_m1'] for r in scr), '%.2f'); put2('DgNScreen', len(scr), '%d')
put2('DgPkMin', min(r['pk'] for r in scr), '%.1f')
put2('DgEqNine', 2 * np.pi * 1e9 * 2.4e-9, '%.0f')
ro = jl('baseline_reopt.json'); g, b2 = ro['baseline_opt_gain'], ro['baseline_opt_gbw']
nom = jl('nominal.json')['proposed']
for tag, r in (('Rg', g), ('Rb', b2)):
    put2(tag + 'Zt', r['z0db'], '%.1f'); put2(tag + 'Bw', r['f3'] / 1e9, '%.1f'); put2(tag + 'Pk', r['pk'], '%.1f')
    put2(tag + 'Pow', r['pwr'] * 1e3, '%.2f'); put2(tag + 'InFive', r['in5'], '%.1f'); put2(tag + 'Irms', r['irms'] * 1e6, '%.2f')
    put2(tag + 'Fom', 10 ** (r['z0db'] / 20) * r['f3'] / 1e9 / (r['pwr'] * 1e3), '%.0f')
    put2(tag + 'Gbw', 10 ** (r['z0db'] / 20) * r['f3'] / 1e12, '%.1f')
put2('RgLf', 5.036, '%.1f'); put2('RbLf', 1.251, '%.2f'); put2('RgRs', 43.0, '%.0f'); put2('RbRs', 42.8, '%.0f')
put2('PFomP', nom['z0'] * nom['f3'] / 1e9 / (nom['pwr'] * 1e3), '%.0f'); put2('PGbw', nom['z0'] * nom['f3'] / 1e12, '%.1f')
put2('BwRatioGain', nom['f3'] / g['f3'], '%.1f')
di = jl('dcc_idc.json'); dz = di['dcc'][0]; pz = di['prop'][0]
def limit(rows):
    z0, f0 = rows[0]['z0db'], rows[0]['f3']
    ok = [r['idc_uA'] for r in rows if abs(r['z0db'] - z0) <= 1.0 and r['f3'] >= 0.9 * f0]
    lim = 0
    for r in rows:
        if r['idc_uA'] in ok: lim = r['idc_uA']
        else: break
    return lim
put2('DcLimit', limit(di['dcc']), '%d'); put2('PrLimit', limit(di['prop']), '%d')
put2('DcPow', dz['pwr'] * 1e3, '%.2f'); put2('DcPowAdd', (dz['pwr'] - pz['pwr']) * 1e6, '%.0f')
put2('DcImfDark', dz['imf'] * 1e6, '%.0f'); put2('DcIdccDark', dz['idcc'] * 1e6, '%.0f'); put2('DcBwDark', dz['f3'] / 1e9, '%.2f')
put2('DcZtDark', dz['z0db'], '%.1f'); put2('DcFloDark', dz['f_lo'] / 1e3, '%.0f')
r5 = [r for r in di['dcc'] if r['idc_uA'] == 500][0]; r3 = [r for r in di['dcc'] if r['idc_uA'] == 300][0]
put2('DcBwFive', r5['f3'] / 1e9, '%.2f'); put2('DcZtFive', r5['z0db'] - dz['z0db'], '%.1f'); put2('DcImfFive', r5['imf'] * 1e6, '%.0f')
put2('DcBwThree', r3['f3'] / 1e9, '%.2f'); put2('DcImfThree', r3['imf'] * 1e6, '%.0f')
put2('DcBwHund', [r for r in di['dcc'] if r['idc_uA'] == 100][0]['f3'] / 1e9, '%.2f')
put2('DcFloMax', max(r['f_lo'] for r in di['dcc'] if r['idc_uA'] <= 500) / 1e6, '%.1f')
put2('DcPkHfMax', max(r['pk_hf'] for r in di['dcc'] if r['idc_uA'] <= 500), '%.1f')
put2('DcPkLfMax', max(r['pk_lf'] for r in di['dcc'] if r['idc_uA'] <= 500), '%.1f')
pr = {r['idc_uA']: r for r in di['prop']}
put2('PrBwHundred', pr[100]['f3'] / 1e9, '%.1f'); put2('PrBwFifty', pr[50]['f3'] / 1e9, '%.1f')
ns = {(r['circ'], r['idc_uA']): r for r in jl('dcc_noise.json')}
put2('DcInFive', ns[('dcc', 0)]['in5'], '%.1f'); put2('DcInFiveThree', ns[('dcc', 300)]['in5'], '%.1f')
put2('DcNoisePct', 100 * (ns[('dcc', 0)]['in5'] / ns[('prop', 0)]['in5'] - 1), '%.0f')
put2('ShotThree', np.sqrt(2 * 1.602e-19 * 300e-6) * 1e12, '%.1f')
lp = jl('dcc_loop.json')
act = [r for r in lp if r['idc_uA'] <= 500]
put2('DcPmMin', min(r['pm_deg'] for r in act), '%.0f'); put2('DcFuMin', min(r['f_unity'] for r in act) / 1e3, '%.0f')
put2('DcFuMax', max(r['f_unity'] for r in act) / 1e6, '%.1f'); put2('DcTzMax', max(r['T0_db'] for r in act), '%.0f')
put2('DcTzMin', min(r['T0_db'] for r in act), '%.0f')
stp = jl('dcc_step.json')
put2('DcSettle', stp['dcc']['settle_s'] * 1e6, '%.1f'); put2('DcDip', -stp['dcc']['dip'] * 1e3, '%.0f')
put2('DcErr', abs(stp['dcc']['v_after'] - stp['dcc']['v_before']) * 1e3, '%.0f'); put2('PrDrop', (stp['prop']['v_before'] - stp['prop']['v_after']) * 1e3, '%.0f')
ey = {(r['circ'], r['idc_uA']): r for r in jl('dcc_eye.json')}
for c, tg in (('prop', 'Pr'), ('dcc', 'Dc')):
    for i, t2 in ((0, 'Zero'), (100, 'Hund'), (300, 'Three')):
        put2(tg + 'Eye' + t2, ey[(c, i)]['eye_height_pct'], '%.0f'); put2(tg + 'EyeW' + t2, ey[(c, i)]['eye_width_pct'], '%.0f')
pv = jl('dcc_pvt.json')
put2('DcPvtIdccMax', max(r['idc0']['idcc'] for r in pv) * 1e6, '%.0f')
put2('DcPvtBwMin', min(r['idc300']['f3'] for r in pv) / 1e9, '%.1f')
put2('DcPvtBwMinB', sorted(r['idc300']['f3'] for r in pv)[1] / 1e9, '%.1f')
put2('DcPvtN', len(pv), '%d')
mc = jl('dcc_mc.json')
f3 = lambda k: np.array([r[k]['f3'] for r in mc]) / 1e9
put2('DcMcN', len(mc), '%d'); put2('DcMcBwMean', f3('idc300').mean()); put2('DcMcBwStd', f3('idc300').std()); put2('DcMcBwMin', f3('idc300').min())
put2('DcMcBwDarkMin', f3('idc0').min()); put2('DcMcPrDarkMin', f3('prop0').min())
put2('DcMcIdccMed', np.median([r['idc0']['idcc'] for r in mc]) * 1e6, '%.0f'); put2('DcMcIdccMax', max(r['idc0']['idcc'] for r in mc) * 1e6, '%.0f')
put2('DcMcImfStd', np.std([r['idc300']['imf'] for r in mc]) * 1e6, '%.0f')
put2('DcMcPkMax', max(r['idc0']['pk'] for r in mc), '%.1f'); put2('DcMcPrPkMax', max(r['prop0']['pk'] for r in mc), '%.1f')
put2('DcMcZtStd', np.std([r['idc0']['z0db'] for r in mc]), '%.1f'); put2('DcMcPrZtStd', np.std([r['prop0']['z0db'] for r in mc]), '%.1f')
put2('DcMcImfDarkStd', np.std([r['prop0']['imf'] for r in mc]) * 1e6, '%.0f')
put2('DcMcPkN', sum(r['idc0']['pk'] > 1 for r in mc), '%d')
tr = jl('dcc_mc_trim.json')
put2('DcTrBwMin', min(r['f3'] for r in tr) / 1e9, '%.1f'); put2('DcTrBwThree', min(r['f3_300'] for r in tr) / 1e9, '%.1f')
put2('DcTrPkThree', max(r['pk_300'] for r in tr), '%.1f')
with open(os.path.join(P, 'numbers.tex'), 'a') as fh:
    fh.write(''.join('\\newcommand{\\%s}{%s}\n' % kv for kv in M2.items()))
M.update(M2); json.dump(M, open(os.path.join(C.ROOT, 'results', 'numbers.json'), 'w'), indent=1)
print(len(M2), 'extra macros'); print(json.dumps(M2, indent=0))

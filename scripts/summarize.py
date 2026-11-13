"""Collect the headline numbers from results/data into results/summary.json (used by the documents)."""
import os, json, math
import numpy as np
import circuits as C

DATA = os.path.join(C.ROOT, 'results', 'data')
Jl = lambda n: json.load(open(os.path.join(DATA, n)))
G = 1e9


def spiral_side_um(L_nH=2.4, n=3.5, w=6.0, s=2.0):
    """Outer side of a square spiral from the modified Wheeler formula (Mohan et al., JSSC 1999)."""
    mu0 = 4e-7 * math.pi
    lo, hi = 20.0, 2000.0
    for _ in range(60):
        d = 0.5 * (lo + hi)
        din = d - 2 * (n * w + (n - 1) * s)
        if din <= 0:
            lo = d; continue
        davg = 0.5 * (d + din) * 1e-6; rho = (d - din) / (d + din)
        L = 2.34 * mu0 * n * n * davg / (1 + 2.75 * rho) * 1e9
        lo, hi = (d, hi) if L < L_nH else (lo, d)
    return d, din


def main():
    nom = Jl('nominal.json'); sw = Jl('vtune_sweep.json'); ai = Jl('active_inductor.json'); nb = Jl('noise_breakdown.json')
    lp = Jl('loopgain.json'); pv = Jl('pvt.json'); se = Jl('sensitivity.json'); ey = Jl('eye.json'); ld = Jl('load_study.json'); mo = Jl('model.json')
    p, b, b2 = nom['proposed'], nom['baseline'], nom['baseline_vg_m1V']
    S = {}
    for tag, d in (('prop', p), ('base', b), ('base_m1v', b2)):
        S[tag] = dict(zt_db=d['z0db'], zt_ohm=d['z0'], peaking_db=d['pk'], fpk_ghz=d['fpk'] / G, f3_ghz=d['f3'] / G,
                      f_flat1db_ghz=d['f_1dB_flat'] / G, power_mw=d['pwr'] * 1e3, in1=d['in1'], in5=d['in5'], in10=d['in10'], in15=d['in15'],
                      irms_ua=d['irms'] * 1e6, irms_tot_ua=d['irms_tot'] * 1e6, in_avg=d['in_avg'] * 1e12,
                      vin=d['v(in)'], vout=d['v(out)'], vn=d['v(n)'], itot_ua=-d['i(vdd)'] * 1e6)
    S['base']['f3_from_peak_ghz'] = b['f3_from_peak'] / G
    S['prop'].update(i1_ua=p['@m1[id]'] * 1e6, i2_ua=p['@m2[id]'] * 1e6, i3_ua=p['@m3[id]'] * 1e6, if_ua=p['@mf[id]'] * 1e6,
                     gm1_ms=p['@m1[gm]'] * 1e3, gm2_ms=p['@m2[gm]'] * 1e3, gm3_ms=p['@m3[gm]'] * 1e3, gmf_ms=p['@mf[gm]'] * 1e3,
                     rt_ohm=1 / p['@mt[gds]'], ro_ohm=1 / (p['@m3[gds]'] + p['@m3b[gds]']), vg=p['v(g)'], vb1=p['v(vb1)'], vbp=p['v(vbp)'])
    S['base'].update(i2_ua=b['@m2[id]'] * 1e6, i1_na=b['@m1[id]'] * 1e9, gm2_ms=b['@m2[gm]'] * 1e3, gds1_ms=b['@m1[gds]'] * 1e3, i3b_ua=b['@m3b[id]'] * 1e6)
    S['gain_improvement_db'] = p['z0db'] - b['z0db']
    S['noise_ratio_5g'] = b['in5'] / p['in5']
    S['power_saving_pct'] = 100 * (1 - p['pwr'] / b['pwr'])
    # figure of merit: gain(ohm) * BW(GHz) / power(mW)
    S['prop']['fom'] = p['z0'] * p['f3'] / G / (p['pwr'] * 1e3)
    S['base']['fom_flat'] = b['z0'] * b['f_1dB_flat'] / G / (b['pwr'] * 1e3)
    # tuning
    ok = [r for r in sw if r['pk'] <= 1.0]
    S['tune'] = dict(vt_min=sw[0]['vtune'], f3_min_ghz=min(r['f3'] for r in ok) / G, f3_max_ghz=max(r['f3'] for r in ok) / G,
                     vt_at_1db=max(r['vtune'] for r in ok), rt_min=sw[0]['rt'], rt_max_1db=max(r['rt'] for r in ok),
                     irms_min_ua=sw[0]['irms'] * 1e6, irms_nom_ua=p['irms'] * 1e6,
                     pk_max_db=max(r['pk'] for r in sw), vt_max=sw[-1]['vtune'],
                     table=[dict(vt=r['vtune'], rt=r['rt'], f3=r['f3'] / G, pk=r['pk'], irms=r['irms'] * 1e6, in5=r['in5']) for r in sw if round(r['vtune'] * 100) % 4 == 0])
    S['tune']['ratio'] = S['tune']['f3_max_ghz'] / S['tune']['f3_min_ghz']
    S['ai'] = {k: dict(rt=v['rt'], rs=v['rs_lf'], L1g_nh=v['L_1G'] * 1e9, qmax=v['Qmax'], srf_ghz=(v['srf'] / G if v['srf'] == v['srf'] else None)) for k, v in ai.items()}
    S['ai_gm_ms'] = list(ai.values())[0]['gm'] * 1e3
    S['noise_share_prop'] = {k: 100 * v for k, v in sorted(nb['prop']['share_at_5GHz'].items(), key=lambda kv: -kv[1]) if v > 0.003}
    S['noise_share_base'] = {k: 100 * v for k, v in sorted(nb['base']['share_at_5GHz'].items(), key=lambda kv: -kv[1]) if v > 0.003}
    S['loop'] = dict(global_t0_db=lp['global'][0]['t0_db'], global_pm_min=min(r['pm_min'] for r in lp['global']),
                     global_fu_ghz=[c[0] / G for r in lp['global'] for c in r['crossings']],
                     local_pm_min=min(r['pm_min'] for r in lp['local']),
                     local_pm_cpd={r['cpd']: r['pm_min'] for r in lp['local_cpd']})
    rows = pv['rows']
    S['pvt'] = dict(rows=[dict(case=r['case'], f3_nom=r['nominal']['f3'] / G, pk_nom=r['nominal']['pk'], zt_nom=r['nominal']['z0db'],
                               p_nom=r['nominal']['pwr'] * 1e3, vt=r['vt_trim'], f3_trim=r['trimmed']['f3'] / G, pk_trim=r['trimmed']['pk'],
                               in5_trim=r['trimmed']['in5']) for r in rows])
    for k in ('f3_nom', 'pk_nom', 'f3_trim', 'pk_trim', 'zt_nom', 'p_nom'):
        v = [r[k] for r in S['pvt']['rows']]; S['pvt'][k + '_min'] = min(v); S['pvt'][k + '_max'] = max(v)
    S['cpd'] = [dict(cpd=r['cpd_fF'], f3=r['nominal']['f3'] / G, pk=r['nominal']['pk'], vt=r['vt_trim'], f3_t=r['trimmed']['f3'] / G,
                     pk_t=r['trimmed']['pk'], in5=r['trimmed']['in5'], base_pk=r['baseline']['pk'], base_fpk=r['baseline']['fpk'] / G) for r in se['cpd']]
    S['overload'] = [dict(idc=r['idc_uA'], zt=r['prop']['z0db'], f3=r['prop']['f3'] / G, zt_base=r['base']['z0db']) for r in se['idc']]
    S['eye'] = ey
    S['load'] = [dict(cl=r['cl_fF'], f3_res=r['resistive']['f3'] / G, pk_res=r['resistive']['pk'], f3_ai_nom=r['ai_nominal']['f3'] / G,
                      vt=r['vt_best'], f3_ai=r['f3_best'] / G, pk_ai=r['pk_best'], ratio=r['f3_best'] / r['resistive']['f3']) for r in ld]
    S['model'] = dict(caps=mo['caps_fF'], z0_sim=mo['z0_sim'], z0_exact=mo['z0_exact'], z0_approx=mo['z0_approx'], t0=mo['T0_approx'], a1=mo['A1'],
                      fz_ghz=mo['fz_GHz'], fp_ghz=mo['fp_fb_GHz'], val=[dict(vt=v['vtune'], rms=v['rms_db'], mx=v['max_db'], f3s=v['f3_sim'] / G, f3m=v['f3_model'] / G) for v in mo['validation']])
    if os.path.exists(os.path.join(DATA, 'montecarlo.json')):
        mc = Jl('montecarlo.json'); r = mc['rows']
        a = lambda k: np.array([x[k] for x in r], float)
        st = lambda v: dict(mean=float(np.nanmean(v)), std=float(np.nanstd(v)), min=float(np.nanmin(v)), max=float(np.nanmax(v)))
        S['mc'] = dict(n=mc['n'], f3=st(a('f3') / G), f3_t=st(a('f3_t') / G), pk=st(a('pk')), pk_t=st(a('pk_t')), zt=st(a('z0db')), pwr=st(a('pwr') * 1e3),
                       vt=st(a('vt_trim')), yield_pk1_fixed=float(100 * np.mean(a('pk') <= 1.0)), yield_pk1_trim=float(100 * np.mean(a('pk_t') <= 1.0)),
                       yield_bw9_fixed=float(100 * np.mean((a('f3') / G >= 9.0) & (a('pk') <= 1.0))), yield_bw9_trim=float(100 * np.mean((a('f3_t') / G >= 9.0) & (a('pk_t') <= 1.0))),
                       assumptions=dict(avt_mV_um=mc['avt'] * 1e9, abeta_pct_um=mc['abeta'] * 1e8, sig_vth_mV=mc['sig_vth_global'] * 1e3,
                                        sig_mu_pct=mc['sig_mu_global'] * 100, sig_r_pct=mc['sig_r'] * 100, sig_c_pct=mc['sig_c'] * 100))
    S['zout'] = Jl('zout.json')
    # sensitivity estimate
    Q = 7.034; resp = 0.8
    ipp = 2 * Q * S['prop']['irms_tot_ua']
    S['sens'] = dict(q=Q, resp=resp, ipp_min_ua=ipp, p_avg_dbm=10 * math.log10(Q * S['prop']['irms_tot_ua'] * 1e-6 / resp * 1e3))
    # area estimate
    d, din = spiral_side_um()
    geo = lambda w, l: w * (l / 1000 + 0.4)          # gate + two 0.2 um diffusions, um^2
    ai_dev = geo(*C.PROP_SZ['Mf']) + geo(*C.PROP_SZ['Mt']); ca_area = 30 / 1.5
    S['area'] = dict(spiral_side_um=d, spiral_inner_um=din, spiral_um2=d * d, turns=3.5, w_um=6.0, s_um=2.0,
                     ai_dev_um2=ai_dev, ca_um2=ca_area, mim_fF_um2=1.5, overhead=5.0, ai_um2=(ai_dev + ca_area) * 5.0)
    S['area']['ratio'] = S['area']['spiral_um2'] / S['area']['ai_um2']
    S['sizes'] = {k: v for k, v in C.PROP_SZ.items()}; S['params'] = C.PROP_P; S['base_sizes'] = C.BASE_SZ; S['base_params'] = C.BASE_P
    def clean(o):
        if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)): return [clean(v) for v in o]
        if isinstance(o, float) and o != o: return None
        return o
    S = clean(S)
    json.dump(S, open(os.path.join(C.ROOT, 'results', 'summary.json'), 'w'), indent=1, default=float, allow_nan=False)
    return S


if __name__ == '__main__':
    S = main()
    for k in ('prop', 'base'):
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in S[k].items()})
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in S.items() if not isinstance(v, (dict, list))})
    print('tune', {k: v for k, v in S['tune'].items() if k != 'table'}); print('area', S['area']); print('sens', S['sens']); print('loop', S['loop'])
    print('ai', S['ai']); print('mc', S.get('mc')); print('noise', S['noise_share_prop'], S['noise_share_base'])

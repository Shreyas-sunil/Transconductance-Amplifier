"""Re-evaluates eye openings from the folded waveforms written by tia.py (eyewave_*.csv).
The waveform is rebuilt from the first UI of every 2-UI window, then the latency and the
polarity (the proposed TIA is inverting) are searched: tia.py assumed a non-inverting output."""
import numpy as np, pandas as pd, glob, os, sys

def prbs7(n):
    s = 0x7f; out = []
    for _ in range(n):
        b = ((s >> 6) ^ (s >> 5)) & 1
        s = ((s << 1) | b) & 0x7f
        out.append(b)
    return np.array(out)

BITS = prbs7(127 * 2 + 20)
NS = 24          # samples per UI in the rebuilt waveform

def rebuild(df):
    k = df.bit.values.astype(int); u = df.ui.values; v = df.v.values
    sel = u < 1.0 - 1e-9
    k, u, v = k[sel], u[sel], v[sel]
    t = k + u                                   # in UI, relative to the stored delay
    o = np.argsort(t)
    return t[o], v[o]

def metrics(t, v, skip=24):
    best = None
    for pol in (1, -1):
        for lat in np.arange(-3.0, 4.0, 1.0 / NS):
            # sample of bit b is taken at time b + 0.5 + lat (in UI) in the rebuilt axis
            b = np.arange(int(t[0]) + skip, int(t[-1]) - 4)
            ts = b + 0.5 + lat
            ok = (ts >= t[0]) & (ts <= t[-1])
            b, ts = b[ok], ts[ok]
            vs = pol * np.interp(ts, t, v)
            one, zero = vs[BITS[b] == 1], vs[BITS[b] == 0]
            op = one.min() - zero.max()
            if best is None or op > best[0]:
                best = (op, pol, lat, one.mean() - zero.mean())
    op, pol, lat, amp = best
    good = 0
    for ph in np.arange(-0.5, 0.5, 1.0 / NS):
        b = np.arange(int(t[0]) + skip, int(t[-1]) - 4)
        ts = b + 0.5 + lat + ph
        ok = (ts >= t[0]) & (ts <= t[-1])
        vs = pol * np.interp(ts[ok], t, v)
        bb = b[ok]
        if vs[BITS[bb] == 1].min() - vs[BITS[bb] == 0].max() > 0:
            good += 1
    return dict(amp=amp, vopen=op, vpct=100 * op / amp, hpct=100.0 * good / NS, pol=pol, lat=lat)

if __name__ == '__main__':
    d = sys.argv[1]
    rows = []
    for f in sorted(glob.glob(os.path.join(d, 'eyewave_*.csv'))):
        name = os.path.basename(f)[8:-4]
        t, v = rebuild(pd.read_csv(f))
        m = metrics(t, v)
        p = name.split('_')
        rate = 12.5 if name.endswith('12p5') else 10.0
        rows.append(dict(case=name, rate=rate, **m))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(d, 'eye_post.csv'), index=False)
    print(out.round(3).to_string())

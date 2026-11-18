"""Build the GPDK090 table bodies for paper/main.tex from results/gpdk090/*.csv (Cadence Spectre output)."""
import csv, pathlib
R = pathlib.Path(__file__).resolve().parent.parent
D = R / "results" / "gpdk090"
P = R / "paper"
corn = list(csv.DictReader(open(D / "corners.csv")))
noise = {r["cell"]: r for r in csv.DictReader(open(D / "noise_nn35.csv"))}
sweep = list(csv.DictReader(open(D / "vtune_sweep.csv")))
names = {"base2020": "2020 baseline, as drawn", "regain": "Same-gain baseline", "proposed": "Proposed, $V_{tune}$ = 0.24\\,V"}

def rows(cell): return [r for r in corn if r["cell"] == cell]
def nn35(cell): return next(r for r in rows(cell) if r["section"] == "NN" and r["temp_C"] == "35")
def span(cell, k, f=lambda r, k: float(r[k])):
    v = [f(r, k) for r in rows(cell)]; return min(v), max(v)

# nominal: NN, 35 C
out = []
for c in names:
    n, z = nn35(c), noise[c]
    zt = float(n["Zt100M_dBohm"]); bw = float(n["f3dB_GHz"])
    gbw = 10 ** (zt / 20) * bw / 1000
    out.append(f'{names[c]} & {zt:.1f} & {float(n["peak_dBohm"]) - zt:.1f} & {bw:.1f} & {gbw:.2f} & {float(n["Idd_mA"]):.2f} & {float(z["in_5GHz_pA"]):.1f} \\\\')
(P / "table_gpdk_nom.tex").write_text("\n".join(out) + "\n")

# corners: min--max over 15 conditions
pk = lambda r, k: float(r["peak_dBohm"]) - float(r["Zt100M_dBohm"])
out = []
for c in names:
    z, b, p, i = span(c, "Zt100M_dBohm"), span(c, "f3dB_GHz"), span(c, None, pk), span(c, "Idd_mA")
    out.append(f'{names[c]} & {z[0]:.1f}--{z[1]:.1f} & {b[0]:.1f}--{b[1]:.1f} & {p[0]:.1f}--{p[1]:.1f} & {i[0]:.2f}--{i[1]:.2f} \\\\')
(P / "table_gpdk_corner.tex").write_text("\n".join(out) + "\n")

# Vtune sweep
out = [f'{float(r["vtn_V"]):.2f} & {float(r["Zt100M_dBohm"]):.2f} & {float(r["peak_dBohm"]) - float(r["Zt100M_dBohm"]):.2f} & {float(r["f3dB_GHz"]):.2f} \\\\' for r in sweep]
(P / "table_gpdk_tune.tex").write_text("\n".join(out) + "\n")
# conference version: short names, no GBW column
short = {"base2020": "2020 baseline", "regain": "Same-gain base.", "proposed": "Proposed"}
out = []
for c in short:
    n, z = nn35(c), noise[c]
    zt = float(n["Zt100M_dBohm"])
    out.append(f'{short[c]} & {zt:.1f} & {float(n["peak_dBohm"]) - zt:.1f} & {float(n["f3dB_GHz"]):.1f} & {float(n["Idd_mA"]):.2f} & {float(z["in_5GHz_pA"]):.1f} \\\\')
(P / "table_gpdk_nom_c.tex").write_text("\n".join(out) + "\n")
out = []
for c in short:
    z, b, p, i = span(c, "Zt100M_dBohm"), span(c, "f3dB_GHz"), span(c, None, pk), span(c, "Idd_mA")
    out.append(f'{short[c]} & {z[0]:.1f}--{z[1]:.1f} & {b[0]:.1f}--{b[1]:.1f} & {p[0]:.1f}--{p[1]:.1f} & {i[0]:.2f}--{i[1]:.2f} \\\\')
(P / "table_gpdk_corner_c.tex").write_text("\n".join(out) + "\n")
print("ok")

"""Write the user-facing files of every final design:
   ngspice .cir, LTspice .net + .asc (PTM90), Spectre .scs (PTM90 and gpdk090),
   one SKILL script that draws every schematic in Virtuoso with gpdk090 devices.
Designs come from ../results/designs.json (written by analyze.py)."""
import os, json, shutil
import lib, circuits as C

R = lib.ROOT
OUT = os.path.join(R, 'netlists')
HERE = lib.HERE
PINS = {
    'tia_nmos4': {'D': (48, 0, 0, -32), 'G': (0, 48, -32, 0), 'S': (48, 96, 0, 32), 'B': (80, 48, 32, 0)},
    'tia_pmos4': {'S': (48, 0, 0, -32), 'G': (0, 48, -32, 0), 'D': (48, 96, 0, 32), 'B': (80, 48, 32, 0)},
    'res': {'A': (16, 16, 0, -32), 'B': (16, 96, 0, 32)},
    'ind': {'A': (16, 16, 0, -32), 'B': (16, 96, 0, 32)},
    'cap': {'A': (16, 0, 0, -32), 'B': (16, 64, 0, 32)},
    'voltage': {'+': (0, 16, 0, -32), '-': (0, 96, 0, 32)},
    'current': {'+': (0, 0, 0, -32), '-': (0, 80, 0, 32)},
}


def place(el):
    """Simple grid: 6 columns, 224 x 208 LTspice units per cell."""
    return {e[1]: (224 * (i % 6), 208 * (i // 6)) for i, e in enumerate(el)}


def analyses_spice(br=5e9, ltspice=False):
    ui = 1 / br
    L = ['.ac dec 40 1Meg 100G', ';.noise V(out) Iin dec 40 1Meg 100G', ';.op']
    L += [f';.tran 0 {200*ui:.4g} {20*ui:.4g} {ui/50:.4g}   ; eye: replace Iin by the PRBS source below',
          f';Ipr 0 in PWL file=prbs7_{br/1e9:g}G.txt   ; 20 uA pk-pk NRZ PRBS7 (prbs7_*.txt is in this folder)']
    L += ['.meas AC zt0 FIND mag(V(out)) AT 10Meg', '.meas AC zpk MAX mag(V(out))',
          '.meas AC f3db WHEN mag(V(out))=zt0/sqrt(2) FALL=1']
    return L


def ngspice_file(name, title, el, br):
    t = [f'* {title}', f'* Run: ngspice -b {name}.cir   (PTM 90 nm BSIM4, VDD = 1 V)', '.include ptm90.lib', '.temp 35', '']
    t += lib.spice(el)
    t += ['', '.control', 'set noaskquit', 'op', 'print i(vdd) v(in) v(out)',
          'ac dec 40 1Meg 100G', 'let zt = vdb(out)', 'meas ac zt0 find zt at=10meg', 'meas ac zpk max zt',
          'let zm3 = zt0 - 3', 'meas ac f3db when zt=zm3 fall=1', f'wrdata {name}_ac.txt vdb(out) vp(out)',
          'noise v(out) iin dec 40 1Meg 100G', 'setplot noise1', f'wrdata {name}_noise.txt inoise_spectrum',
          '.endc', '.end', '']
    open(os.path.join(OUT, 'ngspice', name + '.cir'), 'w').write('\n'.join(t))


def ltspice_net(name, title, el, br):
    t = [f'* {title}', '* LTspice: File > Open (All files) > this .net > Run.  Keep ptm90.lib in this folder.',
         '* One analysis at a time: un-comment the one you want with ";" removed.', '.include ptm90.lib', '.temp 35', '']
    t += lib.spice(el, ltspice=True)
    t += [''] + analyses_spice(br, True) + ['.backanno', '.end', '']
    open(os.path.join(OUT, 'ltspice', name + '.net'), 'w').write('\n'.join(t))


def asc_items(el):
    items = []
    for e in el:
        k, n = e[0], e[1]
        if k == 'M':
            _, _, d, g, s, b, t, w, l = e
            ad, pd = lib.geom(w)
            items.append(('tia_nmos4' if t == 'n' else 'tia_pmos4', n, 'nmos90' if t == 'n' else 'pmos90',
                          f'l={l:g}n w={w:.4g}u ad={ad:.4g}p as={ad:.4g}p pd={pd:.4g}u ps={pd:.4g}u',
                          {'D': d, 'G': g, 'S': s, 'B': b}))
        elif k in 'RLC':
            items.append(({'R': 'res', 'L': 'ind', 'C': 'cap'}[k], n, lib.fmt(e[4]), None, {'A': e[2], 'B': e[3]}))
        elif k == 'V':
            items.append(('voltage', n, lib.fmt(e[4]), None, {'+': e[2], '-': e[3]}))
        elif k == 'I':
            v = lib.fmt(e[4]) + (f' AC {e[5]}' if len(e) > 5 and e[5] else '')
            items.append(('current', n, v, None, {'+': e[2], '-': e[3]}))
    return items


def ltspice_asc(name, title, el, br):
    P = place(el)
    L = ['Version 4', 'SHEET 1 1600 1400']
    wires, flags, syms = [], [], []
    for sym, n, val, val2, pins in asc_items(el):
        x, y = P[n]
        for pn, net in pins.items():
            dx, dy, sx, sy = PINS[sym][pn]
            wires.append(f'WIRE {x+dx} {y+dy} {x+dx+sx} {y+dy+sy}')
            flags.append(f'FLAG {x+dx+sx} {y+dy+sy} {net}')
        syms += [f'SYMBOL {sym} {x} {y} R0', f'SYMATTR InstName {n}', f'SYMATTR Value {val}']
        if val2:
            syms.append(f'SYMATTR Value2 {val2}')
    L += wires + flags + syms
    ty = 208 * ((len(el) + 5) // 6) + 64
    for s in ['!.include ptm90.lib', '!.temp 35'] + [('!' if not a.startswith(';') else '') + a for a in analyses_spice(br, True)] + \
             [f';{title}', ';Nets are joined by label (same name = same net). Zt = V(out) for the 1 A AC source Iin.']:
        L.append(f'TEXT 0 {ty} Left 2 {s}'); ty += 32
    open(os.path.join(OUT, 'ltspice', name + '.asc'), 'w').write('\n'.join(L) + '\n')


def spectre_file(name, title, el, pdk):
    t = [f'// {title}', f'// Run:  spectre {name}.scs', 'simulator lang=spectre', 'global 0']
    if pdk == 'ptm':
        t += ['include "ptm90.lib"   // SPICE-syntax PTM card (Spectre reads it as SPICE)', '']
        body = lib.spectre(el)
        body = [l.replace(' nmos1v ', ' nmos90 ').replace(' pmos1v ', ' pmos90 ') for l in body]
    else:
        t += ['// gpdk090: set the path to your kit. Sections: NN FF SS FS SF',
              'include "/path/to/gpdk090_v4.6/models/spectre/gpdk090.scs" section=NN', '']
        body = lib.spectre(el)
    t += body
    t += ['', 'simOpts options temp=35 tnom=27 reltol=1e-4 save=allpub',
          'dcOp dc oppoint=logfile',
          'acZt ac start=1M stop=100G dec=40',
          'noiseIn (out 0) noise start=1M stop=100G dec=40 iprobe=Iin']
    if pdk == 'gpdk':
        t += ['// corners x temperature (uncomment):',
              '// alter / altergroup in ADE Explorer/Assembler is easier: corners NN SS FF FS SF, temp -40 35 125, VDD 0.9 1.0 1.1']
    open(os.path.join(OUT, 'cadence_' + pdk, name + '.scs'), 'w').write('\n'.join(t) + '\n')


SKILL_HEAD = r''';; Draws every TIA of the 2025 redesign study as a Virtuoso schematic with gpdk090 devices.
;; CIW:  load("build_gpdk090_schematics.il")  tia25BuildAll("TIA25")   (library TIA25 must exist,
;; attached to gpdk090).  NMOS/PMOS = gpdk090 nmos1v/pmos1v, passives and sources = analogLib.
;; Nets are joined by wire labels (same name = same net).  Generated outside Cadence: if a pin
;; name differs in your kit version (D G S B), edit tia25Place.
procedure( tia25Place(cv lib cell name x y props nets)
  let( (master inst term fig c pt pt2 w)
    master = dbOpenCellViewByType(lib cell "symbol")
    unless(master error("no master %s %s" lib cell))
    inst = dbCreateParamInst(cv master name list(x y) "R0" 1 props)
    foreach(n nets
      term = dbFindTermByName(master car(n))
      fig = car(term~>pins)~>fig
      c = centerBox(fig~>bBox)
      pt = dbTransformPoint(c inst~>transform)
      pt2 = list(xCoord(pt)+caddr(n) yCoord(pt)+cadddr(n))
      w = schCreateWire(cv "draw" "full" list(pt pt2) 0.0625 0.0625 0.0)
      schCreateWireLabel(cv car(w) pt2 cadr(n) "lowerLeft" "R0" "stick" 0.0625 nil))
    inst))
'''


def skill(designs):
    L = [SKILL_HEAD]
    net = lambda n: 'gnd!' if n == '0' else n
    for name, (title, el) in designs.items():
        P = place(el)
        L.append(f';; {title}')
        L.append(f'procedure( tia25_{name}(lib)\n  let( (cv)\n    cv = dbOpenCellViewByType(lib "{name}" "schematic" "schematic" "w")')
        for e in el:
            k, n = e[0], e[1]
            x, y = P[n][0] / 64.0, -P[n][1] / 64.0
            if k == 'M':
                _, _, d, g, s, b, t, w, l = e
                l = max(l, 100)
                props = [('w', f'{w:.4g}u'), ('fw', f'{w:.4g}u'), ('l', f'{l:g}n'), ('fingers', '1'), ('m', '1')]
                nets = [('D', net(d), 0, 0.25 if t == 'n' else -0.25), ('G', net(g), -0.25, 0),
                        ('S', net(s), 0, -0.25 if t == 'n' else 0.25), ('B', net(b), 0.25, 0)]
                lb, cell = 'gpdk090', 'nmos1v' if t == 'n' else 'pmos1v'
            else:
                cell, pn = {'R': ('res', 'r'), 'C': ('cap', 'c'), 'L': ('ind', 'l'), 'V': ('vdc', 'vdc'), 'I': ('idc', 'idc')}[k]
                props = [(pn, lib.fmt(e[4]))]
                if k == 'I' and len(e) > 5 and e[5]:
                    props.append(('acm', str(e[5])))
                nets = [('PLUS', net(e[2]), 0, 0.25), ('MINUS', net(e[3]), 0, -0.25)]
                lb = 'analogLib'
            ps = ' '.join(f'list("{a}" "string" "{b}")' for a, b in props)
            ns = ' '.join(f'list("{a}" "{b}" {c:g} {d_:g})' for a, b, c, d_ in nets)
            L.append(f'    tia25Place(cv "{lb}" "{cell}" "{n}" {x:g} {y:g} list({ps}) list({ns}))')
        L.append('    schCheck(cv) dbSave(cv) dbClose(cv) t))\n')
    L.append('procedure( tia25BuildAll(lib) ' + ' '.join(f'tia25_{n}(lib)' for n in designs) + ' )\n')
    open(os.path.join(OUT, 'cadence_gpdk', 'build_gpdk090_schematics.il'), 'w').write('\n'.join(L))


def prbs7_file(br, amp=20e-6, nbits=254, tr=0.1):
    """Current PWL for an NRZ PRBS7 between 0 and amp (into node in)."""
    s = [1] * 7; bits = []
    for _ in range(nbits):
        b = s[6] ^ s[5]; bits.append(s[6]); s = [b] + s[:6]
    ui = 1 / br; pts = [(0, 0)]
    for i, b in enumerate(bits):
        v = amp * b
        pts += [(i * ui + tr * ui, v), ((i + 1) * ui, v)]
    return bits, pts


def emit(designs, br=5e9):
    for d in ('ngspice', 'ltspice', 'cadence_ptm', 'cadence_gpdk'):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    for d in ('ngspice', 'ltspice', 'cadence_ptm'):
        shutil.copy(lib.MODEL, os.path.join(OUT, d, 'ptm90.lib'))
    open(os.path.join(OUT, 'ltspice', 'tia_nmos4.asy'), 'w').write(open(os.path.join(HERE, 'ASY_N.txt')).read())
    open(os.path.join(OUT, 'ltspice', 'tia_pmos4.asy'), 'w').write(open(os.path.join(HERE, 'ASY_P.txt')).read())
    _, pts = prbs7_file(br)
    for d in ('ngspice', 'ltspice'):
        open(os.path.join(OUT, d, f'prbs7_{br/1e9:g}G.txt'), 'w').write('\n'.join(f'{t:.6g} {v:.6g}' for t, v in pts) + '\n')
    for name, (title, el) in designs.items():
        ngspice_file(name, title, el, br); ltspice_net(name, title, el, br); ltspice_asc(name, title, el, br)
        spectre_file(name, title, el, 'ptm'); spectre_file(name, title, el, 'gpdk')
    skill(designs)

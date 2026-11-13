;; Builds Virtuoso schematics of the baseline and proposed TIAs from analogLib parts.
;; Usage in the CIW:   load("build_tia_schematics.il")   tiaBuildAll("TIA_LIB")
;; The library TIA_LIB must already exist (File > New > Library, no tech file needed).
;; Devices are analogLib nmos4/pmos4 with model names nmos90/pmos90: add ptm90.lib under
;; ADE > Setup > Model Libraries. Nets are connected by wire labels (same name = same net).
;; NOTE: generated without access to a Cadence installation, so it has not been executed.
;;       The Spectre netlists (*.scs) in this folder are the verified-by-construction reference.

procedure( tiaPlace(cv cell name x y props nets)
  let( (master inst term fig c pt pt2 w)
    master = dbOpenCellViewByType("analogLib" cell "symbol")
    inst = dbCreateInst(cv master name list(x y) "R0")
    foreach(p props dbReplaceProp(inst car(p) "string" cadr(p)))
    foreach(n nets
      term = dbFindTermByName(master car(n))
      fig = car(term~>pins)~>fig
      c = centerBox(fig~>bBox)
      pt = dbTransformPoint(c inst~>transform)
      pt2 = list(xCoord(pt)+caddr(n) yCoord(pt)+cadddr(n))
      w = schCreateWire(cv "draw" "full" list(pt pt2) 0.0625 0.0625 0.0)
      schCreateWireLabel(cv car(w) pt2 cadr(n) "lowerLeft" "R0" "stick" 0.0625 nil)
    )
    inst))

procedure( tiaBuild_baseline_tia(lib)
  let( (cv)
    cv = dbOpenCellViewByType(lib "baseline_tia" "schematic" "schematic" "w")
    tiaPlace(cv "vdc" "Vdd" -3.125 -0.5 list(list("vdc" "vdd")) list(list("PLUS" "vdd" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "vdc" "Vg3b" -1.875 -0.5 list(list("vdc" "vg3b")) list(list("PLUS" "g3b" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "pmos4" "M2b" 0.125 0 list(list("model" "pmos90") list("w" "0.9u") list("l" "90n") list("as" "0.18p") list("ad" "0.18p") list("ps" "2.2u") list("pd" "2.2u")) list(list("D" "n" 0 -0.25) list("G" "vdd" -0.25 0) list("S" "vdd" 0 0.25) list("B" "vdd" 0.25 0)))
    tiaPlace(cv "nmos4" "M1" 0.125 -1.625 list(list("model" "nmos90") list("w" "5u") list("l" "90n") list("as" "1p") list("ad" "1p") list("ps" "10.4u") list("pd" "10.4u")) list(list("D" "n" 0 0.25) list("G" "vdd" -0.25 0) list("S" "in" 0 -0.25) list("B" "gnd!" 0.25 0)))
    tiaPlace(cv "nmos4" "M2" 0.125 -3.25 list(list("model" "nmos90") list("w" "5u") list("l" "90n") list("as" "1p") list("ad" "1p") list("ps" "10.4u") list("pd" "10.4u")) list(list("D" "in" 0 0.25) list("G" "n" -0.25 0) list("S" "gnd!" 0 -0.25) list("B" "gnd!" 0.25 0)))
    tiaPlace(cv "nmos4" "M3" 3.75 -3.25 list(list("model" "nmos90") list("w" "5u") list("l" "90n") list("as" "1p") list("ad" "1p") list("ps" "10.4u") list("pd" "10.4u")) list(list("D" "out" 0 0.25) list("G" "n" -0.25 0) list("S" "gnd!" 0 -0.25) list("B" "gnd!" 0.25 0)))
    tiaPlace(cv "pmos4" "M3b" 3.75 0 list(list("model" "pmos90") list("w" "5u") list("l" "90n") list("as" "1p") list("ad" "1p") list("ps" "10.4u") list("pd" "10.4u")) list(list("D" "out" 0 -0.25) list("G" "g3b" -0.25 0) list("S" "vdd" 0 0.25) list("B" "vdd" 0.25 0)))
    tiaPlace(cv "ind" "Lf" 2 -1.75 list(list("l" "lf")) list(list("PLUS" "out" 0 0.25) list("MINUS" "in" 0 -0.25)))
    tiaPlace(cv "cap" "Cpd" -2 -3 list(list("c" "cpd")) list(list("PLUS" "in" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "cap" "Cout" 5.625 -3 list(list("c" "cout")) list(list("PLUS" "out" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "idc" "Iin" -3.125 -3 list(list("idc" "0") list("acm" "1")) list(list("PLUS" "gnd!" 0 0.25) list("MINUS" "in" 0 -0.25)))
    schCheck(cv)
    dbSave(cv)
    dbClose(cv)
    t))

;; design variables for baseline_tia: vdd=1.0, cpd=50f, cout=30f, lf=2.4n, vg3b=0.0, temp=35
procedure( tiaBuild_proposed_tia(lib)
  let( (cv)
    cv = dbOpenCellViewByType(lib "proposed_tia" "schematic" "schematic" "w")
    tiaPlace(cv "vdc" "Vdd" -5.625 -0.5 list(list("vdc" "vdd")) list(list("PLUS" "vdd" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "vdc" "Vtune" -4.375 -0.5 list(list("vdc" "vtune")) list(list("PLUS" "vt" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "idc" "Iref" -5.625 -2.5 list(list("idc" "iref")) list(list("PLUS" "vbp" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "pmos4" "Mbp" -3.25 0 list(list("model" "pmos90") list("w" "2u") list("l" "180n") list("as" "0.4p") list("ad" "0.4p") list("ps" "4.4u") list("pd" "4.4u")) list(list("D" "vbp" 0 -0.25) list("G" "vbp" -0.25 0) list("S" "vdd" 0 0.25) list("B" "vdd" 0.25 0)))
    tiaPlace(cv "pmos4" "Mbr" -1.625 0 list(list("model" "pmos90") list("w" "2u") list("l" "180n") list("as" "0.4p") list("ad" "0.4p") list("ps" "4.4u") list("pd" "4.4u")) list(list("D" "vb1" 0 -0.25) list("G" "vbp" -0.25 0) list("S" "vdd" 0 0.25) list("B" "vdd" 0.25 0)))
    tiaPlace(cv "nmos4" "Mbn" -1.625 -1.625 list(list("model" "nmos90") list("w" "0.4u") list("l" "90n") list("as" "0.08p") list("ad" "0.08p") list("ps" "1.2u") list("pd" "1.2u")) list(list("D" "vb1" 0 0.25) list("G" "vb1" -0.25 0) list("S" "vr" 0 -0.25) list("B" "gnd!" 0.25 0)))
    tiaPlace(cv "res" "Rb" -1.375 -3.125 list(list("r" "rb")) list(list("PLUS" "vr" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "cap" "Cb" -0.5 -2 list(list("c" "cb")) list(list("PLUS" "vb1" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "res" "Rn" 0.375 -0.125 list(list("r" "rn")) list(list("PLUS" "vdd" 0 0.25) list("MINUS" "n" 0 -0.25)))
    tiaPlace(cv "nmos4" "M1" 0.125 -1.625 list(list("model" "nmos90") list("w" "4.5u") list("l" "90n") list("as" "0.9p") list("ad" "0.9p") list("ps" "9.4u") list("pd" "9.4u")) list(list("D" "n" 0 0.25) list("G" "vb1" -0.25 0) list("S" "in" 0 -0.25) list("B" "gnd!" 0.25 0)))
    tiaPlace(cv "nmos4" "M2" 0.125 -3.25 list(list("model" "nmos90") list("w" "3.5u") list("l" "90n") list("as" "0.7p") list("ad" "0.7p") list("ps" "7.4u") list("pd" "7.4u")) list(list("D" "in" 0 0.25) list("G" "n" -0.25 0) list("S" "gnd!" 0 -0.25) list("B" "gnd!" 0.25 0)))
    tiaPlace(cv "nmos4" "M3" 5.375 -3.25 list(list("model" "nmos90") list("w" "7u") list("l" "90n") list("as" "1.4p") list("ad" "1.4p") list("ps" "14.4u") list("pd" "14.4u")) list(list("D" "out" 0 0.25) list("G" "n" -0.25 0) list("S" "gnd!" 0 -0.25) list("B" "gnd!" 0.25 0)))
    tiaPlace(cv "pmos4" "M3b" 5.375 0 list(list("model" "pmos90") list("w" "28u") list("l" "180n") list("as" "5.6p") list("ad" "5.6p") list("ps" "56.4u") list("pd" "56.4u")) list(list("D" "out" 0 -0.25) list("G" "vbp" -0.25 0) list("S" "vdd" 0 0.25) list("B" "vdd" 0.25 0)))
    tiaPlace(cv "nmos4" "Mf" 2 -1.625 list(list("model" "nmos90") list("w" "3.5u") list("l" "90n") list("as" "0.7p") list("ad" "0.7p") list("ps" "7.4u") list("pd" "7.4u")) list(list("D" "vdd" 0 0.25) list("G" "g" -0.25 0) list("S" "in" 0 -0.25) list("B" "gnd!" 0.25 0)))
    tiaPlace(cv "pmos4" "Mt" 3.5 -1.625 list(list("model" "pmos90") list("w" "12u") list("l" "90n") list("as" "2.4p") list("ad" "2.4p") list("ps" "24.4u") list("pd" "24.4u")) list(list("D" "g" 0 -0.25) list("G" "vt" -0.25 0) list("S" "out" 0 0.25) list("B" "out" 0.25 0)))
    tiaPlace(cv "cap" "Ca" 2.125 -3.125 list(list("c" "ca")) list(list("PLUS" "g" 0 0.25) list("MINUS" "in" 0 -0.25)))
    tiaPlace(cv "cap" "Cpd" -4.375 -4.375 list(list("c" "cpd")) list(list("PLUS" "in" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "cap" "Cout" 7.25 -3.125 list(list("c" "cout")) list(list("PLUS" "out" 0 0.25) list("MINUS" "gnd!" 0 -0.25)))
    tiaPlace(cv "idc" "Iin" -5.625 -4.375 list(list("idc" "0") list("acm" "1")) list(list("PLUS" "gnd!" 0 0.25) list("MINUS" "in" 0 -0.25)))
    schCheck(cv)
    dbSave(cv)
    dbClose(cv)
    t))

;; design variables for proposed_tia: vdd=1.0, cpd=50f, cout=30f, iref=50u, vtune=0.28, rn=5k, rb=4.2k, ca=30f, cb=2p, temp=35
procedure( tiaBuildAll(lib) tiaBuild_baseline_tia(lib) tiaBuild_proposed_tia(lib) )

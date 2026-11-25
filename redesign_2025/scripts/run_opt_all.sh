#!/bin/bash
for c in cm_nrc_d1 cm_nrc_out mdfrgc rgc cm_rgc shaaban_L shaaban_AN shaaban_AP pf_tia; do
  python3 optimize.py $c 40 1.5 2.5 >> ../results/opt_log.txt 2>&1
done
echo DONE >> ../results/opt_log.txt

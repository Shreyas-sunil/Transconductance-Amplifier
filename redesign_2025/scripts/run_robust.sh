#!/bin/bash
cd "$(dirname "$0")"
for c in cm_nrc_d1 mdfrgc cm_rgc rgc; do
  ROBUST=1 python3 optimize.py $c 30 1.5 2.5 >> ../results/robust_log.txt 2>&1
done
echo DONE >> ../results/robust_log.txt

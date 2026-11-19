#!/bin/sh
# usage: sh run.sh selftest | all | <task...>
cd "$(dirname "$0")"
export OUT=$HOME/exchange/tia_results WORK=/tmp/tia_work
python2 tia.py "$@" 2>&1 | tee -a $OUT.console.log
cd $HOME/exchange && tar czf ${TGZ:-tia_results}.tgz tia_results && ls -la tia_results.tgz

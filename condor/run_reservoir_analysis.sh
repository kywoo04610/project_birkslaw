#!/bin/bash
set -euo pipefail

ENERGY="${1:?Usage: run_reservoir_analysis.sh 100GeV|300GeV}"

case "$ENERGY" in
    100GeV|300GeV) ;;
    *)
        echo "ERROR: unsupported energy: $ENERGY" >&2
        exit 2
        ;;
esac

PROJECT_DIR="/afs/cern.ch/work/y/ykim/project_birkslaw"
OUTPUT_DIR="$PROJECT_DIR/analysis/results_reservoir_full_${ENERGY}"

source /cvmfs/sndlhc.cern.ch/SNDLHC-2025/Oct7/setUp.sh
cd /afs/cern.ch/work/y/ykim/SNDBUILD
eval "$(alienv load sndsw/latest-master-release --no-refresh)"

cd "$PROJECT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "Reservoir analysis start: $(date --iso-8601=seconds)"
echo "Host: $(hostname)"
echo "Energy: $ENERGY"
echo "Output: $OUTPUT_DIR"
echo "SNDSW_ROOT: $SNDSW_ROOT"
echo "ROOT: $(root-config --version)"
echo "Python: $(python3 --version)"

python3 analysis/analyze_qdc_reservoir.py \
    --energies "$ENERGY" \
    --max-events 15000 \
    --max-scanned-events -1 \
    --file-check-events 1 \
    --min-scifi-hits 200 \
    --data-sampling reservoir \
    --random-seed 42 \
    --progress-every 100000 \
    --output-dir "$OUTPUT_DIR"

echo "Reservoir analysis completed: $(date --iso-8601=seconds)"

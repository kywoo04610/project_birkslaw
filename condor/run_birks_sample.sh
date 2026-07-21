#!/bin/bash
set -eo pipefail

PID="$1"
ENERGY="$2"
RUN_ID="$3"
SAMPLE_NAME="$4"

BUILD_DIR="/afs/cern.ch/work/y/ykim/SNDBUILD"
OUTPUT_DIR="/eos/user/y/ykim/project_birkslaw/birks_samples/${SAMPLE_NAME}"

source /cvmfs/sndlhc.cern.ch/SNDLHC-2025/Oct7/setUp.sh

cd "$BUILD_DIR"
eval "$(alienv load sndsw/latest-master-release --no-refresh)"
set -u

echo "Starting sample: $SAMPLE_NAME"
echo "Particle ID: $PID"
echo "Energy: $ENERGY GeV"
echo "PGrunID: $RUN_ID"
echo "SNDSW_ROOT: $SNDSW_ROOT"
echo "ROOT version: $(root-config --version)"

python "$SNDSW_ROOT/shipLHC/run_simSND.py" \
    --PG \
    --pID "$PID" \
    --Estart "$ENERGY" \
    --Eend "$ENERGY" \
    --EVx -38 \
    --EVy 44 \
    --EVz 310 \
    -n 100 \
    --HX \
    --PGrunID "$RUN_ID" \
    -o "$OUTPUT_DIR"

SIM_FILE="sndLHC.PG_${PID}-TGeant4.root"
GEO_FILE="geofile_full.PG_${PID}-TGeant4.root"

test -s "$SIM_FILE"
test -s "$GEO_FILE"

python "$SNDSW_ROOT/shipLHC/run_digiSND.py" \
    -f "$SIM_FILE" \
    -g "$GEO_FILE" \
    -cpp

DIGI_FILE="sndLHC.PG_${PID}-TGeant4_digCPP.root"
test -s "$DIGI_FILE"

echo "Completed sample: $SAMPLE_NAME"
ls -lh "$OUTPUT_DIR"
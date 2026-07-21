#!/bin/bash
set -eo pipefail

PID="$1"
SAMPLE_NAME="$2"

BUILD_DIR="/afs/cern.ch/work/y/ykim/SNDBUILD"
OUTPUT_DIR="/eos/user/y/ykim/project_birkslaw/birks_samples/${SAMPLE_NAME}"

source /cvmfs/sndlhc.cern.ch/SNDLHC-2025/Oct7/setUp.sh

cd "$BUILD_DIR"
eval "$(alienv load sndsw/latest-master-release --no-refresh)"
set -u

cd "$OUTPUT_DIR"

SIM_FILE="sndLHC.PG_${PID}-TGeant4.root"
GEO_FILE="geofile_full.PG_${PID}-TGeant4.root"
DIGI_FILE="sndLHC.PG_${PID}-TGeant4_digCPP.root"

test -s "$SIM_FILE"
test -s "$GEO_FILE"

echo "Starting digitization: $SAMPLE_NAME"
echo "Input: $SIM_FILE"
echo "Geometry: $GEO_FILE"
echo "ROOT version: $(root-config --version)"

python "$SNDSW_ROOT/shipLHC/run_digiSND.py" \
    -f "$SIM_FILE" \
    -g "$GEO_FILE" \
    -cpp

test -s "$DIGI_FILE"

echo "Completed digitization: $SAMPLE_NAME"
ls -lh "$DIGI_FILE"
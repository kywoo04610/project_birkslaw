#!/bin/bash
set -eo pipefail

PID="$1"
ENERGY="$2"
RUN_ID="$3"
SAMPLE_NAME="$4"
BATCH="$5"

BUILD_DIR="/afs/cern.ch/work/y/ykim/SNDBUILD"
OUTPUT_BASE="/eos/user/y/ykim/project_birkslaw/birks_samples_10k"

# Convert 0, 1, ..., 99 into 000, 001, ..., 099.
printf -v BATCH_PADDED "%03d" "$BATCH"

OUTPUT_DIR="${OUTPUT_BASE}/${SAMPLE_NAME}/batch_${BATCH_PADDED}"

# Keep nounset disabled while loading the SND environment.
source /cvmfs/sndlhc.cern.ch/SNDLHC-2025/Oct7/setUp.sh

cd "$BUILD_DIR"
eval "$(alienv load sndsw/latest-master-release --no-refresh)"
set -u

mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

echo "Starting sample: $SAMPLE_NAME"
echo "Batch: $BATCH_PADDED"
echo "Particle ID: $PID"
echo "Energy: $ENERGY GeV"
echo "PGrunID: $RUN_ID"
echo "Output directory: $OUTPUT_DIR"
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
echo "Completed batch: $BATCH_PADDED"
ls -lh "$OUTPUT_DIR"
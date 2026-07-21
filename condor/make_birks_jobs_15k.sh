#!/bin/bash
set -euo pipefail

JOB_FILE="birks_jobs_15k.txt"

# 기존 파일이 있다면 새로 작성
: > "$JOB_FILE"

# 100 GeV pi+
# batch: 0~149
# run ID: 12000~12149
for batch in $(seq 0 149); do
    run_id=$((12000 + batch))

    printf "211 100 %d piPlus_100GeV_15k %d\n" \
        "$run_id" "$batch" >> "$JOB_FILE"
done

# 300 GeV pi-
# batch: 0~149
# run ID: 32000~32149
for batch in $(seq 0 149); do
    run_id=$((32000 + batch))

    printf "%d 300 %d piMinus_300GeV_15k %d\n" \
        "-211" "$run_id" "$batch" >> "$JOB_FILE"
done

echo "Created: $JOB_FILE"
echo "Number of jobs: $(wc -l < "$JOB_FILE")"

echo
echo "First entries:"
head -n 3 "$JOB_FILE"

echo
echo "Last entries:"
tail -n 3 "$JOB_FILE"
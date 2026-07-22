#!/usr/bin/env python3
"""Validate the final EOS outputs of the SND@LHC 15k Birks MC production."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_BASE = Path("/eos/user/y/ykim/project_birkslaw/birks_samples_15k")
DEFAULT_OUTPUT = Path("production/15k/eos_validation")

SAMPLES = (
    {
        "sample": "piPlus_100GeV_15k",
        "pdg_id": 211,
        "energy_GeV": 100,
        "runid_first": 12000,
        "filename": "sndLHC.PG_211-TGeant4_digCPP.root",
    },
    {
        "sample": "piMinus_300GeV_15k",
        "pdg_id": -211,
        "energy_GeV": 300,
        "runid_first": 32000,
        "filename": "sndLHC.PG_-211-TGeant4_digCPP.root",
    },
)

EXPECTED_BATCHES = 150
EXPECTED_ENTRIES = 100
EXPECTED_TREE = "cbmsim"
EXPECTED_BRANCH = "Digi_MuFilterHits"

CSV_FIELDS = (
    "sample",
    "pdg_id",
    "energy_GeV",
    "batch",
    "pgrunid",
    "path",
    "exists",
    "size_bytes",
    "mtime_utc",
    "root_open_ok",
    "is_zombie",
    "tree_exists",
    "entries",
    "expected_entries",
    "branch_exists",
    "sha256",
    "valid",
    "error",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate all 300 digitized ROOT files in the 15k Birks MC production."
    )
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--sha256",
        action="store_true",
        help="Calculate SHA-256 for every ROOT file (slow and I/O intensive).",
    )
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_file(path: Path, calculate_sha256: bool) -> dict:
    import ROOT

    result = {
        "exists": path.is_file(),
        "size_bytes": None,
        "mtime_utc": "",
        "root_open_ok": False,
        "is_zombie": None,
        "tree_exists": False,
        "entries": None,
        "expected_entries": EXPECTED_ENTRIES,
        "branch_exists": False,
        "sha256": "",
        "valid": False,
        "error": "",
    }

    if not result["exists"]:
        result["error"] = "missing file"
        return result

    try:
        stat = path.stat()
        result["size_bytes"] = stat.st_size
        result["mtime_utc"] = datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat()
    except OSError as exc:
        result["error"] = f"stat failed: {exc}"
        return result

    if result["size_bytes"] <= 0:
        result["error"] = "empty file"
        return result

    root_file = None
    try:
        root_file = ROOT.TFile.Open(str(path), "READ")
        result["root_open_ok"] = bool(root_file)
        if not root_file:
            result["error"] = "ROOT.TFile.Open returned null"
            return result

        result["is_zombie"] = bool(root_file.IsZombie())
        if result["is_zombie"]:
            result["error"] = "ROOT file is zombie"
            return result

        tree = root_file.Get(EXPECTED_TREE)
        result["tree_exists"] = bool(tree)
        if not tree:
            result["error"] = f"missing tree: {EXPECTED_TREE}"
            return result

        result["entries"] = int(tree.GetEntries())
        result["branch_exists"] = bool(tree.GetBranch(EXPECTED_BRANCH))

        errors = []
        if result["entries"] != EXPECTED_ENTRIES:
            errors.append(
                f"entries={result['entries']} expected={EXPECTED_ENTRIES}"
            )
        if not result["branch_exists"]:
            errors.append(f"missing branch: {EXPECTED_BRANCH}")

        if errors:
            result["error"] = "; ".join(errors)
            return result

        if calculate_sha256:
            result["sha256"] = file_sha256(path)

        result["valid"] = True
        return result
    except Exception as exc:  # PyROOT can surface several exception classes.
        result["error"] = f"exception: {type(exc).__name__}: {exc}"
        return result
    finally:
        if root_file:
            root_file.Close()


def discover_batch_directories(sample_dir: Path) -> tuple[list[int], list[str]]:
    batches = []
    unrecognized = []
    pattern = re.compile(r"^batch_(\d+)$")

    if not sample_dir.is_dir():
        return batches, unrecognized

    for path in sorted(sample_dir.iterdir()):
        if not path.is_dir():
            continue
        match = pattern.match(path.name)
        if match:
            batches.append(int(match.group(1)))
        else:
            unrecognized.append(path.name)
    return batches, unrecognized


def main() -> int:
    args = parse_args()
    try:
        import ROOT
    except ImportError:
        print(
            "ERROR: PyROOT is unavailable. Load the SND software environment first.",
            file=sys.stderr,
        )
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ROOT.gROOT.SetBatch(True)

    rows = []
    sample_summaries = []

    for config in SAMPLES:
        sample = config["sample"]
        sample_dir = args.base / sample
        discovered, unrecognized = discover_batch_directories(sample_dir)
        expected_set = set(range(EXPECTED_BATCHES))
        discovered_set = set(discovered)
        missing_directories = sorted(expected_set - discovered_set)
        extra_directories = sorted(discovered_set - expected_set)

        duplicate_candidates = []
        if sample_dir.is_dir():
            for batch_dir in sorted(sample_dir.glob("batch_*")):
                matches = list(batch_dir.rglob(config["filename"]))
                if len(matches) > 1:
                    duplicate_candidates.append(
                        {"batch_directory": batch_dir.name, "paths": [str(x) for x in matches]}
                    )

        valid_count = 0
        total_entries = 0

        for batch in range(EXPECTED_BATCHES):
            path = sample_dir / f"batch_{batch:03d}" / config["filename"]
            validation = validate_file(path, args.sha256)
            row = {
                "sample": sample,
                "pdg_id": config["pdg_id"],
                "energy_GeV": config["energy_GeV"],
                "batch": batch,
                "pgrunid": config["runid_first"] + batch,
                "path": str(path),
                **validation,
            }
            rows.append(row)
            if row["valid"]:
                valid_count += 1
                total_entries += int(row["entries"])

            status = "OK" if row["valid"] else f"FAIL: {row['error']}"
            print(f"[{sample}] batch {batch:03d}: {status}", flush=True)

        sample_summaries.append(
            {
                "sample": sample,
                "expected_batches": EXPECTED_BATCHES,
                "discovered_batch_directories": len(discovered),
                "valid_files": valid_count,
                "invalid_files": EXPECTED_BATCHES - valid_count,
                "valid_entries": total_entries,
                "expected_entries": EXPECTED_BATCHES * EXPECTED_ENTRIES,
                "missing_batch_directories": missing_directories,
                "extra_batch_directories": extra_directories,
                "unrecognized_directories": unrecognized,
                "duplicate_file_candidates": duplicate_candidates,
                "validated": (
                    valid_count == EXPECTED_BATCHES
                    and total_entries == EXPECTED_BATCHES * EXPECTED_ENTRIES
                    and not missing_directories
                    and not extra_directories
                    and not unrecognized
                    and not duplicate_candidates
                ),
            }
        )

    csv_path = args.output_dir / "eos_file_validation.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    overall_valid = all(item["validated"] for item in sample_summaries)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base": str(args.base),
        "sha256_enabled": args.sha256,
        "expected_tree": EXPECTED_TREE,
        "expected_branch": EXPECTED_BRANCH,
        "expected_entries_per_file": EXPECTED_ENTRIES,
        "overall_valid": overall_valid,
        "samples": sample_summaries,
    }

    json_path = args.output_dir / "eos_validation_summary.json"
    with json_path.open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")

    print(f"\nCSV:  {csv_path}")
    print(f"JSON: {json_path}")
    print(f"Overall validation: {'PASS' if overall_valid else 'FAIL'}")
    return 0 if overall_valid else 1


if __name__ == "__main__":
    sys.exit(main())

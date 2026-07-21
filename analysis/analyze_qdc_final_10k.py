#!/usr/bin/env python3

from collections import defaultdict
from glob import glob
from pathlib import Path
import argparse
import csv
import math

import ROOT

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


DEFAULT_OUTPUT_DIR = Path(
    "/afs/cern.ch/work/y/ykim/project_birkslaw/analysis/results_cutflow_filecheck"
)

DEFAULT_FILE_CHECK_EVENTS = 10000

CHANNELS = [0, 1, 3, 4, 6, 7, 8, 9, 11, 12, 14, 15]

COLORS = {
    "Birks MC": "tab:blue",
    "No-Birks MC": "tab:orange",
    "Data": "black",
}


DATASETS = {
    "100GeV": {
        "Birks MC": {
            "tree": "cbmsim",
            "files": sorted(
                glob(
                    "/eos/user/y/ykim/project_birkslaw/birks_samples_10k/"
                    "piPlus_100GeV/batch_*/"
                    "sndLHC.PG_211-TGeant4_digCPP.root"
                )
            ),
        },
        "No-Birks MC": {
            "tree": "cbmsim",
            "files": [
                "/eos/experiment/sndlhc/MonteCarlo/testbeam2023/"
                "2mmRangeCut/100GeV_211/"
                "sndLHC.PG_211-TGeant4_MCEB_dig.root"
            ],
        },
        "Data": {
            "tree": "rawConv",
            "files": sorted(
                glob(
                    "/eos/experiment/sndlhc/convertedData/commissioning/"
                    "testbeam_June2023_H8/run_100630/sndsw_raw-*.root"
                )
            ),
        },
    },
    "300GeV": {
        "Birks MC": {
            "tree": "cbmsim",
            "files": sorted(
                glob(
                    "/eos/user/y/ykim/project_birkslaw/birks_samples_10k/"
                    "piMinus_300GeV/batch_*/"
                    "sndLHC.PG_-211-TGeant4_digCPP.root"
                )
            ),
        },
        "No-Birks MC": {
            "tree": "cbmsim",
            "files": sorted(
                glob(
                    "/eos/experiment/sndlhc/MonteCarlo/testbeam2023/"
                    "2mmRangeCut/300GeV_-211/*/"
                    "sndLHC.PG_-211-TGeant4_MCEB_dig.root"
                )
            ),
        },
        "Data": {
            "tree": "rawConv",
            "files": sorted(
                glob(
                    "/eos/experiment/sndlhc/convertedData/commissioning/"
                    "testbeam_June2023_H8/run_100639/sndsw_raw-*.root"
                )
            ),
        },
    },
}

CUTFLOW_NAMES = [
    "all", "US1", "US2", "US3", "US1_US2", "US1_US3", "US2_US3",
    "US1_US2_US3",
]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Compare US QDC in Birks MC, no-Birks MC, and test-beam data."
        )
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=-1,
        help=(
            "Maximum number of selected events per sample. "
            "Use -1 to scan and retain the complete sample (default)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--max-scanned-events",
        type=int,
        default=10000,
        help="Maximum input entries scanned per sample (-1: all; default: 10000).",
    )
    parser.add_argument(
        "--file-check-events",
        type=int,
        default=DEFAULT_FILE_CHECK_EVENTS,
        help="Entries checked in each Data file (-1: entire file; default: 10000).",
    )
    parser.add_argument(
        "--min-scifi-hits",
        type=int,
        default=200,
        help=(
            "Require the number of Digi_ScifiHits to be greater than this value "
            "(default: 200)."
        ),
    )
    args = parser.parse_args()

    if args.max_events == 0 or args.max_events < -1:
        parser.error("--max-events must be -1 or a positive integer")

    if args.max_scanned_events == 0 or args.max_scanned_events < -1:
        parser.error("--max-scanned-events must be -1 or a positive integer")

    if args.file_check_events == 0 or args.file_check_events < -1:
        parser.error("--file-check-events must be -1 or a positive integer")

    if args.min_scifi_hits < 0:
        parser.error("--min-scifi-hits must be zero or a positive integer")

    return args


def calculate_efficiency(count, denominator):
    return count / denominator if denominator else 0.0


def update_cutflow(cutflow, planes):
    cutflow["all"] += 1
    for plane, name in ((0, "US1"), (1, "US2"), (2, "US3")):
        if plane in planes:
            cutflow[name] += 1
    for required, name in (
        ({0, 1}, "US1_US2"), ({0, 2}, "US1_US3"),
        ({1, 2}, "US2_US3"), ({0, 1, 2}, "US1_US2_US3"),
    ):
        if required.issubset(planes):
            cutflow[name] += 1


def print_cutflow(cutflow):
    denominator = cutflow["all"]
    print("\n  US bar-4/5 cut-flow")
    print("  " + "-" * 51)
    print(f"  {'Condition':18s}{'Events':>12s}{'Fraction of all':>19s}")
    print("  " + "-" * 51)
    for name in CUTFLOW_NAMES:
        fraction = calculate_efficiency(cutflow[name], denominator)
        print(f"  {name:18s}{cutflow[name]:12d}{fraction:18.2%}")
    print("  " + "-" * 51)


def analyze_dataset(
    files, tree_name, max_events, max_scanned_events, min_scifi_hits
):
    """Extract US QDC after the SciFi and US bar-4/5 selections."""

    if not files:
        raise RuntimeError("No input files were found.")

    chain = ROOT.TChain(tree_name)

    for filename in files:
        added = chain.Add(filename)
        if added == 0:
            raise RuntimeError(f"Could not add file: {filename}")

    available_events = int(chain.GetEntries())

    print(f"  Input files: {len(files)}")
    print(f"  Available events: {available_events}")
    if max_events < 0:
        print("  Requested selected events: all")
    else:
        print(f"  Requested selected events: {max_events}")
    print(
        "  Maximum scanned events: "
        + ("all" if max_scanned_events < 0 else str(max_scanned_events))
    )
    print(f"  SciFi selection: Digi_ScifiHits > {min_scifi_hits}")

    total_us_qdc = []
    channel_qdc = defaultdict(list)

    scanned_events = 0
    scifi_selected_events = 0
    required_planes = {0, 1, 2}
    cutflow = {name: 0 for name in CUTFLOW_NAMES}

    for event_index in range(available_events):
        if max_scanned_events > 0 and scanned_events >= max_scanned_events:
            break
        if max_events > 0 and len(total_us_qdc) >= max_events:
            break

        chain.GetEntry(event_index)
        scanned_events += 1

        # Keep shower-like events with more than the requested number of
        # digitized SciFi hits. Apply the same condition to Data and both MCs.
        n_scifi_hits = len(chain.Digi_ScifiHits)
        if n_scifi_hits <= min_scifi_hits:
            continue

        scifi_selected_events += 1

        event_total = 0.0
        planes_with_target_hit = set()
        event_channel_qdc = defaultdict(list)

        for hit in chain.Digi_MuFilterHits:
            detector_id = hit.GetDetectorID()

            system = detector_id // 10000
            plane = (detector_id % 10000) // 1000
            bar = detector_id % 1000

            if system != 2:
                continue

            signals = [
                (int(signal.first), float(signal.second))
                for signal in hit.GetAllSignals(
                    mask=True,
                    positive=True,
                    use_small_sipms=False,
                )
            ]

            # Sum positive large-SiPM signals from every US bar.
            for channel, qdc in signals:
                event_total += qdc

            # The only event selection: bar 4 or 5 has a positive signal
            # in each of US1, US2, and US3.
            if plane in required_planes and bar in (4, 5) and signals:
                planes_with_target_hit.add(plane)

                for channel, qdc in signals:
                    event_channel_qdc[(plane, bar, channel)].append(qdc)

        update_cutflow(cutflow, planes_with_target_hit)

        if not required_planes.issubset(planes_with_target_hit):
            continue

        total_us_qdc.append(event_total)

        # Store bar-4/5 channel values only after the event passes selection.
        for key, values in event_channel_qdc.items():
            channel_qdc[key].extend(values)

    selected_events = len(total_us_qdc)
    selection_efficiency = (
        selected_events / scanned_events if scanned_events else 0.0
    )

    print(f"  Scanned events: {scanned_events}")
    print(f"  Events passing SciFi cut: {scifi_selected_events}")
    print(f"  Selected events: {selected_events}")
    print(f"  Selection efficiency: {selection_efficiency:.4%}")
    print_cutflow(cutflow)

    if max_events > 0 and selected_events < max_events:
        print("  WARNING: Fewer selected events than requested.")

    return {
        "available_events": available_events,
        "events": selected_events,
        "scanned_events": scanned_events,
        "scifi_selected_events": scifi_selected_events,
        "selection_efficiency": selection_efficiency,
        "total_us_qdc": np.asarray(total_us_qdc, dtype=float),
        "channel_qdc": channel_qdc,
        "cutflow": cutflow,
    }


def analyze_data_file_by_file(files, tree_name, max_entries, energy):
    """Measure the bar-4/5 acceptance separately in every Data ROOT file."""
    required_planes = {0, 1, 2}
    results = []

    print("\n  File-by-file Data check")
    print("  " + "-" * 94)
    print(
        f"  {'File':35s}{'Checked':>10s}{'US1':>10s}{'US2':>10s}"
        f"{'US3':>10s}{'All 3':>10s}"
    )
    print("  " + "-" * 94)

    for filename in files:
        root_file = ROOT.TFile.Open(filename)
        if not root_file or root_file.IsZombie():
            print(f"  WARNING: Could not open {filename}")
            continue

        tree = root_file.Get(tree_name)
        if not tree:
            print(f"  WARNING: Tree {tree_name} not found in {filename}")
            root_file.Close()
            continue

        available = int(tree.GetEntries())
        checked = available if max_entries < 0 else min(available, max_entries)
        counts = {name: 0 for name in CUTFLOW_NAMES}

        for event_index in range(checked):
            tree.GetEntry(event_index)
            planes = set()

            for hit in tree.Digi_MuFilterHits:
                detector_id = hit.GetDetectorID()
                system = detector_id // 10000
                plane = (detector_id % 10000) // 1000
                bar = detector_id % 1000

                if system != 2 or plane not in required_planes or bar not in (4, 5):
                    continue

                signals = hit.GetAllSignals(
                    mask=True, positive=True, use_small_sipms=False
                )
                if signals:
                    planes.add(plane)

            update_cutflow(counts, planes)

        def percent(name):
            return 100.0 * calculate_efficiency(counts[name], counts["all"])

        short_name = Path(filename).name
        print(
            f"  {short_name:35.35s}{checked:10d}{percent('US1'):9.2f}%"
            f"{percent('US2'):9.2f}%{percent('US3'):9.2f}%"
            f"{percent('US1_US2_US3'):9.2f}%"
        )
        results.append({"energy": energy, "filename": filename, **counts})
        root_file.Close()

    print("  " + "-" * 94)
    return results


def write_file_check_summary(file_results, output_dir):
    output_file = output_dir / "data_file_by_file_cutflow.csv"
    with output_file.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            ["energy", "filename", *CUTFLOW_NAMES,
             "US1_fraction", "US2_fraction", "US3_fraction",
             "US1_US2_US3_fraction"]
        )
        for result in file_results:
            denominator = result["all"]
            writer.writerow(
                [result["energy"], result["filename"]]
                + [result[name] for name in CUTFLOW_NAMES]
                + [calculate_efficiency(result[name], denominator) for name in
                   ("US1", "US2", "US3", "US1_US2_US3")]
            )


def plot_total_us_qdc(energy, results, output_dir):
    """Compare event-by-event total US QDC."""

    nonempty = [
        result["total_us_qdc"]
        for result in results.values()
        if len(result["total_us_qdc"]) > 0
    ]
    if not nonempty:
        print(f"  WARNING: No selected events for {energy}; skipping total-QDC plot.")
        return

    all_values = np.concatenate(nonempty)
    upper_limit = float(np.percentile(all_values, 99.5))
    if upper_limit <= 0:
        upper_limit = 1.0

    bins = np.linspace(0.0, upper_limit, 41)
    fig, ax = plt.subplots(figsize=(8, 6))

    for label, result in results.items():
        values = result["total_us_qdc"]
        if len(values) == 0:
            continue
        ax.hist(
            values,
            bins=bins,
            density=True,
            histtype="step",
            linewidth=2,
            color=COLORS[label],
            label=f"{label} ({len(values)} events)",
        )

    ax.set_xlabel("Total US QDC per event")
    ax.set_ylabel("Normalized events")
    ax.set_title(f"{energy}: total Upstream MuFilter response")
    ax.legend()
    ax.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(output_dir / f"total_us_qdc_{energy}.png", dpi=160)
    plt.close(fig)


def mean_and_error(values):
    """Return mean and standard error."""

    if not values:
        return math.nan, math.nan

    array = np.asarray(values, dtype=float)
    mean = float(np.mean(array))
    if len(array) == 1:
        return mean, 0.0

    error = float(np.std(array, ddof=1) / np.sqrt(len(array)))
    return mean, error


def plot_channel_response(energy, results, output_dir):
    """Compare channel response in bars 4 and 5 of US1, US2 and US3."""

    fig, axes = plt.subplots(3, 2, figsize=(13, 11), sharex=True)

    for plane in (0, 1, 2):
        for bar_column, bar in enumerate((4, 5)):
            ax = axes[plane, bar_column]

            for label, result in results.items():
                means = []
                errors = []

                for channel in CHANNELS:
                    values = result["channel_qdc"].get(
                        (plane, bar, channel), []
                    )
                    mean, error = mean_and_error(values)
                    means.append(mean)
                    errors.append(error)

                ax.errorbar(
                    CHANNELS,
                    means,
                    yerr=errors,
                    marker="o",
                    markersize=4,
                    linewidth=1.5,
                    capsize=2,
                    color=COLORS[label],
                    label=label,
                )

            ax.set_title(f"US{plane + 1}, bar {bar}")
            ax.set_ylabel("Mean positive QDC")
            ax.grid(alpha=0.25)

    for ax in axes[-1, :]:
        ax.set_xlabel("SiPM channel")

    axes[0, 0].legend()
    fig.suptitle(
        f"{energy}: channel response in US bars 4 and 5",
        fontsize=14,
    )
    fig.tight_layout()
    fig.savefig(output_dir / f"channel_response_{energy}.png", dpi=160)
    plt.close(fig)


def safe_statistics(values):
    """Return summary statistics without warnings for empty/singleton samples."""

    if len(values) == 0:
        return math.nan, math.nan, math.nan

    mean = float(np.mean(values))
    median = float(np.median(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return mean, median, std


def write_summary(all_results, output_dir):
    """Save event counts, efficiencies, and QDC summaries to CSV."""

    output_file = output_dir / "total_us_qdc_summary.csv"

    with output_file.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "energy",
                "sample",
                "available_events",
                "scanned_events",
                "scifi_selected_events",
                "selected_events",
                "selection_efficiency",
                "mean_total_us_qdc",
                "median_total_us_qdc",
                "std_total_us_qdc",
                *[f"cutflow_{name}" for name in CUTFLOW_NAMES],
            ]
        )

        for energy, results in all_results.items():
            for label, result in results.items():
                values = result["total_us_qdc"]
                mean, median, std = safe_statistics(values)
                writer.writerow(
                    [
                        energy,
                        label,
                        result["available_events"],
                        result["scanned_events"],
                        result["scifi_selected_events"],
                        result["events"],
                        result["selection_efficiency"],
                        mean,
                        median,
                        std,
                        *[result["cutflow"][name] for name in CUTFLOW_NAMES],
                    ]
                )


def main():
    args = parse_arguments()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ROOT.gROOT.SetBatch(True)

    all_results = {}
    all_file_results = []

    for energy, datasets in DATASETS.items():
        print(f"\n=== Analyzing {energy} ===")
        energy_results = {}

        for label, configuration in datasets.items():
            print(f"\n{label}")
            if label == "Data":
                all_file_results.extend(
                    analyze_data_file_by_file(
                        files=configuration["files"],
                        tree_name=configuration["tree"],
                        max_entries=args.file_check_events,
                        energy=energy,
                    )
                )
            energy_results[label] = analyze_dataset(
                files=configuration["files"],
                tree_name=configuration["tree"],
                max_events=args.max_events,
                max_scanned_events=args.max_scanned_events,
                min_scifi_hits=args.min_scifi_hits,
            )

        all_results[energy] = energy_results
        plot_total_us_qdc(energy, energy_results, args.output_dir)
        plot_channel_response(energy, energy_results, args.output_dir)

    write_summary(all_results, args.output_dir)
    write_file_check_summary(all_file_results, args.output_dir)

    print("\nAnalysis completed.")
    print(f"Results saved in: {args.output_dir}")


if __name__ == "__main__":
    main()

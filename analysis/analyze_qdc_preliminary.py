#!/usr/bin/env python3

from collections import defaultdict
from glob import glob
from pathlib import Path
import csv
import math

import ROOT

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


MAX_EVENTS = 100

OUTPUT_DIR = Path(
    "/afs/cern.ch/work/y/ykim/project_birkslaw/analysis/results"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
            "files": [
                "/eos/user/y/ykim/project_birkslaw/birks_samples/"
                "piPlus_100GeV/sndLHC.PG_211-TGeant4_digCPP.root"
            ],
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
            "files": [
                "/eos/user/y/ykim/project_birkslaw/birks_samples/"
                "piMinus_300GeV/sndLHC.PG_-211-TGeant4_digCPP.root"
            ],
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


def analyze_dataset(files, tree_name, max_events):
    """Extract total US QDC and channel QDC values."""

    if not files:
        raise RuntimeError("No input files were found.")

    chain = ROOT.TChain(tree_name)

    for filename in files:
        added = chain.Add(filename)
        if added == 0:
            raise RuntimeError(f"Could not add file: {filename}")

    available_events = chain.GetEntries()
    events_to_process = min(max_events, available_events)

    print(f"  Input files: {len(files)}")
    print(f"  Available events: {available_events}")
    print(f"  Processing events: {events_to_process}")

    total_us_qdc = []
    channel_qdc = defaultdict(list)

    for event_index in range(events_to_process):
        chain.GetEntry(event_index)

        event_total = 0.0

        for hit in chain.Digi_MuFilterHits:
            detector_id = hit.GetDetectorID()

            system = detector_id // 10000
            plane = (detector_id % 10000) // 1000
            bar = detector_id % 1000

            # Use only Upstream MuFilter hits.
            if system != 2:
                continue

            signals = hit.GetAllSignals(
                mask=True,
                positive=True,
                use_small_sipms=False,
            )

            for signal in signals:
                channel = int(signal.first)
                qdc = float(signal.second)

                event_total += qdc

                if plane in (0, 1, 2) and bar in (4, 5):
                    channel_qdc[(plane, bar, channel)].append(qdc)

        total_us_qdc.append(event_total)

    return {
        "events": events_to_process,
        "total_us_qdc": np.asarray(total_us_qdc, dtype=float),
        "channel_qdc": channel_qdc,
    }


def plot_total_us_qdc(energy, results):
    """Compare event-by-event total US QDC."""

    all_values = np.concatenate(
        [
            result["total_us_qdc"]
            for result in results.values()
            if len(result["total_us_qdc"]) > 0
        ]
    )

    upper_limit = np.percentile(all_values, 99.5)

    if upper_limit <= 0:
        upper_limit = 1.0

    bins = np.linspace(0.0, upper_limit, 41)

    fig, ax = plt.subplots(figsize=(8, 6))

    for label, result in results.items():
        values = result["total_us_qdc"]

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
    fig.savefig(
        OUTPUT_DIR / f"total_us_qdc_{energy}.png",
        dpi=160,
    )
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


def plot_channel_response(energy, results):
    """Compare channel response in bars 4 and 5 of US1, US2 and US3."""

    fig, axes = plt.subplots(
        3,
        2,
        figsize=(13, 11),
        sharex=True,
    )

    for plane in (0, 1, 2):
        for bar_column, bar in enumerate((4, 5)):
            ax = axes[plane, bar_column]

            for label, result in results.items():
                means = []
                errors = []

                for channel in CHANNELS:
                    values = result["channel_qdc"].get(
                        (plane, bar, channel),
                        [],
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
    fig.savefig(
        OUTPUT_DIR / f"channel_response_{energy}.png",
        dpi=160,
    )
    plt.close(fig)


def write_summary(all_results):
    """Save numerical summaries to a CSV file."""

    output_file = OUTPUT_DIR / "total_us_qdc_summary.csv"

    with output_file.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "energy",
                "sample",
                "events",
                "mean_total_us_qdc",
                "median_total_us_qdc",
                "std_total_us_qdc",
            ]
        )

        for energy, results in all_results.items():
            for label, result in results.items():
                values = result["total_us_qdc"]

                writer.writerow(
                    [
                        energy,
                        label,
                        len(values),
                        float(np.mean(values)),
                        float(np.median(values)),
                        float(np.std(values, ddof=1)),
                    ]
                )


def main():
    all_results = {}

    for energy, datasets in DATASETS.items():
        print(f"\n=== Analyzing {energy} ===")
        energy_results = {}

        for label, configuration in datasets.items():
            print(f"\n{label}")

            energy_results[label] = analyze_dataset(
                files=configuration["files"],
                tree_name=configuration["tree"],
                max_events=MAX_EVENTS,
            )

        all_results[energy] = energy_results

        plot_total_us_qdc(energy, energy_results)
        plot_channel_response(energy, energy_results)

    write_summary(all_results)

    print("\nAnalysis completed.")
    print(f"Results saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
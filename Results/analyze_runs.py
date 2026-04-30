import argparse
import math
import os
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


TARGET_COLUMNS = [
    "FrameTime",
    "GPUTime",
    "RenderThreadTime",
    "RHI/DrawCalls",
    "Exclusive/AllWorkers/RenderBasePass",
    "Exclusive/AllWorkers/RenderShadows",
]

COLUMN_ORDER = [
    "FrameTime",
    "FPS",
    "GPUTime",
    "RenderThreadTime",
    "RHI/DrawCalls",
    "Exclusive/AllWorkers/RenderBasePass",
    "Exclusive/AllWorkers/RenderShadows",
]

PLOT_COLUMNS = [
    ("FrameTime", "Milliseconds", "FrameTime.png"),
    ("FPS", "Frames Per Second", "FPS.png"),
    ("GPUTime", "Milliseconds", "GPU_Time.png"),
    ("RenderThreadTime", "Milliseconds", "RenderThreadTime.png"),
    ("RHI/DrawCalls", "Draw Calls", "DrawCalls.png"),
    ("Exclusive/AllWorkers/RenderBasePass", "Milliseconds", "BasePass.png"),
    ("Exclusive/AllWorkers/RenderShadows", "Milliseconds", "RenderShadows.png"),
]


# Reads CSV using pandas and filters for columns of interest
def load_and_filter_csv(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path, low_memory=False)

    targeted_cols = [col for col in TARGET_COLUMNS if col in df.columns]
    filtered = df[targeted_cols].copy()

    for col in targeted_cols:
        filtered[col] = pd.to_numeric(filtered[col], errors="coerce")

    # Calculate FPS from frame time; uses formula mentioned here:
    # https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-profiling-fundamentals.html
    if "FrameTime" in filtered.columns:
        filtered["FPS"] = 1000.0 / filtered["FrameTime"]

    ordered = [col for col in COLUMN_ORDER if col in filtered.columns]
    return filtered[ordered]


# Gets stats for a single series
def summarize_series(series: pd.Series) -> dict:
    numericized = pd.to_numeric(series, errors="coerce").dropna()

    return {
        "Mean": numericized.mean(),
        "Median": numericized.median(),
        "Min": numericized.min(),
        "Max": numericized.max(),
        "StdDev": numericized.std(),
        "P95": numericized.quantile(0.95),
        "P99": numericized.quantile(0.99),
    }


# Creates a dataframe holding stats
def create_summary_dataframe(df: pd.DataFrame, run_name: str | None = None) -> pd.DataFrame:
    rows = []

    for col in df.columns:
        stats = summarize_series(df[col])

        row = {"Metric": col, **stats}
        if run_name is not None:
            row["Run"] = run_name
        rows.append(row)

    summary_df = pd.DataFrame(rows)

    if run_name is not None and not summary_df.empty:
        summary_df = summary_df[["Run", "Metric", "Mean", "Median", "Min", "Max", "StdDev", "P95", "P99"]]
    elif not summary_df.empty:
        summary_df = summary_df[["Metric", "Mean", "Median", "Min", "Max", "StdDev", "P95", "P99"]]

    return summary_df


# Get means for each run
def compute_run_means(df: pd.DataFrame, run_name: str) -> dict:
    result = {"Run": run_name}

    for col in df.columns:
        numericized = pd.to_numeric(df[col], errors="coerce").dropna()
        result[col] = numericized.mean() if not numericized.empty else pd.NA

    return result


# Generic dataframe -> CSV save function
def save_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


# Preps aggregate summary frame for save
def create_aggregate_summary(run_means_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    metric_columns = [col for col in run_means_df.columns if col != "Run"]
    for col in metric_columns:
        numericized = pd.to_numeric(run_means_df[col], errors="coerce").dropna()

        z = 1.96
        n = len(numericized)
        mean = numericized.mean()
        std_dev = numericized.std()
        moe = z * (std_dev / math.sqrt(n)) if n > 0 else pd.NA

        rows.append(
            {
                "Metric": col,
                "RunCount": n,
                "MeanOfRuns": mean,
                "MedianOfRuns": numericized.median(),
                "MinRunMean": numericized.min(),
                "MaxRunMean": numericized.max(),
                "StdDev": std_dev,
                "MarginOfError95": moe,
                "LowerBound95": mean - moe if n > 0 else pd.NA,
                "UpperBound95": mean + moe if n > 0 else pd.NA,
            }
        )

    return pd.DataFrame(rows)


# Generates a plot for the given metric; does plots for a single configuration only
def plot_data(run_means_df: pd.DataFrame, metric: str, ylabel: str, output_path: Path) -> None:
    plot_df = run_means_df[["Run", metric]].copy()
    plot_df[metric] = pd.to_numeric(plot_df[metric], errors="coerce")
    plot_df = plot_df.dropna(subset=[metric])

    plt.figure(figsize=(10, 5))
    plt.plot(plot_df["Run"], plot_df[metric], marker="o")
    plt.xlabel("Run")
    plt.ylabel(ylabel)
    plt.title(metric)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


# Defines dir paths for saves and calls relevant processing functions
def process_cleaned_directory(cleaned_dir: Path) -> None:
    cleaned_dir = cleaned_dir.resolve()

    csv_files = sorted(cleaned_dir.glob("*.csv"), key=os.path.getctime)
    if not csv_files:
        print(f"No CSVs found in {cleaned_dir}")
        return

    parent_dir = cleaned_dir.parent
    filtered_dir = parent_dir / "Filtered"
    summaries_dir = parent_dir / "Summaries"
    plots_dir = parent_dir / "Plots"
    filtered_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    run_means = []

    for file in csv_files:
        run_name = file.stem
        print(f"Processing {file}")

        filtered_df = load_and_filter_csv(file)
        filtered_output_path = filtered_dir / f"{run_name}_Filtered.csv"
        save_csv(filtered_df, filtered_output_path)

        run_summary_df = create_summary_dataframe(filtered_df, run_name=run_name)
        run_summary_path = summaries_dir / f"{run_name}_Summary.csv"
        save_csv(run_summary_df, run_summary_path)

        run_means.append(compute_run_means(filtered_df, run_name))

    run_means_df = pd.DataFrame(run_means)

    run_means_path = summaries_dir / "AggregatedRunMeans.csv"
    save_csv(run_means_df, run_means_path)

    aggregate_summary_path = summaries_dir / "AggregateSummary.csv"
    aggregate_df = create_aggregate_summary(run_means_df)
    save_csv(aggregate_df, aggregate_summary_path)

    for metric, ylabel, filename in PLOT_COLUMNS:
        plot_data(
            run_means_df=run_means_df,
            metric=metric,
            ylabel=ylabel,
            output_path=plots_dir / filename,
        )

    print(f"Complete: {cleaned_dir}")


def process_parent_directory(parent_dir: Path) -> None:
    parent_dir = parent_dir.resolve()

    if not parent_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {parent_dir}")

    subdirectories = sorted([path for path in parent_dir.iterdir() if path.is_dir()])
    if not subdirectories:
        print(f"No subdirectories found in {parent_dir}")
        return

    processed_count = 0
    for subdirectory in subdirectories:
        cleaned_dir = subdirectory / "Cleaned"
        if not cleaned_dir.is_dir():
            print(f"Skipping {subdirectory}: no Cleaned directory found")
            continue

        process_cleaned_directory(cleaned_dir)
        processed_count += 1

    if processed_count == 0:
        print(f"No subdirectories with a Cleaned directory were found in {parent_dir}")
    else:
        print(f"Finished processing {processed_count} subdirectories")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target_dir",
        type=str,
        help="Path to the parent directory containing subdirectories with Cleaned CSV folders",
    )
    args = parser.parse_args()

    process_parent_directory(Path(args.target_dir))


if __name__ == "__main__":
    main()

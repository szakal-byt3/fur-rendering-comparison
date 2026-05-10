import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


METRICS = [
    ("FrameTime", "Frame Time (ms)", "FrameTime_Scaling.png"),
    ("FPS", "Frames per Second", "FPS_Scaling.png"),
    ("GPUTime", "GPU Time (ms)", "GPUTime_Scaling.png"),
    ("RenderThreadTime", "Render Thread Time (ms)", "RenderThreadTime_Scaling.png"),
    ("RHI/DrawCalls", "Draw Calls", "DrawCalls_Scaling.png"),
    ("Exclusive/AllWorkers/RenderBasePass", "Base Pass (ms)", "BasePass_Scaling.png"),
    ("Exclusive/AllWorkers/RenderShadows", "Render Shadows (ms)", "Shadows_Scaling.png"),
]


# Expects files to be named like 8_Shells.csv or 16k_Strands.csv
def parse_config_name(file_name: str) -> tuple[str, int]:
    file_name_split = file_name.split('_')

    complexity = file_name_split[0]
    method = file_name_split[1]

    if "Shell" in method:
        method = "Shell"
    elif "Strand" in method:
        method = "Strand"
        complexity = complexity.rstrip('k')
    else:
        print("WARNING: Method unknown")
    return method, int(complexity)


def load_aggregate_summaries(target_dir: Path) -> pd.DataFrame:
    rows = []

    csv_files = sorted(target_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSVs found in {target_dir}")
        return

    for file in csv_files:
        method, complexity = parse_config_name(file.name)
        summary_df = pd.read_csv(file, low_memory=False)

        for index, row in summary_df.iterrows():
            rows.append({
                "Method": method,
                "Complexity": complexity,
                "Metric": row["Metric"],
                "MeanOfRuns": pd.to_numeric(row["MeanOfRuns"], errors="coerce"),
                "MarginOfError95": pd.to_numeric(row["MarginOfError95"], errors="coerce"),
                "StdDev": pd.to_numeric(row["StdDev"], errors="coerce"),
                "RunCount": pd.to_numeric(row["RunCount"], errors="coerce"),
            })

    return pd.DataFrame(rows)


def save_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def plot_data(df: pd.DataFrame, metric: str, ylabel: str, output_path: Path) -> None:
    metric_df = df[df["Metric"] == metric].copy()
    metric_df = metric_df.sort_values("Complexity")

    plt.figure(figsize=(8, 5))

    # Get the method (should be the same for every row)
    methods = metric_df["Method"].dropna().unique()
    method = methods[0]

    x = metric_df["Complexity"]
    y = metric_df["MeanOfRuns"]
    yerr = metric_df["MarginOfError95"]

    plt.errorbar(x, y, yerr=yerr, marker="o", capsize=5)

    # Label based on method
    xlabel = "Complexity"
    title_mod = "Complexity"

    if method == "Strand":
        xlabel = "Number of Curves (thousands)"
        title_mod = "Curve Count"
    elif method == "Shell":
        xlabel = "Number of Shells"
        title_mod = "Shell Count"

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} vs {title_mod}")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target_dir",
        type=str,
        help="Parent directory containing subdirectories with AggregateSummaries folders",
    )
    args = parser.parse_args()

    parent_dir = Path(args.target_dir).resolve()

    for subdir in sorted(parent_dir.iterdir()):
        if not subdir.is_dir():
            continue

        aggregate_dir = subdir / "AggregateSummaries"
        if not aggregate_dir.is_dir():
            print(f"Skipping {subdir.name}: no AggregateSummaries directory found")
            continue

        print(f"Processing {aggregate_dir}")

        output_dir = subdir / "Combined"
        plots_dir = output_dir / "Plots"
        output_dir.mkdir(parents=True, exist_ok=True)
        plots_dir.mkdir(parents=True, exist_ok=True)

        combined_df = load_aggregate_summaries(aggregate_dir)

        save_csv(combined_df, output_dir / "CombinedSummary.csv")

        for metric, ylabel, filename in METRICS:
            plot_data(combined_df, metric, ylabel, plots_dir / filename)

    print("\nComplete")


if __name__ == "__main__":
    main()
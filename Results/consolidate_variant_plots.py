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


VARIANT_MAP = {
    "Shell": ("Shell", "Shell"),
    "Shell_ISM": ("Shell", "Shell (ISM)"),
    "Shell_ISM_Raytraced": ("Shell", "Shell (ISM) with RT"),
    "Strand": ("Strand", "Strand"),
    "Strand_Raytraced": ("Strand", "Strand with RT"),
}


RESOLUTIONS = [
    "1280x720",
    "1600x900",
    "1920x1080",
    "2560x1440",
]


# Reads the intermediary CombinedSummary.csv files created by analyze_agg_summaries.py.
def load_combined_summaries(parent_dir: Path) -> pd.DataFrame:
    rows = []

    for subdir in sorted(parent_dir.iterdir()):
        if not subdir.is_dir():
            continue

        if subdir.name not in VARIANT_MAP:
            print(f"Skipping {subdir.name}: not a known variant directory")
            continue

        method_group, variant_name = VARIANT_MAP[subdir.name]
        combined_summary = subdir / "Combined" / "CombinedSummary.csv"

        if not combined_summary.is_file():
            print(f"Skipping {subdir.name}: no Combined/CombinedSummary.csv found")
            continue

        print(f"Loading {combined_summary}")
        summary_df = pd.read_csv(combined_summary, low_memory=False)

        for index, row in summary_df.iterrows():
            rows.append({
                "Method": method_group,
                "Variant": variant_name,
                "Complexity": row["Complexity"],
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


def get_axis_labels(method: str, x_override: str | None = None) -> tuple[str, str]:
    xlabel = "Complexity"
    title_mod = "Complexity"

    if x_override == "Resolution":
        xlabel = "Resolution"
        title_mod = "Resolution"
    elif x_override is not None:
        xlabel = f"Number of {x_override}"
        title_mod = f"{x_override} Count"
    elif method == "Strand":
        xlabel = "Number of Curves (thousands)"
        title_mod = "Curve Count"
    elif method == "Shell":
        xlabel = "Number of Shells"
        title_mod = "Shell Count"

    return xlabel, title_mod


def plot_data(df: pd.DataFrame, method: str, metric: str, ylabel: str, output_path: Path, x_override: str | None = None) -> None:
    metric_df = df[(df["Method"] == method) & (df["Metric"] == metric)].copy()

    if x_override == "Resolution":
        metric_df["Complexity"] = metric_df["Complexity"].astype(str)
        metric_df["XPosition"] = metric_df["Complexity"].apply(lambda value: RESOLUTIONS.index(value))
        metric_df = metric_df.sort_values(["Variant", "XPosition"])
    else:
        metric_df["Complexity"] = pd.to_numeric(metric_df["Complexity"], errors="coerce")
        metric_df = metric_df.sort_values(["Variant", "Complexity"])

    if metric_df.empty:
        print(f"Skipping {method} {metric}: no matching rows")
        return

    plt.figure(figsize=(8, 5))

    for variant_name, variant_df in metric_df.groupby("Variant"):
        if x_override == "Resolution":
            variant_df = variant_df.sort_values("XPosition")
        else:
            variant_df = variant_df.sort_values("Complexity")

        # Don't include RT results for AllWorkers/RenderShadows
        if "RenderShadows" in metric and "RT" in variant_name:
            continue

        if x_override == "Resolution":
            x = variant_df["XPosition"]
        else:
            x = variant_df["Complexity"]
        y = variant_df["MeanOfRuns"]
        yerr = variant_df["MarginOfError95"]

        plt.errorbar(x, y, yerr=yerr, marker="o", capsize=5, label=variant_name)

    xlabel, title_mod = get_axis_labels(method, x_override)

    if x_override == "Resolution":
        plt.xticks(range(len(RESOLUTIONS)), RESOLUTIONS, rotation=30, ha="right")

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f"Mean {ylabel} vs {title_mod}")
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_data_shared_x(df: pd.DataFrame, metric: str, ylabel: str, output_path: Path, x_override: str | None = None) -> None:
    metric_df = df[df["Metric"] == metric].copy()

    if x_override == "Resolution":
        metric_df["Complexity"] = metric_df["Complexity"].astype(str)
        metric_df["XPosition"] = metric_df["Complexity"].apply(lambda value: RESOLUTIONS.index(value))
        metric_df = metric_df.sort_values(["Method", "Variant", "XPosition"])
    else:
        metric_df["Complexity"] = pd.to_numeric(metric_df["Complexity"], errors="coerce")
        metric_df = metric_df.sort_values(["Method", "Variant", "Complexity"])

    if metric_df.empty:
        print(f"Skipping shared {metric}: no matching rows")
        return

    plt.figure(figsize=(8, 5))

    for variant_name, variant_df in metric_df.groupby("Variant"):
        if x_override == "Resolution":
            variant_df = variant_df.sort_values("XPosition")
        else:
            variant_df = variant_df.sort_values("Complexity")

        # Don't include RT results for AllWorkers/RenderShadows
        if "RenderShadows" in metric and "RT" in variant_name:
            continue

        if x_override == "Resolution":
            x = variant_df["XPosition"]
        else:
            x = variant_df["Complexity"]
        y = variant_df["MeanOfRuns"]
        yerr = variant_df["MarginOfError95"]

        plt.errorbar(x, y, yerr=yerr, marker="o", capsize=5, label=variant_name)

    if x_override == "Resolution":
        xlabel = "Resolution"
        title_mod = "Resolution"
    elif x_override is not None:
        xlabel = f"Number of {x_override}"
        title_mod = f"{x_override} Count"
    else:
        xlabel = "Shared Complexity"
        title_mod = "Shared Complexity"

    if x_override == "Resolution":
        plt.xticks(range(len(RESOLUTIONS)), RESOLUTIONS, rotation=30, ha="right")

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f"Mean {ylabel} vs {title_mod}")
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target_dir",
        type=str,
        help="Parent directory containing Shell and Strand results",
    )
    parser.add_argument(
        "--x-override",
        type=str,
        default=None,
        help="Optional x-axis label override",
    )
    parser.add_argument(
        "--shared-x-axis",
        action="store_true",
        help="Plot shell and strand methods on same graph; needs to be used with x-override",
    )
    args = parser.parse_args()

    parent_dir = Path(args.target_dir).resolve()
    output_dir = parent_dir / "Consolidated"

    combined_df = load_combined_summaries(parent_dir)
    if combined_df.empty:
        print("No CombinedSummary.csv data found")
        return

    save_csv(combined_df, output_dir / "ConsolidatedSummary.csv")

    if args.shared_x_axis:
        shared_output_dir = output_dir / "SharedXAxis"
        plots_dir = shared_output_dir / "Plots"
        plots_dir.mkdir(parents=True, exist_ok=True)

        save_csv(combined_df, shared_output_dir / "ConsolidatedSummary.csv")

        for metric, ylabel, filename in METRICS:
            plot_data_shared_x(combined_df, metric, ylabel, plots_dir / filename, args.x_override)
    
    else:
        for method in ["Shell", "Strand"]:
            method_df = combined_df[combined_df["Method"] == method]
            if method_df.empty:
                continue

            method_output_dir = output_dir / method
            plots_dir = method_output_dir / "Plots"
            plots_dir.mkdir(parents=True, exist_ok=True)

            save_csv(method_df, method_output_dir / "ConsolidatedSummary.csv")

            for metric, ylabel, filename in METRICS:
                plot_data(method_df, method, metric, ylabel, plots_dir / filename, args.x_override)

    print("\nComplete")


if __name__ == "__main__":
    main()

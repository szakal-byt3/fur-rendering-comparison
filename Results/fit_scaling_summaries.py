import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


METRICS = [
    ("FrameTime", "Frame Time (ms)", "FrameTime_Fit.png"),
    ("GPUTime", "GPU Time (ms)", "GPUTime_Fit.png"),
]


VARIANT_MAP = {
    "Shell": ("Shell", "Shell"),
    "Shell_ISM": ("Shell", "Shell (ISM)"),
    "Shell_ISM_Raytraced": ("Shell", "Shell (ISM) with RT"),
    "Strand": ("Strand", "Strand"),
    "Strand_Raytraced": ("Strand", "Strand with RT"),
}


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
                "Complexity": pd.to_numeric(row["Complexity"], errors="coerce"),
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

    if x_override is not None:
        xlabel = f"Number of {x_override}"
        title_mod = f"{x_override} Count"
    elif method == "Strand":
        xlabel = "Number of Curves (thousands)"
        title_mod = "Curve Count"
    elif method == "Shell":
        xlabel = "Number of Shells"
        title_mod = "Shell Count"

    return xlabel, title_mod


def fit_line(variant_df: pd.DataFrame) -> tuple[float, float, float]:
    x = variant_df["Complexity"].to_numpy()
    y = variant_df["MeanOfRuns"].to_numpy()

    slope, intercept = np.polyfit(x, y, 1)
    y_predicted = slope * x + intercept

    residual_sum_squares = np.sum((y - y_predicted) ** 2)
    total_sum_squares = np.sum((y - np.mean(y)) ** 2)

    if total_sum_squares == 0:
        r_squared = 1.0
    else:
        r_squared = 1 - (residual_sum_squares / total_sum_squares)

    return slope, intercept, r_squared


def plot_fit_data(df: pd.DataFrame, method: str, metric: str, ylabel: str, output_path: Path, x_override: str | None = None) -> list[dict]:
    metric_df = df[(df["Method"] == method) & (df["Metric"] == metric)].copy()
    metric_df = metric_df.dropna(subset=["Complexity", "MeanOfRuns"])
    metric_df = metric_df.sort_values(["Variant", "Complexity"])

    if metric_df.empty:
        print(f"Skipping {method} {metric}: no matching rows")
        return []

    fit_rows = []
    plt.figure(figsize=(8, 5))

    for variant_name, variant_df in metric_df.groupby("Variant"):
        variant_df = variant_df.sort_values("Complexity")

        if len(variant_df) < 2:
            print(f"Skipping {method} {variant_name} {metric}: fewer than two points")
            continue

        slope, intercept, r_squared = fit_line(variant_df)

        x = variant_df["Complexity"]
        y = variant_df["MeanOfRuns"]
        yerr = variant_df["MarginOfError95"]

        fit_x = np.linspace(x.min(), x.max(), 100)
        fit_y = slope * fit_x + intercept

        label = f"{variant_name} (R^2={r_squared:.3f})"
        points = plt.errorbar(x, y, yerr=yerr, marker="o", capsize=5, linestyle="none", alpha=0.55)
        color = points[0].get_color()
        plt.plot(fit_x, fit_y, label=label, color=color)

        fit_rows.append({
            "Method": method,
            "Variant": variant_name,
            "Metric": metric,
            "Slope": slope,
            "Intercept": intercept,
            "RSquared": r_squared,
            "PointCount": len(variant_df),
            "MinComplexity": x.min(),
            "MaxComplexity": x.max(),
        })

    xlabel, title_mod = get_axis_labels(method, x_override)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f"Linear Fit of Mean {ylabel} vs {title_mod}")
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return fit_rows


def plot_fit_data_shared_x(df: pd.DataFrame, metric: str, ylabel: str, output_path: Path, x_override: str | None = None) -> list[dict]:
    metric_df = df[df["Metric"] == metric].copy()
    metric_df = metric_df.dropna(subset=["Complexity", "MeanOfRuns"])
    metric_df = metric_df.sort_values(["Method", "Variant", "Complexity"])

    if metric_df.empty:
        print(f"Skipping shared {metric}: no matching rows")
        return []

    fit_rows = []
    plt.figure(figsize=(8, 5))

    for variant_name, variant_df in metric_df.groupby("Variant"):
        variant_df = variant_df.sort_values("Complexity")

        if len(variant_df) < 2:
            print(f"Skipping shared {variant_name} {metric}: fewer than two points")
            continue

        method = variant_df["Method"].iloc[0]
        slope, intercept, r_squared = fit_line(variant_df)

        x = variant_df["Complexity"]
        y = variant_df["MeanOfRuns"]
        yerr = variant_df["MarginOfError95"]

        fit_x = np.linspace(x.min(), x.max(), 100)
        fit_y = slope * fit_x + intercept

        label = f"{variant_name} fit (R^2={r_squared:.3f})"
        points = plt.errorbar(x, y, yerr=yerr, marker="o", capsize=5, linestyle="none", alpha=0.55)
        color = points[0].get_color()
        plt.plot(fit_x, fit_y, label=label, color=color)

        fit_rows.append({
            "Method": method,
            "Variant": variant_name,
            "Metric": metric,
            "Slope": slope,
            "Intercept": intercept,
            "RSquared": r_squared,
            "PointCount": len(variant_df),
            "MinComplexity": x.min(),
            "MaxComplexity": x.max(),
        })

    if x_override is not None:
        xlabel = f"Number of {x_override}"
        title_mod = f"{x_override} Count"
    else:
        xlabel = "Shared Complexity"
        title_mod = "Shared Complexity"

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f"Linear Fit of Mean {ylabel} vs {title_mod}")
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return fit_rows


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
    output_dir = parent_dir / "Consolidated" / "Fits"

    combined_df = load_combined_summaries(parent_dir)
    if combined_df.empty:
        print("No CombinedSummary.csv data found")
        return

    fit_rows = []

    if args.shared_x_axis:
        shared_output_dir = output_dir / "SharedXAxis"
        plots_dir = shared_output_dir / "Plots"
        plots_dir.mkdir(parents=True, exist_ok=True)

        for metric, ylabel, filename in METRICS:
            fit_rows.extend(plot_fit_data_shared_x(combined_df, metric, ylabel, plots_dir / filename, args.x_override))

        save_csv(pd.DataFrame(fit_rows), shared_output_dir / "FitSummary.csv")

    else:
        for method in ["Shell", "Strand"]:
            method_df = combined_df[combined_df["Method"] == method]
            if method_df.empty:
                continue

            method_output_dir = output_dir / method
            plots_dir = method_output_dir / "Plots"
            plots_dir.mkdir(parents=True, exist_ok=True)

            method_fit_rows = []
            for metric, ylabel, filename in METRICS:
                metric_fit_rows = plot_fit_data(method_df, method, metric, ylabel, plots_dir / filename, args.x_override)
                method_fit_rows.extend(metric_fit_rows)
                fit_rows.extend(metric_fit_rows)

            save_csv(pd.DataFrame(method_fit_rows), method_output_dir / "FitSummary.csv")

    save_csv(pd.DataFrame(fit_rows), output_dir / "FitSummary.csv")

    print("\nComplete")


if __name__ == "__main__":
    main()

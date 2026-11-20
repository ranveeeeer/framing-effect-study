"""
Make the charts from the tables in results/tables.

    1. headline.png         - % risky by frame: students vs each model (direct mode)
    2. by_scenario.png      - the same, split by scenario, one panel each
    3. step_by_step.png     - framing gap per model: direct vs step by step
    4. students.png         - students only, by scenario and pooled

Usage:
    python src/make_charts.py          # real data
    python src/make_charts.py --mock   # test data
    python src/make_charts.py --students-only   # before any model results exist
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import model_dirs
from items import SCENARIOS

# Colours: one for gain, one for loss, used in every chart.
# Blue/orange (not green/red) so colour-blind readers can tell them apart.
GAIN = "#2a78d6"
LOSS = "#eb6834"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.edgecolor": "#c3c2b7",
    "axes.labelcolor": INK,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "savefig.dpi": 200,
})


def ci_errors(df, frame):
    """Turn the '45-72' confidence-interval text into error-bar lengths."""
    lo_hi = df[f"ci_{frame}"].str.split("-", expand=True).astype(float)
    pct = df[f"pct_{frame}"]
    return np.vstack([pct - lo_hi[0], lo_hi[1] - pct])


def percent_axis(ax):
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def headline(students, pooled, out):
    direct = pooled[pooled["mode"] == "direct"]
    st = students[students["scenario"] == "all"].assign(model="Students")
    df = pd.concat([st, direct], ignore_index=True)

    x = np.arange(len(df))
    w = 0.38
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for offset, frame, colour, label in [(-w / 2, "gain", GAIN, "Gain frame"),
                                         (w / 2, "loss", LOSS, "Loss frame")]:
        bars = ax.bar(x + offset, df[f"pct_{frame}"], width=w - 0.04, color=colour, label=label)
        ax.errorbar(x + offset, df[f"pct_{frame}"], yerr=ci_errors(df, frame),
                    fmt="none", ecolor=INK, elinewidth=0.8, capsize=2)
        for b, v in zip(bars, df[f"pct_{frame}"]):
            ax.text(b.get_x() + b.get_width() / 2, 2, f"{v:.0f}", ha="center",
                    va="bottom", fontsize=8, color="white")

    ax.axvline(0.5, color=GRID, linewidth=1)  # separates students from models
    ax.set_xticks(x)
    ax.set_xticklabels(df["model"], rotation=20, ha="right")
    percent_axis(ax)
    ax.set_ylabel("Chose the risky option")
    ax.set_title("Same facts, different frames: who gambles more after a loss frame?")
    ax.legend(frameon=False, loc="upper right", ncol=2)
    fig.text(0.01, 0.01, "Bars: % choosing the risky option, all 5 scenarios pooled. "
             "Lines: 95% confidence intervals. Models answered directly (no step-by-step).",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out / "headline.png")
    plt.close(fig)


def by_scenario(students, per_scenario, out):
    direct = per_scenario[per_scenario["mode"] == "direct"]
    panels = [("Students", students[students["scenario"] != "all"])]
    panels += [(m, d) for m, d in direct.groupby("model", sort=False)]

    cols = 4
    rows = int(np.ceil(len(panels) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(12, 3.0 * rows), sharey=True)
    axes = np.atleast_1d(axes).ravel()
    x = np.arange(len(SCENARIOS))
    w = 0.38
    for ax, (name, df) in zip(axes, panels):
        df = df.set_index("scenario").loc[SCENARIOS].reset_index()
        ax.bar(x - w / 2, df["pct_gain"], width=w - 0.04, color=GAIN, label="Gain frame")
        ax.bar(x + w / 2, df["pct_loss"], width=w - 0.04, color=LOSS, label="Loss frame")
        ax.set_xticks(x)
        ax.set_xticklabels(SCENARIOS, fontsize=8)
        percent_axis(ax)
        ax.set_title(name, fontsize=10)
    for ax in axes[len(panels):]:
        ax.axis("off")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Framing effect by scenario (% choosing the risky option)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "by_scenario.png")
    plt.close(fig)


def step_by_step(students, gaps, out):
    gaps = gaps.sort_values("direct")
    y = np.arange(len(gaps))
    fig, ax = plt.subplots(figsize=(8, 0.6 * len(gaps) + 1.6))
    for yi, (_, r) in zip(y, gaps.iterrows()):
        ax.plot([r["direct"], r["step_by_step"]], [yi, yi], color=GRID, linewidth=2, zorder=1)
    ax.scatter(gaps["direct"], y, s=60, color=INK, zorder=2, label="Direct answer")
    ax.scatter(gaps["step_by_step"], y, s=60, facecolor=SURFACE, edgecolor=INK,
               linewidth=1.5, zorder=3, label="Step by step")

    student_gap = students.loc[students["scenario"] == "all", "gap_points"].iloc[0]
    ax.axvline(student_gap, color=MUTED, linestyle="--", linewidth=1)
    ax.text(student_gap, -0.75, f" Students: {student_gap:+.0f}", color=INK, fontsize=8, va="center")
    ax.axvline(0, color="#c3c2b7", linewidth=1)

    ax.set_ylim(-1.0, len(gaps) - 0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(gaps["model"])
    ax.set_xlabel("Framing gap: % risky (loss) minus % risky (gain), in points")
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Does thinking step by step shrink the framing effect?")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "step_by_step.png")
    plt.close(fig)


def students_chart(students, out):
    """% risky by frame for the students: each scenario, then all five pooled."""
    order = SCENARIOS + ["all"]
    df = students.set_index("scenario").loc[order].reset_index()
    labels = [s.capitalize() for s in SCENARIOS] + ["All 5\n(per student)"]

    x = np.arange(len(df)).astype(float)
    x[-1] += 0.5  # a little space before the pooled pair
    w = 0.38
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for offset, frame, colour, label in [(-w / 2, "gain", GAIN, "Gain frame (saved / keep)"),
                                         (w / 2, "loss", LOSS, "Loss frame (die / lose)")]:
        bars = ax.bar(x + offset, df[f"pct_{frame}"], width=w - 0.04, color=colour, label=label)
        ax.errorbar(x + offset, df[f"pct_{frame}"], yerr=ci_errors(df, frame),
                    fmt="none", ecolor=INK, elinewidth=0.8, capsize=2)
        for b, v in zip(bars, df[f"pct_{frame}"]):
            ax.text(b.get_x() + b.get_width() / 2, 2, f"{v:.0f}", ha="center",
                    va="bottom", fontsize=8, color="white")

    ax.axvline((x[-2] + x[-1]) / 2, color=GRID, linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    percent_axis(ax)
    ax.set_ylabel("Chose the risky option")
    pooled = df[df["scenario"] == "all"].iloc[0]
    ax.set_title("Students gambled more when the same outcome was framed as a loss")
    ax.legend(frameon=False, loc="upper left", ncol=2, fontsize=8)
    fig.text(0.01, 0.01,
             f"15 students per frame, each saw one frame only. Bars: % choosing the risky option. "
             f"Lines: 95% confidence intervals.\nAll 5 pooled: {pooled['pct_gain']:.0f}% vs "
             f"{pooled['pct_loss']:.0f}%, Mann-Whitney p = {pooled['mann_whitney_p']:.2f} "
             "(same direction in every scenario, but not statistically significant at this sample size).",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(out / "students.png")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--students-only", action="store_true",
                        help="only the students chart (no model results needed)")
    args = parser.parse_args()
    dirs = model_dirs(mock=args.mock)
    dirs["figures"].mkdir(parents=True, exist_ok=True)

    students = pd.read_csv(model_dirs()["tables"] / "students_by_scenario.csv")
    students_chart(students, model_dirs()["figures"])
    if args.students_only:
        print(f"Students chart saved in {model_dirs()['figures']}")
        return
    pooled = pd.read_csv(dirs["tables"] / "models_pooled.csv")
    per_scenario = pd.read_csv(dirs["tables"] / "models_by_scenario.csv")
    gaps = pd.read_csv(dirs["tables"] / "models_gap_direct_vs_step.csv")

    headline(students, pooled, dirs["figures"])
    by_scenario(students, per_scenario, dirs["figures"])
    step_by_step(students, gaps, dirs["figures"])
    print(f"Charts saved in {dirs['figures']}")


if __name__ == "__main__":
    main()
